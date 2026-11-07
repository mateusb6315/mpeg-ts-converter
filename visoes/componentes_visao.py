"""Componentes visuais e diálogos reutilizáveis da camada de visão PyQt6."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.interface import (
    ALTURA_BOTAO_NVENC,
    LARGURA_ZONA_ARRASTE,
    ROTULO_ARQUIVO,
    ROTULO_DECORRIDO,
    ROTULO_DURACAO,
    ROTULO_RESTANTE,
    ROTULO_STATUS,
    ROTULO_TAMANHO,
    STATUS_AGUARDANDO,
    TEXTO_BOTAO_SELECIONAR_NVENC,
    TEXTO_VALOR_VAZIO,
    TEXTO_ZONA_ARRASTE_LIVRE,
    TITULO_POPUP,
)
from visoes.estilos_visao import (
    gerar_estilo_botao_nvenc,
    gerar_estilo_painel_informacoes,
    gerar_estilo_zona_arraste,
)


# --- Componentes Visuais Públicos ---


class ZonaArraste(QFrame):
    """Retângulo tracejado clicável à esquerda que aceita seleção ou arraste."""

    clicada = pyqtSignal()

    def __init__(self, pai: QWidget | None = None) -> None:
        """Inicializa a zona de arraste no estado livre e clicável."""
        super().__init__(pai)
        self._ativa = True
        self.setObjectName("ZonaArraste")
        self.setFixedWidth(LARGURA_ZONA_ARRASTE)
        self._rotulo = QLabel(TEXTO_ZONA_ARRASTE_LIVRE, self)
        self._rotulo.setObjectName("RotuloZonaArraste")
        self._rotulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._rotulo.setWordWrap(True)
        self._montar_layout()
        self.exibir_estado_livre()

    def exibir_estado_livre(self) -> None:
        """Restaura o texto, o cursor de clique e o estilo de aguardando .ts."""
        self._ativa = True
        self._rotulo.setText(TEXTO_ZONA_ARRASTE_LIVRE)
        self.setToolTip("")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(gerar_estilo_zona_arraste(ocupada=False))

    def exibir_arquivo_em_conversao(
        self, nome_exibicao: str, caminho_completo: str
    ) -> None:
        """Exibe o nome do arquivo em processamento com tom visual desabilitado."""
        self._ativa = False
        self._rotulo.setText(nome_exibicao)
        self.setToolTip(caminho_completo)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setStyleSheet(gerar_estilo_zona_arraste(ocupada=True))

    def mousePressEvent(self, evento: QMouseEvent | None) -> None:
        """Emite `clicada` ao receber clique esquerdo quando a zona está livre."""
        if (
            evento is not None
            and self._ativa
            and evento.button() == Qt.MouseButton.LeftButton
        ):
            self.clicada.emit()
        super().mousePressEvent(evento)

    def _montar_layout(self) -> None:
        """Posiciona o rótulo centralizado dentro do quadro."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self._rotulo)


