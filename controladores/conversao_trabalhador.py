"""Objeto trabalhador Qt que executa a conversão fora da thread da interface."""

import logging
from pathlib import Path
import threading
import time
from typing import Callable

from PyQt6.QtCore import QObject, pyqtSignal

from config.interface import INTERVALO_MINIMO_ATUALIZACAO_UI_S
from servicos.conversao_servico import ErroConversao

REGISTRADOR = logging.getLogger(__name__)
FuncaoConversao = Callable[
    [Path, Callable[[float], None], threading.Event | None], Path
]


# --- Trabalhador em Segundo Plano ---


class ConversaoTrabalhador(QObject):
    """Executa o serviço de conversão em uma QThread e emite sinais Qt seguros."""

    progresso = pyqtSignal(float)
    concluida = pyqtSignal(str)
    falhou = pyqtSignal(str)
    finalizado = pyqtSignal()

    def __init__(self, converter: FuncaoConversao, origem: Path) -> None:
        """Inicializa o trabalhador com a função de serviço injetada e o arquivo alvo.

        Args:
            converter: Função de conversão pura em relação ao Qt.
            origem: Caminho do arquivo .ts de entrada.
        """
        super().__init__()
        self._converter = converter
        self._origem = origem
        self._evento_cancelamento = threading.Event()
        self._ultimo_envio = 0.0

    def solicitar_cancelamento(self) -> None:
        """Sinaliza ao serviço em execução que o processo deve ser interrompido."""
        self._evento_cancelamento.set()

    def executar(self) -> None:
        """Dispara a conversão e garante emissão de resultado e `finalizado`."""
        try:
            destino = self._converter(
                self._origem,
                self._emitir_progresso_limitado,
                self._evento_cancelamento,
            )
        except ErroConversao as erro:
            REGISTRADOR.error("Falha controlada na conversão: %s", erro)
            self.falhou.emit(str(erro))
        except Exception as erro:  # noqa: BLE001
            # Nenhuma exceção pode morrer silenciosamente dentro da QThread.
            REGISTRADOR.exception("Erro inesperado durante a conversão.")
            self.falhou.emit(f"Erro inesperado: {erro}")
        else:
            self.concluida.emit(str(destino))
        finally:
            self.finalizado.emit()

    def _emitir_progresso_limitado(self, percentual: float) -> None:
        """Limita a emissão de sinais de progresso a cerca de 10 vezes por segundo."""
        agora = time.monotonic()
        if agora - self._ultimo_envio >= INTERVALO_MINIMO_ATUALIZACAO_UI_S:
            self._ultimo_envio = agora
            self.progresso.emit(percentual)
