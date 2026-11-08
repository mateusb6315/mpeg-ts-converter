"""Testes internos de integração entre camadas, serviços com dublês e GUI headless."""

import os
from pathlib import Path
import threading

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication

from config.interface import TEXTO_ZONA_ARRASTE_LIVRE
from controladores.conversao_controlador import ConversaoControlador
from controladores.conversao_trabalhador import ConversaoTrabalhador
from controladores.verificador_nvenc_trabalhador import (
    VerificadorNvencControlador,
    VerificadorNvencTrabalhador,
)
from modelos.conversao import InformacoesArquivo
from servicos.arquivo_servico import (
    resolver_candidato_executavel,
    validar_arquivo_ts_local,
)
from servicos.conversao_servico import ErroConversao
from servicos.nvenc_config_servico import (
    salvar_executavel_nvenc_manual,
    validar_executavel_nvenc_selecionado,
)
from visoes.janela_principal import JanelaPrincipal
from visoes.tema_visao import aplicar_tema_claro

_APLICACAO_QT: QApplication | None = None


def _obter_aplicacao_qt() -> QApplication:
    """Retorna ou cria a instância global de QApplication mantendo referência viva."""
    global _APLICACAO_QT  # noqa: PLW0603
    instancia = QApplication.instance()
    if isinstance(instancia, QApplication):
        _APLICACAO_QT = instancia
        return instancia
    _APLICACAO_QT = QApplication([])
    aplicar_tema_claro(_APLICACAO_QT)
    return _APLICACAO_QT


def test_validar_arquivo_ts_local_verifica_existencia_no_disco(tmp_path: Path) -> None:
    """Garante que apenas arquivos .ts reais existentes no disco sejam aceitos."""
    arquivo_ts = tmp_path / "amostra.ts"
    arquivo_ts.write_bytes(b"\x47" * 188)
    pasta_ts = tmp_path / "pasta.ts"
    pasta_ts.mkdir()
    inexistente = tmp_path / "nao_existe.ts"

    assert validar_arquivo_ts_local(arquivo_ts) is True
    assert validar_arquivo_ts_local(pasta_ts) is False
    assert validar_arquivo_ts_local(inexistente) is False


def test_resolver_candidato_executavel_encontra_binario_na_pasta(
    tmp_path: Path,
) -> None:
    """Testa a resolução de caminho do NVEncC apontando para pasta ou arquivo."""
    falso_nvenc = tmp_path / "NVEncC64.exe"
    falso_nvenc.write_bytes(b"MZ")
    assert resolver_candidato_executavel(str(tmp_path)) == falso_nvenc.resolve()
    assert resolver_candidato_executavel(str(falso_nvenc)) == falso_nvenc.resolve()
    assert resolver_candidato_executavel("") is None


def test_validar_executavel_nvenc_selecionado_aceita_ambos_os_nomes(
    tmp_path: Path,
) -> None:
    """Confere se nvenc64.exe e NVEncC64.exe são aceitos e outros rejeitados."""
    nvenc_padrao = tmp_path / "nvenc64.exe"
    nvenc_padrao.write_bytes(b"MZ")
    nvenc_oficial = tmp_path / "NVEncC64.exe"
    nvenc_oficial.write_bytes(b"MZ")
    outro_exe = tmp_path / "ffmpeg.exe"
    outro_exe.write_bytes(b"MZ")

    assert validar_executavel_nvenc_selecionado(nvenc_padrao) is True
    assert validar_executavel_nvenc_selecionado(nvenc_oficial) is True
    assert validar_executavel_nvenc_selecionado(outro_exe) is False
    assert validar_executavel_nvenc_selecionado(tmp_path / "inexistente.exe") is False


def test_salvar_executavel_nvenc_manual_atualiza_ambiente(
    tmp_path: Path, monkeypatch
) -> None:
    """Verifica que a seleção manual grava em os.environ e chama a persistência."""
    executavel = tmp_path / "NVEncC64.exe"
    executavel.write_bytes(b"MZ")
    chamadas_persistencia: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "servicos.nvenc_config_servico._persistir_variavel_usuario_windows",
        lambda nome, valor: chamadas_persistencia.append((nome, valor)),
    )

    monkeypatch.setenv("nvenc64", "")
    sucesso = salvar_executavel_nvenc_manual(executavel)
    assert sucesso is True
    assert os.environ.get("nvenc64") == str(executavel.resolve())
    assert chamadas_persistencia == [("nvenc64", str(executavel.resolve()))]


def test_verificador_nvenc_trabalhador_emite_identificado_e_nao_identificado(
    tmp_path: Path,
) -> None:
    """Testa sinais do trabalhador de verificação do nvenc64 em segundo plano."""
    _obter_aplicacao_qt()
    identificados: list[str] = []
    nao_identificados: list[bool] = []

    trab_ok = VerificadorNvencTrabalhador(lambda: tmp_path / "NVEncC64.exe")
    trab_ok.identificado.connect(identificados.append)
    trab_ok.executar()
    assert len(identificados) == 1

    trab_falha = VerificadorNvencTrabalhador(lambda: None)
    trab_falha.nao_identificado.connect(lambda: nao_identificados.append(True))
    trab_falha.executar()
    assert nao_identificados == [True]


