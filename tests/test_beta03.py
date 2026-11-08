"""Regressões da beta: versões, integridade, áudio e transação de saída."""
from pathlib import Path
import threading
from unittest.mock import patch
import pytest
from scripts.distribuicao.versoes import validar_nome, validar_producao
from servicos import conversao_servico as motor
from servicos.pipeline_conversao import executar_conversao
from modelos.conversao import validar_fluxos_audio


@pytest.mark.parametrize("nome", ["0.0.3-beta1", "ensaio livre", "teste", "0.3"])
def test_beta_aceita_formato_livre(nome):
    assert validar_nome(nome) == nome


@pytest.mark.parametrize("nome", ["", "../fora", "CON", "NUL.txt", "x.", " x", "a/b"])
def test_nome_recusa_caminhos_e_reservados(nome):
    with pytest.raises(ValueError):
        validar_nome(nome)


def test_producao_exige_tres_numeros():
    assert validar_producao("0.0.3") == "0.0.3"
    with pytest.raises(ValueError):
        validar_producao("0.0.3-beta1")


def test_cancelamento_previo_nao_inicia_processo(tmp_path):
    evento = threading.Event()
    evento.set()
    with patch.object(motor, "_obter_executavel_validado") as obter:
        with pytest.raises(motor.ErroConversao):
            executar_conversao(tmp_path / "ausente.ts", lambda p: None, evento)
        obter.assert_not_called()


def test_transacao_preserva_destino_e_valida_video(tmp_path, monkeypatch):
    entrada = tmp_path / "a.ts"
    entrada.write_bytes(b"ts")
    fluxos = [{"codec_type": "video", "start_time": "1"},
              {"codec_type": "audio", "start_time": "1", "channels": 2}]
    monkeypatch.setattr(motor, "_obter_executavel_validado", lambda: Path("nvenc.exe"))
    monkeypatch.setattr(motor, "_verificar_versao_nvenc", lambda p: None)
    monkeypatch.setattr(motor, "sondar_duracao_arquivo", lambda p: None)
    monkeypatch.setattr("servicos.pipeline_conversao.sondar_fluxos_midia", lambda p: fluxos)
    recebidos = []
    monkeypatch.setattr(motor, "_registrar_validacao_audio", lambda p, f: recebidos.extend(f))
    def executar(exe, args, contexto):
        Path(args[-1]).write_bytes(b"mkv")
        return 0
    monkeypatch.setattr(motor, "_executar_processo_nvenc", executar)
    saida = executar_conversao(entrada, lambda p: None)
    assert recebidos == fluxos
    assert saida.read_bytes() == b"mkv"
    with pytest.raises(motor.ErroConversao, match="existe"):
        executar_conversao(entrada, lambda p: None)
    assert saida.read_bytes() == b"mkv"


def test_faixa_invalida_nao_oculta_divergencia_seguinte():
    origem = [{"codec_type": "video", "start_time": "0"},
              {"codec_type": "audio", "start_time": "N/A"},
              {"codec_type": "audio", "start_time": "0"}]
    saida = [{"codec_type": "video", "start_time": "0"},
             {"codec_type": "audio", "start_time": "0"},
             {"codec_type": "audio", "start_time": "1"}]
    assert len(validar_fluxos_audio(origem, saida)) == 2


def test_cli_solicita_versao_manual(monkeypatch, tmp_path):
    from scripts.distribuicao import cli
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr("sys.argv", ["compilar_beta.py"])
    monkeypatch.setattr("builtins.input", lambda texto: "ensaio livre")
    recebidos = []
    monkeypatch.setattr(cli, "compilar", lambda p, **k: recebidos.append(k["versao"]))
    assert cli.principal("beta") == 0
    assert recebidos == ["ensaio livre"]


def test_processo_real_consumo_e_cancelamento():
    import sys
    evento = threading.Event()
    contexto = motor._ContextoExecucao("teste", None, lambda p: None, evento)
    timer = threading.Timer(0.3, evento.set)
    timer.start()
    try:
        with pytest.raises(motor.ErroConversao, match="cancelada"):
            motor._executar_processo_nvenc(
                Path(sys.executable), ["-c", "import time; time.sleep(10)"], contexto)
    finally:
        timer.cancel()


def test_release_detecta_adulteracao(tmp_path):
    import json
    from scripts.release import verificar
    from scripts.distribuicao.manifesto import hash_arquivo
    arquivos = {}
    pasta = tmp_path / "mpeg-ts-converter 0.0.3-beta"
    pasta.mkdir()
    for nome in ("mpeg-ts-converter.exe", "LICENSE", "README.md"):
        caminho = pasta / nome
        caminho.write_bytes(b"original")
        arquivos[nome] = {"sha256": hash_arquivo(caminho), "bytes": 8}
    (pasta / "build.json").write_text(json.dumps(
        {"esquema": 1, "versao": "0.0.3-beta", "arquivos": arquivos}))
    verificar(pasta)
    (pasta / "mpeg-ts-converter.exe").write_bytes(b"alterado")
    with pytest.raises(ValueError, match="Integridade"):
        verificar(pasta)


def test_metadados_lentos_e_ciclo_qthread_nao_bloqueiam_gui(tmp_path):
    import time
    from tests.test_integracao_interna import _obter_aplicacao_qt
    from PyQt6.QtCore import QEventLoop, QTimer
    from visoes.janela_principal import JanelaPrincipal
    from controladores.conversao_controlador import ConversaoControlador
    from modelos.conversao import InformacoesArquivo
    app = _obter_aplicacao_qt()
    janela = JanelaPrincipal(lambda p: True)
    janela.exibir_popup_conclusao = lambda: None
    janela.exibir_popup_erro = lambda mensagem: pytest.fail(mensagem)
    entrada = tmp_path / "video.ts"
    entrada.write_bytes(b"ts")
    batidas = []
    def ler(caminho):
        time.sleep(0.15)
        return InformacoesArquivo(caminho, 2)
    ctrl = ConversaoControlador(janela, lambda p, cb, ev: p.with_suffix(".mkv"), ler)
    ctrl.iniciar()
    loop = QEventLoop()
    QTimer.singleShot(50, lambda: batidas.append(True))
    inicio = time.monotonic()
    ctrl._ao_receber_arquivo(str(entrada))
    assert time.monotonic() - inicio < 0.1
    ctrl._thread.finished.connect(loop.quit)
    QTimer.singleShot(2000, loop.quit)
    loop.exec()
    app.processEvents()
    assert batidas
    assert ctrl._thread is None
    janela.close()


def test_build_isola_path_e_variaveis_qt(monkeypatch):
    from scripts.distribuicao.ambiente import ambiente_compilacao
    monkeypatch.setenv("PATH", r"C:\aplicativo-externo")
    monkeypatch.setenv("QT_PLUGIN_PATH", r"C:\plugins-externos")
    ambiente = ambiente_compilacao()
    assert "aplicativo-externo" not in ambiente["PATH"]
    assert "QT_PLUGIN_PATH" not in ambiente
