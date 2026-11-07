"""Janela principal PyQt6: drag & drop, seletores de arquivo, barra e popups."""

from pathlib import Path
from typing import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QFileDialog, QHBoxLayout, QMessageBox, QProgressBar, QVBoxLayout, QWidget,
)

from config.interface import (
    ALTURA_BARRA_PROGRESSO, ALTURA_JANELA, ESPACAMENTO_LAYOUT, LARGURA_JANELA,
    MARGEM_EXTERNA_LAYOUT, MENSAGEM_CONFIRMAR_SAIDA, MENSAGEM_DOWNLOAD_NVENC,
    MENSAGEM_NVENC_NAO_IDENTIFICADO, MENSAGEM_POPUP_CONCLUSAO,
    STATUS_ARQUIVO_INVALIDO, STATUS_CONCLUIDO, STATUS_CONVERTENDO, STATUS_FALHA,
    TITULO_DIALOGO_NVENC, TITULO_DIALOGO_TS, TITULO_JANELA,
)
from visoes.componentes_visao import (
    PainelInformacoes, ZonaArraste, criar_botao_selecionar_nvenc,
    exibir_caixa_mensagem, exibir_pergunta_sim_nao,
)
from visoes.estilos_visao import gerar_estilo_barra_progresso, gerar_estilo_janela


