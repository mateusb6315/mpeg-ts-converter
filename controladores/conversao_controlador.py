"""Controlador principal que coordena a View, o Model e o serviço em QThread."""

import logging
from pathlib import Path
import time
from typing import Callable

from PyQt6.QtCore import QObject, QThread, QTimer, Qt

from config.configuracoes import FILTRO_DIALOGO_TS
from config.interface import (
    INTERVALO_TIMER_SEGUNDOS_MS,
    STATUS_ARQUIVO_INVALIDO,
    STATUS_NVENC_PENDENTE,
    TEXTO_CALCULANDO,
)
from controladores.conversao_trabalhador import ConversaoTrabalhador, FuncaoConversao
from modelos.conversao import (
    EstadoConversao,
    InformacoesArquivo,
    calcular_tempo_restante,
    eh_arquivo_ts,
)
from utilitarios.formatacao import (
    formatar_duracao,
    formatar_percentual,
    formatar_tamanho,
    truncar_texto_meio,
)
from visoes.janela_principal import JanelaPrincipal

REGISTRADOR = logging.getLogger(__name__)
FuncaoLeituraArquivo = Callable[[Path], InformacoesArquivo]


# --- Controlador do Fluxo de Conversão ---


class ConversaoControlador(QObject):
    """Coordena eventos da janela, validação, thread de conversão e estados."""

    def __init__(
        self,
        janela: JanelaPrincipal,
        converter: FuncaoConversao,
        ler_informacoes: FuncaoLeituraArquivo,
    ) -> None:
        """Configura o controlador com as dependências injetadas."""
        super().__init__()
        self._janela = janela
        self._converter = converter
        self._ler_informacoes = ler_informacoes
        self._estado = EstadoConversao.AGUARDANDO
        self._thread: QThread | None = None
        self._trabalhador: ConversaoTrabalhador | None = None
        self._instante_inicio = 0.0
        self._percentual_atual = 0.0
        self._cancelado_pelo_usuario = False
        self._ultimo_diretorio_ts = str(Path.home())
        self._timer_decorrido = QTimer(self)
        self._timer_decorrido.setInterval(INTERVALO_TIMER_SEGUNDOS_MS)
        self._timer_decorrido.timeout.connect(self._ao_atualizar_relogio)

    # --- Ciclo de Vida e Ações Públicas ---

    def iniciar(self) -> None:
        """Conecta os sinais da View e posiciona a janela no estado inicial."""
        self._janela.arquivo_solto.connect(self._ao_receber_arquivo)
        self._janela.selecao_ts_solicitada.connect(self._ao_solicitar_selecao_ts)
        self._janela.definir_acao_cancelamento(self.cancelar_conversao_ativa)
        self._restaurar_estado_inicial()

    def cancelar_conversao_ativa(self) -> None:
        """Interrompe a conversão em andamento e aguarda o encerramento da thread."""
        self._cancelado_pelo_usuario = True
        self._timer_decorrido.stop()
        if self._trabalhador is not None:
            self._trabalhador.solicitar_cancelamento()
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(5000)

    # --- Tratadores de Sinais da View e do Trabalhador ---

    def _ao_solicitar_selecao_ts(self) -> None:
        """Abre o seletor do Windows Explorer ao clicar na zona de arraste."""
        if self._estado == EstadoConversao.CONVERTENDO:
            return
        if self._janela.esta_botao_nvenc_visivel():
            self._janela.exibir_status(STATUS_NVENC_PENDENTE)
            return
        escolhido = self._janela.selecionar_arquivo_ts_dialogo(
            self._ultimo_diretorio_ts, FILTRO_DIALOGO_TS
        )
        if not escolhido:
            return
        self._ultimo_diretorio_ts = str(Path(escolhido).parent)
        self._ao_receber_arquivo(escolhido)

    def _ao_receber_arquivo(self, caminho_texto: str) -> None:
        """Valida o arquivo selecionado ou solto e inicia a conversão se livre."""
        if self._estado == EstadoConversao.CONVERTENDO:
            return
        if self._janela.esta_botao_nvenc_visivel():
            self._janela.exibir_status(STATUS_NVENC_PENDENTE)
            return
        caminho = Path(caminho_texto)
        if not eh_arquivo_ts(caminho) or not caminho.is_file():
            self._janela.exibir_status(STATUS_ARQUIVO_INVALIDO)
            return
        self._ultimo_diretorio_ts = str(caminho.parent)
        REGISTRADOR.info("Iniciando conversão do arquivo: %s", caminho)
        self._preparar_interface_para_conversao(caminho)
        self._iniciar_execucao_em_thread(caminho)

    def _ao_progredir(self, percentual: float) -> None:
        """Recebe o percentual da thread e atualiza a barra e a estimativa de tempo."""
        if self._estado != EstadoConversao.CONVERTENDO:
            return
        if percentual > self._percentual_atual:
            self._percentual_atual = percentual
        inteiro = int(round(self._percentual_atual))
        texto = formatar_percentual(self._percentual_atual)
        self._janela.atualizar_progresso(inteiro, texto)
        self._atualizar_tempos_na_janela()

    def _ao_atualizar_relogio(self) -> None:
        """Atualiza a cada segundo o tempo decorrido e o restante estimado."""
        if self._estado == EstadoConversao.CONVERTENDO:
            self._atualizar_tempos_na_janela()

    def _ao_concluir(self, caminho_destino: str) -> None:
        """Finaliza o progresso em 100%, exibe o popup de sucesso e reinicia a janela."""
        self._timer_decorrido.stop()
        self._estado = EstadoConversao.CONCLUIDA
        REGISTRADOR.info("Conversão concluída com sucesso: %s", caminho_destino)
        self._janela.exibir_popup_conclusao()
        self._restaurar_estado_inicial()

    def _ao_falhar(self, mensagem_erro: str) -> None:
        """Exibe o popup de erro crítico (se não cancelado na saída) e reinicia a janela."""
        self._timer_decorrido.stop()
        self._estado = EstadoConversao.FALHOU
        if not self._cancelado_pelo_usuario:
            self._janela.exibir_popup_erro(mensagem_erro)
            self._restaurar_estado_inicial()

    def _ao_finalizar_trabalhador(self) -> None:
        """Encerra a QThread e agenda a liberação de memória dos objetos Qt."""
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(2000)
            self._thread.deleteLater()
            self._thread = None
        if self._trabalhador is not None:
            self._trabalhador.deleteLater()
            self._trabalhador = None

    # --- Métodos Auxiliares Privados ---

    def _preparar_interface_para_conversao(self, caminho: Path) -> None:
        """Preenche as informações do arquivo na View e inicia o cronômetro."""
        self._estado = EstadoConversao.CONVERTENDO
        self._cancelado_pelo_usuario = False
        self._percentual_atual = 0.0
        self._instante_inicio = time.monotonic()
        nome_curto = truncar_texto_meio(caminho.name)
        self._janela.exibir_inicio_conversao(nome_curto, str(caminho))
        informacoes = self._ler_informacoes(caminho)
        tamanho_txt = formatar_tamanho(informacoes.tamanho_bytes)
        duracao_txt = formatar_duracao(informacoes.duracao_segundos)
        self._janela.exibir_metadados_midia(tamanho_txt, duracao_txt)
        self._janela.atualizar_tempos("00:00:00", TEXTO_CALCULANDO)
        self._timer_decorrido.start()

    def _iniciar_execucao_em_thread(self, caminho: Path) -> None:
        """Cria a QThread e o trabalhador, conecta sinais em fila e inicia a thread."""
        thread = QThread(self)
        trabalhador = ConversaoTrabalhador(self._converter, caminho)
        trabalhador.moveToThread(thread)
        fila = Qt.ConnectionType.QueuedConnection
        thread.started.connect(trabalhador.executar)
        trabalhador.progresso.connect(self._ao_progredir, fila)
        trabalhador.concluida.connect(self._ao_concluir, fila)
        trabalhador.falhou.connect(self._ao_falhar, fila)
        trabalhador.finalizado.connect(self._ao_finalizar_trabalhador, fila)
        self._thread = thread
        self._trabalhador = trabalhador
        thread.start()

    def _atualizar_tempos_na_janela(self) -> None:
        """Calcula o tempo decorrido e o estimado restante e atualiza a View."""
        decorrido_seg = max(0.0, time.monotonic() - self._instante_inicio)
        decorrido_txt = formatar_duracao(decorrido_seg)
        restante_seg = calcular_tempo_restante(self._percentual_atual, decorrido_seg)
        restante_txt = (
            formatar_duracao(restante_seg)
            if restante_seg is not None
            else TEXTO_CALCULANDO
        )
        self._janela.atualizar_tempos(decorrido_txt, restante_txt)

    def _restaurar_estado_inicial(self) -> None:
        """Retorna o controlador e a janela ao estado inicial aguardando arquivo."""
        self._timer_decorrido.stop()
        self._estado = EstadoConversao.AGUARDANDO
        self._percentual_atual = 0.0
        self._janela.exibir_estado_inicial()
        if self._janela.esta_botao_nvenc_visivel():
            self._janela.exibir_status(STATUS_NVENC_PENDENTE)