def test_controlador_nvenc_fluxo_nao_identificado_opcoes_sim_e_nao(
    tmp_path: Path,
) -> None:
    """Garante que o botão só aparece quando nvenc64 falta e some ao selecionar."""
    _obter_aplicacao_qt()
    janela = JanelaPrincipal(validar_arquivo=lambda p: p.suffix.lower() == ".ts")
    executavel = tmp_path / "nvenc64.exe"
    executavel.write_bytes(b"MZ")

    popups_download: list[bool] = []
    janela.exibir_popup_download_nvenc = lambda: popups_download.append(True)  # type: ignore[method-assign]

    # Caso 1: Usuário escolhe 'Não' -> exibe popup download e mostra botão
    janela.perguntar_selecao_manual_nvenc = lambda: False  # type: ignore[method-assign]
    ctrl = VerificadorNvencControlador(
        janela, verificar_nvenc=lambda: None, salvar_nvenc=lambda p: p.is_file()
    )
    assert janela.esta_botao_nvenc_visivel() is False
    ctrl._ao_nao_identificar_nvenc()
    assert janela.esta_botao_nvenc_visivel() is True
    assert len(popups_download) == 1

    # Caso 2: Usuário clica no botão 'Selecionar nvenc64' e escolhe arquivo válido -> botão some
    janela.selecionar_executavel_nvenc_dialogo = (  # type: ignore[method-assign]
        lambda _dir, _filtro: str(executavel)
    )
    assert ctrl.selecionar_nvenc_manual() is True
    assert janela.esta_botao_nvenc_visivel() is False
    janela.close()


def test_controlador_nvenc_sim_seguido_de_cancelamento_no_explorer() -> None:
    """Trata a lacuna onde o usuário clica 'Sim' mas cancela a janela do Explorer."""
    _obter_aplicacao_qt()
    janela = JanelaPrincipal(validar_arquivo=lambda p: p.suffix.lower() == ".ts")
    popups_download: list[bool] = []
    janela.perguntar_selecao_manual_nvenc = lambda: True  # type: ignore[method-assign]
    janela.selecionar_executavel_nvenc_dialogo = lambda _d, _f: ""  # type: ignore[method-assign]
    janela.exibir_popup_download_nvenc = lambda: popups_download.append(True)  # type: ignore[method-assign]

    ctrl = VerificadorNvencControlador(
        janela, verificar_nvenc=lambda: None, salvar_nvenc=lambda _p: False
    )
    ctrl._ao_nao_identificar_nvenc()
    assert janela.esta_botao_nvenc_visivel() is True
    assert len(popups_download) == 1
    janela.close()


def test_clique_na_zona_arraste_abre_dialogo_ts_e_texto_atualizado(
    tmp_path: Path,
) -> None:
    """Verifica o novo texto da zona de arraste e a seleção de .ts por clique."""
    _obter_aplicacao_qt()
    janela = JanelaPrincipal(validar_arquivo=lambda p: p.suffix.lower() == ".ts")
    assert janela._zona_arraste._rotulo.text() == TEXTO_ZONA_ARRASTE_LIVRE

    arquivo_ts = tmp_path / "video_teste.ts"
    arquivo_ts.write_bytes(b"\x47" * 188)
    janela.selecionar_arquivo_ts_dialogo = (  # type: ignore[method-assign]
        lambda _dir, _filtro: str(arquivo_ts)
    )

    recebidos: list[str] = []
    controlador = ConversaoControlador(
        janela,
        converter=lambda p, _cb, _ev=None: p.with_suffix(".mkv"),
        ler_informacoes=lambda p: InformacoesArquivo(p, 188, 10.0, 599),
    )
    controlador.iniciar()
    controlador._ao_receber_arquivo = recebidos.append  # type: ignore[method-assign]

    evento_clique = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(10.0, 10.0),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    janela._zona_arraste.mousePressEvent(evento_clique)
    assert recebidos == [str(arquivo_ts)]
    janela.close()


def test_trabalhador_emite_sinais_de_progresso_e_conclusao(tmp_path: Path) -> None:
    """Verifica que o ConversaoTrabalhador traduz o callback em sinais Qt."""
    _obter_aplicacao_qt()
    origem = tmp_path / "entrada.ts"
    progresso_recebido: list[float] = []
    concluidos: list[str] = []
    finalizados: list[bool] = []

    def converter_falso(
        caminho: Path,
        ao_progredir,
        _cancelamento: threading.Event | None = None,
    ) -> Path:
        ao_progredir(50.0)
        return caminho.with_suffix(".mkv")

    trabalhador = ConversaoTrabalhador(converter_falso, origem)
    trabalhador.progresso.connect(progresso_recebido.append)
    trabalhador.concluida.connect(concluidos.append)
    trabalhador.finalizado.connect(lambda: finalizados.append(True))
    trabalhador.executar()

    assert progresso_recebido == [50.0]
    assert concluidos == [str(origem.with_suffix(".mkv"))]
    assert finalizados == [True]


def test_trabalhador_captura_erro_conversao_e_emite_falhou(tmp_path: Path) -> None:
    """Confirma que ErroConversao vira sinal `falhou` sem derrubar a thread."""
    _obter_aplicacao_qt()
    erros: list[str] = []

    def converter_com_erro(
        _caminho: Path,
        _ao_progredir,
        _cancelamento: threading.Event | None = None,
    ) -> Path:
        raise ErroConversao("Falha simulada do NVEncC")

    trabalhador = ConversaoTrabalhador(converter_com_erro, tmp_path / "a.ts")
    trabalhador.falhou.connect(erros.append)
    trabalhador.executar()
    assert erros == ["Falha simulada do NVEncC"]