class JanelaPrincipal(QWidget):
    """Janela horizontal fixa que aceita arquivos .ts e exibe o progresso."""

    arquivo_solto = pyqtSignal(str)
    selecao_ts_solicitada = pyqtSignal()
    selecao_nvenc_solicitada = pyqtSignal()

    def __init__(self, validar_arquivo: Callable[[Path], bool]) -> None:
        """Configura dimensões fixas, componentes visuais e suporte a drag & drop."""
        super().__init__()
        self._validar_arquivo = validar_arquivo
        self._ao_cancelar_conversao: Callable[[], None] | None = None
        self._ocupada = False
        self._configurar_janela()
        self._zona_arraste = ZonaArraste(self)
        self._botao_nvenc = criar_botao_selecionar_nvenc(self)
        self._painel_info = PainelInformacoes(self)
        self._barra_progresso = self._criar_barra_progresso()
        self._conectar_eventos_internos()
        self._montar_layout()
        self.exibir_estado_inicial()

    def definir_acao_cancelamento(self, acao: Callable[[], None]) -> None:
        """Registra a função a ser invocada caso o usuário feche durante a conversão."""
        self._ao_cancelar_conversao = acao

    def definir_visibilidade_botao_nvenc(self, visivel: bool) -> None:
        """Exibe ou oculta o botão 'Selecionar nvenc64' conforme detecção."""
        self._botao_nvenc.setVisible(visivel)

    def esta_botao_nvenc_visivel(self) -> bool:
        """Indica se o botão 'Selecionar nvenc64' está marcado como visível."""
        return not self._botao_nvenc.isHidden()

    def exibir_estado_inicial(self) -> None:
        """Restaura a janela para o estado inicial pronta para receber outro .ts."""
        self._ocupada = False
        self._zona_arraste.exibir_estado_livre()
        self._painel_info.limpar_informacoes()
        self._barra_progresso.setRange(0, 100)
        self._barra_progresso.setValue(0)
        self._barra_progresso.setFormat("0%")

    def exibir_inicio_conversao(self, nome_exibicao: str, caminho_completo: str) -> None:
        """Coloca a janela em modo ocupado e exibe a identificação do arquivo."""
        self._ocupada = True
        self._zona_arraste.exibir_arquivo_em_conversao(nome_exibicao, caminho_completo)
        self._painel_info.exibir_arquivo(nome_exibicao, caminho_completo)
        self._painel_info.atualizar_status(STATUS_CONVERTENDO)
        self._barra_progresso.setValue(0)
        self._barra_progresso.setFormat("0,0%")

    def exibir_metadados_midia(self, tamanho: str, duracao: str) -> None:
        """Exibe o tamanho e a duração formatados no painel de informações."""
        self._painel_info.exibir_midia(tamanho, duracao)

    def atualizar_progresso(self, percentual_inteiro: int, texto_percentual: str) -> None:
        """Atualiza o preenchimento e o texto centralizado da barra de progresso."""
        valor = max(0, min(100, percentual_inteiro))
        if valor >= self._barra_progresso.value():
            self._barra_progresso.setValue(valor)
            self._barra_progresso.setFormat(texto_percentual)

    def atualizar_tempos(self, decorrido: str, restante: str) -> None:
        """Atualiza os campos de tempo decorrido e tempo restante estimado."""
        self._painel_info.atualizar_tempos(decorrido, restante)

    def exibir_status(self, mensagem: str) -> None:
        """Exibe uma mensagem curta no campo de status do painel."""
        self._painel_info.atualizar_status(mensagem)

    def exibir_popup_conclusao(self) -> None:
        """Garante a barra em 100%, mostra status Concluído e abre o popup modal OK."""
        self._barra_progresso.setValue(100)
        self._barra_progresso.setFormat("100%")
        self._painel_info.atualizar_status(STATUS_CONCLUIDO)
        exibir_caixa_mensagem(self, QMessageBox.Icon.Information, MENSAGEM_POPUP_CONCLUSAO)

    def exibir_popup_erro(self, mensagem: str) -> None:
        """Atualiza o status para falha e exibe um popup crítico com botão único OK."""
        self._painel_info.atualizar_status(STATUS_FALHA)
        exibir_caixa_mensagem(self, QMessageBox.Icon.Critical, mensagem)

    def perguntar_selecao_manual_nvenc(self) -> bool:
        """Pergunta ao usuário se deseja localizar manualmente o executável nvenc64."""
        return exibir_pergunta_sim_nao(self, MENSAGEM_NVENC_NAO_IDENTIFICADO)

    def exibir_popup_download_nvenc(self) -> None:
        """Exibe popup com link clicável de download e instrução sobre o botão."""
        exibir_caixa_mensagem(
            self, QMessageBox.Icon.Information, MENSAGEM_DOWNLOAD_NVENC, usar_html=True
        )

    def selecionar_executavel_nvenc_dialogo(self, diretorio_inicial: str, filtro: str) -> str:
        """Abre o Windows Explorer em Program Files para escolher o nvenc64."""
        caminho, _ = QFileDialog.getOpenFileName(
            self, TITULO_DIALOGO_NVENC, diretorio_inicial, filtro
        )
        return caminho

    def selecionar_arquivo_ts_dialogo(self, diretorio_inicial: str, filtro: str) -> str:
        """Abre o Windows Explorer para o usuário escolher um arquivo .ts."""
        caminho, _ = QFileDialog.getOpenFileName(
            self, TITULO_DIALOGO_TS, diretorio_inicial, filtro
        )
        return caminho

    def dragEnterEvent(self, evento: QDragEnterEvent | None) -> None:
        """Aceita o arraste apenas de um único .ts válido quando a janela está livre."""
        if evento is None or self._ocupada:
            if evento is not None:
                evento.ignore()
            return
        caminho = _extrair_caminho_unico(evento)
        if caminho is not None and self._validar_arquivo(caminho):
            evento.acceptProposedAction()
            return
        self._painel_info.atualizar_status(STATUS_ARQUIVO_INVALIDO)
        evento.ignore()

    def dropEvent(self, evento: QDropEvent | None) -> None:
        """Valida a soltura e emite `arquivo_solto` para iniciar a conversão."""
        if evento is None or self._ocupada:
            if evento is not None:
                evento.ignore()
            return
        caminho = _extrair_caminho_unico(evento)
        if caminho is None or not self._validar_arquivo(caminho):
            self._painel_info.atualizar_status(STATUS_ARQUIVO_INVALIDO)
            evento.ignore()
            return
        evento.acceptProposedAction()
        self.arquivo_solto.emit(str(caminho))

    def closeEvent(self, evento: QCloseEvent | None) -> None:
        """Pede confirmação antes de fechar caso haja uma conversão em andamento."""
        if evento is None:
            return
        if not self._ocupada:
            evento.accept()
            return
        if not exibir_pergunta_sim_nao(self, MENSAGEM_CONFIRMAR_SAIDA):
            evento.ignore()
            return
        if self._ao_cancelar_conversao is not None:
            self._ao_cancelar_conversao()
        evento.accept()

    def _configurar_janela(self) -> None:
        """Define título, tamanho fixo, flags sem maximizar e estilo da janela."""
        self.setObjectName("JanelaPrincipal")
        self.setWindowTitle(TITULO_JANELA)
        self.setFixedSize(LARGURA_JANELA, ALTURA_JANELA)
        self.setAcceptDrops(True)
        flags = (
            Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowFlags(flags)
        self.setStyleSheet(gerar_estilo_janela())

    def _criar_barra_progresso(self) -> QProgressBar:
        """Cria e estiliza a barra de progresso horizontal verde."""
        barra = QProgressBar(self)
        barra.setObjectName("BarraProgresso")
        barra.setFixedHeight(ALTURA_BARRA_PROGRESSO)
        barra.setRange(0, 100)
        barra.setValue(0)
        barra.setTextVisible(True)
        barra.setAlignment(Qt.AlignmentFlag.AlignCenter)
        barra.setStyleSheet(gerar_estilo_barra_progresso())
        return barra

    def _conectar_eventos_internos(self) -> None:
        """Conecta cliques na zona de arraste e no botão nvenc aos sinais da View."""
        self._zona_arraste.clicada.connect(self._ao_clicar_zona_arraste)
        self._botao_nvenc.clicked.connect(self.selecao_nvenc_solicitada.emit)

    def _ao_clicar_zona_arraste(self) -> None:
        """Emite solicitação de seleção de arquivo .ts se a janela estiver livre."""
        if not self._ocupada:
            self.selecao_ts_solicitada.emit()

    def _montar_layout(self) -> None:
        """Dispõe coluna esquerda (zona + botão), painel direito e barra inferior."""
        m = MARGEM_EXTERNA_LAYOUT
        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(m, m, m, m)
        layout_raiz.setSpacing(ESPACAMENTO_LAYOUT)
        coluna_esquerda = QVBoxLayout()
        coluna_esquerda.setSpacing(4)
        coluna_esquerda.addWidget(self._zona_arraste, stretch=1)
        coluna_esquerda.addWidget(self._botao_nvenc)
        linha_superior = QHBoxLayout()
        linha_superior.setSpacing(ESPACAMENTO_LAYOUT)
        linha_superior.addLayout(coluna_esquerda)
        linha_superior.addWidget(self._painel_info, stretch=1)
        layout_raiz.addLayout(linha_superior, stretch=1)
        layout_raiz.addWidget(self._barra_progresso)


def _extrair_caminho_unico(evento: QDragEnterEvent | QDropEvent) -> Path | None:
    """Extrai o Path se o evento de arraste contiver exatamente um arquivo local."""
    dados_mime = evento.mimeData()
    if dados_mime is None or not dados_mime.hasUrls():
        return None
    urls = dados_mime.urls()
    if len(urls) != 1 or not urls[0].isLocalFile():
        return None
    caminho_texto = urls[0].toLocalFile()
    return Path(caminho_texto) if caminho_texto else None