class PainelInformacoes(QFrame):
    """Painel à direita com pares rótulo/valor do arquivo e do andamento."""

    def __init__(self, pai: QWidget | None = None) -> None:
        """Inicializa os campos informativos no estado inicial."""
        super().__init__(pai)
        self.setObjectName("PainelInformacoes")
        self.setStyleSheet(gerar_estilo_painel_informacoes())
        self._valor_arquivo = _criar_rotulo_valor()
        self._valor_tamanho = _criar_rotulo_valor()
        self._valor_duracao = _criar_rotulo_valor()
        self._valor_status = _criar_rotulo_valor()
        self._valor_decorrido = _criar_rotulo_valor()
        self._valor_restante = _criar_rotulo_valor()
        self._montar_grade()
        self.limpar_informacoes()

    def _montar_grade(self) -> None:
        """Organiza os pares rótulo/valor em uma grade compacta de 4 linhas."""
        grade = QGridLayout(self)
        grade.setContentsMargins(10, 6, 10, 6)
        grade.setHorizontalSpacing(8)
        grade.setVerticalSpacing(3)
        grade.addWidget(_criar_rotulo_titulo(ROTULO_ARQUIVO), 0, 0)
        grade.addWidget(self._valor_arquivo, 0, 1, 1, 3)
        grade.addWidget(_criar_rotulo_titulo(ROTULO_TAMANHO), 1, 0)
        grade.addWidget(self._valor_tamanho, 1, 1)
        grade.addWidget(_criar_rotulo_titulo(ROTULO_DURACAO), 1, 2)
        grade.addWidget(self._valor_duracao, 1, 3)
        grade.addWidget(_criar_rotulo_titulo(ROTULO_STATUS), 2, 0)
        grade.addWidget(self._valor_status, 2, 1, 1, 3)
        grade.addWidget(_criar_rotulo_titulo(ROTULO_DECORRIDO), 3, 0)
        grade.addWidget(self._valor_decorrido, 3, 1)
        grade.addWidget(_criar_rotulo_titulo(ROTULO_RESTANTE), 3, 2)
        grade.addWidget(self._valor_restante, 3, 3)
        grade.setColumnStretch(1, 1)
        grade.setColumnStretch(3, 1)

    def exibir_arquivo(self, nome_exibicao: str, caminho_completo: str) -> None:
        """Preenche o nome do arquivo e define o caminho completo no tooltip."""
        self._valor_arquivo.setText(nome_exibicao)
        self._valor_arquivo.setToolTip(caminho_completo)

    def exibir_midia(self, tamanho_formatado: str, duracao_formatada: str) -> None:
        """Atualiza os campos de tamanho e duração do arquivo de entrada."""
        self._valor_tamanho.setText(tamanho_formatado)
        self._valor_duracao.setText(duracao_formatada)

    def atualizar_status(self, texto_status: str) -> None:
        """Atualiza o texto descritivo do status atual da janela."""
        self._valor_status.setText(texto_status)

    def atualizar_tempos(self, decorrido: str, restante: str) -> None:
        """Atualiza os indicadores de tempo decorrido e tempo restante estimado."""
        self._valor_decorrido.setText(decorrido)
        self._valor_restante.setText(restante)

    def limpar_informacoes(self) -> None:
        """Restaura todos os campos do painel para o estado inicial aguardando."""
        self._valor_arquivo.setText(TEXTO_VALOR_VAZIO)
        self._valor_arquivo.setToolTip("")
        self._valor_tamanho.setText(TEXTO_VALOR_VAZIO)
        self._valor_duracao.setText(TEXTO_VALOR_VAZIO)
        self._valor_status.setText(STATUS_AGUARDANDO)
        self._valor_decorrido.setText(TEXTO_VALOR_VAZIO)
        self._valor_restante.setText(TEXTO_VALOR_VAZIO)


# --- Fábricas e Diálogos Modais Públicos ---


def criar_botao_selecionar_nvenc(pai: QWidget) -> QPushButton:
    """Cria o botão 'Selecionar nvenc64' inicialmente oculto."""
    botao = QPushButton(TEXTO_BOTAO_SELECIONAR_NVENC, pai)
    botao.setObjectName("BotaoSelecionarNvenc")
    botao.setFixedSize(LARGURA_ZONA_ARRASTE, ALTURA_BOTAO_NVENC)
    botao.setCursor(Qt.CursorShape.PointingHandCursor)
    botao.setStyleSheet(gerar_estilo_botao_nvenc())
    botao.setVisible(False)
    return botao


def exibir_caixa_mensagem(
    pai: QWidget, icone: QMessageBox.Icon, texto: str, usar_html: bool = False
) -> None:
    """Cria e exibe um QMessageBox modal com botão único OK."""
    caixa = QMessageBox(pai)
    caixa.setIcon(icone)
    caixa.setWindowTitle(TITULO_POPUP)
    if usar_html:
        caixa.setTextFormat(Qt.TextFormat.RichText)
        caixa.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
    caixa.setText(texto)
    caixa.setStandardButtons(QMessageBox.StandardButton.Ok)
    caixa.exec()


def exibir_pergunta_sim_nao(pai: QWidget, texto: str) -> bool:
    """Exibe caixa de pergunta modal com botões 'Sim' e 'Não'."""
    caixa = QMessageBox(pai)
    caixa.setIcon(QMessageBox.Icon.Question)
    caixa.setWindowTitle(TITULO_POPUP)
    caixa.setText(texto)
    botao_sim = caixa.addButton("Sim", QMessageBox.ButtonRole.YesRole)
    botao_nao = caixa.addButton("Não", QMessageBox.ButtonRole.NoRole)
    caixa.setDefaultButton(botao_nao)
    caixa.exec()
    return caixa.clickedButton() == botao_sim


# --- Funções Auxiliares Privadas ---


def _criar_rotulo_titulo(texto: str) -> QLabel:
    """Cria um QLabel configurado como título de campo no painel."""
    rotulo = QLabel(texto)
    rotulo.setProperty("papel", "titulo")
    return rotulo


def _criar_rotulo_valor() -> QLabel:
    """Cria um QLabel configurado para exibir valores dinâmicos no painel."""
    rotulo = QLabel(TEXTO_VALOR_VAZIO)
    rotulo.setProperty("papel", "valor")
    return rotulo
