"""Ponto de entrada da aplicação: configura log, tema claro e monta o MVC."""

import logging
import os
from pathlib import Path
import sys

from PyQt6.QtWidgets import QApplication

from config.interface import CAMINHO_ARQUIVO_LOG, FORMATO_REGISTRO_LOG
from controladores.conversao_controlador import ConversaoControlador
from controladores.verificador_nvenc_trabalhador import VerificadorNvencControlador
from servicos.arquivo_servico import (
    ler_informacoes_arquivo,
    validar_arquivo_ts_local,
)
from servicos.conversao_servico import converter_arquivo
from servicos.identidade_servico import obter_titulo_aplicacao
from visoes.janela_principal import JanelaPrincipal
from visoes.tema_visao import aplicar_tema_claro


# --- Ponto de Entrada Público ---


def principal() -> int:
    """Inicializa a aplicação gráfica PyQt6 e retorna o código de encerramento.

    Returns:
        Código de saída retornado pelo laço de eventos do Qt.
    """
    if "--smoke-test" in sys.argv:
        return _testar_inicializacao()
    _configurar_logging()
    aplicacao = QApplication(sys.argv)
    aplicar_tema_claro(aplicacao)
    janela = JanelaPrincipal(validar_arquivo=validar_arquivo_ts_local)
    controlador_conversao = ConversaoControlador(
        janela=janela,
        converter=converter_arquivo,
        ler_informacoes=ler_informacoes_arquivo,
    )
    janela.setWindowTitle(obter_titulo_aplicacao())
    controlador_nvenc = VerificadorNvencControlador(janela=janela)
    controlador_conversao.iniciar()
    _configurar_encerramento(aplicacao, janela, controlador_nvenc)
    janela.show()
    controlador_nvenc.iniciar_verificacao_em_segundo_plano()
    codigo = aplicacao.exec()
    controlador_nvenc.encerrar_verificacao()
    return codigo


# --- Funções Auxiliares Privadas ---


def _configurar_encerramento(aplicacao, janela, controlador) -> None:
    """Mantém Qt ativo até concluir a descoberta, inclusive ao fechar cedo."""
    from PyQt6.QtCore import QTimer
    aplicacao.setQuitOnLastWindowClosed(False)
    aplicacao.lastWindowClosed.connect(lambda: setattr(controlador, "_encerrando", True))
    vigia = QTimer(aplicacao)
    def encerrar_quando_livre():
        """Espera a thread inicial sem bloquear a interface."""
        if not janela.isVisible() and controlador._thread is None:
            aplicacao.quit()
    vigia.timeout.connect(encerrar_quando_livre)
    vigia.start(100)


def _testar_inicializacao() -> int:
    """Exercita Qt e a janela sem descoberta, Registro ou conversão."""
    aplicacao = QApplication([])
    aplicar_tema_claro(aplicacao)
    janela = JanelaPrincipal(validar_arquivo=lambda caminho: False)
    janela.show()
    aplicacao.processEvents()
    janela.close()
    return 0


def _obter_caminho_log() -> Path:
    """Mantém o log da distribuição na área de dados gravável do usuário."""
    if not getattr(sys, "frozen", False):
        return CAMINHO_ARQUIVO_LOG
    base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    diretorio = base / "Projeto Broadcast"
    diretorio.mkdir(parents=True, exist_ok=True)
    return diretorio / CAMINHO_ARQUIVO_LOG.name


def _configurar_logging() -> None:
    """Configura o registro central de logs em arquivo para execução sem console."""
    try:
        logging.basicConfig(
            filename=str(_obter_caminho_log()), level=logging.INFO,
            format=FORMATO_REGISTRO_LOG, encoding="utf-8",
        )
    except OSError:
        logging.basicConfig(handlers=[logging.NullHandler()])



if __name__ == "__main__":
    raise SystemExit(principal())
