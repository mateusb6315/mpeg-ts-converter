"""Trabalhador e controlador de verificação em segundo plano do executável nvenc64."""

import logging
from pathlib import Path
from typing import Callable

from PyQt6.QtCore import QObject, QThread, Qt, pyqtSignal

from config.configuracoes import FILTRO_DIALOGO_NVENC
from config.interface import STATUS_AGUARDANDO, STATUS_NVENC_PENDENTE
from servicos.nvenc_config_servico import (
    obter_diretorio_program_files,
    salvar_executavel_nvenc_manual,
    verificar_ambiente_nvenc,
)
from visoes.janela_principal import JanelaPrincipal

REGISTRADOR = logging.getLogger(__name__)
FuncaoVerificarNvenc = Callable[[], Path | None]
FuncaoSalvarNvenc = Callable[[Path], bool]


# --- Trabalhador em Segundo Plano (QThread) ---


class VerificadorNvencTrabalhador(QObject):
    """Executa a busca pelo executável nvenc64 e variáveis de ambiente em QThread."""

    identificado = pyqtSignal(str)
    nao_identificado = pyqtSignal()
    finalizado = pyqtSignal()

    def __init__(self, verificar_nvenc: FuncaoVerificarNvenc) -> None:
        """Inicializa o trabalhador com a função de verificação injetada."""
        super().__init__()
        self._verificar_nvenc = verificar_nvenc

    def executar(self) -> None:
        """Realiza a verificação em segundo plano e emite o sinal correspondente."""
        try:
            caminho = self._verificar_nvenc()
        except Exception:  # noqa: BLE001
            REGISTRADOR.exception("Erro ao verificar nvenc64 em segundo plano.")
            caminho = None
        if caminho is not None:
            self.identificado.emit(str(caminho))
        else:
            self.nao_identificado.emit()
        self.finalizado.emit()


# --- Controlador de Configuração do nvenc64 ---


class VerificadorNvencControlador(QObject):
    """Coordena a verificação inicial em segundo plano e a seleção manual do nvenc64."""

    def __init__(
        self,
        janela: JanelaPrincipal,
        verificar_nvenc: FuncaoVerificarNvenc = verificar_ambiente_nvenc,
        salvar_nvenc: FuncaoSalvarNvenc = salvar_executavel_nvenc_manual,
    ) -> None:
        """Configura o controlador de verificação do nvenc64 com injeção de dependências."""
        super().__init__()
        self._janela = janela
        self._verificar_nvenc = verificar_nvenc
        self._salvar_nvenc = salvar_nvenc
        self._thread: QThread | None = None
        self._trabalhador: VerificadorNvencTrabalhador | None = None
        self._janela.selecao_nvenc_solicitada.connect(self.selecionar_nvenc_manual)

    def iniciar_verificacao_em_segundo_plano(self) -> None:
        """Dispara a QThread que verifica o nvenc64 ao iniciar o software."""
        self._janela.definir_verificacao_ambiente(True)
        thread = QThread(self)
        trabalhador = VerificadorNvencTrabalhador(self._verificar_nvenc)
        trabalhador.moveToThread(thread)
        fila = Qt.ConnectionType.QueuedConnection
        thread.started.connect(trabalhador.executar)
        trabalhador.identificado.connect(self._ao_identificar_nvenc, fila)
        trabalhador.nao_identificado.connect(self._ao_nao_identificar_nvenc, fila)
        trabalhador.finalizado.connect(self._limpar_thread_verificacao, fila)
        self._thread = thread
        self._trabalhador = trabalhador
        thread.start()

    def selecionar_nvenc_manual(self) -> bool:
        """Abre o seletor em Program Files e oculta o botão se válido."""
        diretorio_inicial = str(obter_diretorio_program_files())
        escolhido = self._janela.selecionar_executavel_nvenc_dialogo(
            diretorio_inicial, FILTRO_DIALOGO_NVENC
        )
        if not escolhido:
            return False
        if not self._salvar_nvenc(Path(escolhido)):
            self._janela.exibir_status(STATUS_NVENC_PENDENTE)
            return False
        self._janela.definir_visibilidade_botao_nvenc(False)
        self._janela.exibir_status(STATUS_AGUARDANDO)
        return True

    def encerrar_verificacao(self) -> None:
        """Aguarda a conclusão da thread de verificação caso ainda esteja ativa."""
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)

    def _ao_identificar_nvenc(self, _caminho: str) -> None:
        """Segue com o fluxo normal sem exibir popups quando o nvenc64 é encontrado."""
        self._janela.definir_verificacao_ambiente(False)
        self._janela.exibir_status(STATUS_AGUARDANDO)

    def _ao_nao_identificar_nvenc(self) -> None:
        """Exibe os popups de seleção manual ou download e habilita o botão na GUI."""
        self._janela.definir_verificacao_ambiente(False)
        if getattr(self, "_encerrando", False):
            return
        deseja_selecionar = self._janela.perguntar_selecao_manual_nvenc()
        if deseja_selecionar and self.selecionar_nvenc_manual():
            return
        self._janela.definir_visibilidade_botao_nvenc(True)
        self._janela.exibir_status(STATUS_NVENC_PENDENTE)
        self._janela.exibir_popup_download_nvenc()

    def _limpar_thread_verificacao(self) -> None:
        """Encerra e libera a QThread e o trabalhador de verificação inicial."""
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(2000)
            self._thread.deleteLater()
            self._thread = None
        if self._trabalhador is not None:
            self._trabalhador.deleteLater()
            self._trabalhador = None
