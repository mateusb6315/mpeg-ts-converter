"""Configuração e aplicação forçada do tema claro na aplicação PyQt6."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from config.interface import (
    COR_DESTAQUE_SELECAO,
    COR_FUNDO_JANELA,
    COR_FUNDO_PAINEL,
    COR_TEXTO_DESABILITADO,
    COR_TEXTO_PRINCIPAL,
    COR_TEXTO_SELECAO,
)


# --- Configuração Pública de Tema ---


def aplicar_tema_claro(aplicacao: QApplication) -> None:
    """Força o estilo Fusion e uma paleta clara independente do tema do Windows.

    Args:
        aplicacao: Instância principal do QApplication.
    """
    aplicacao.setStyle("Fusion")
    _forcar_esquema_claro_qt(aplicacao)
    paleta = _construir_paleta_clara()
    aplicacao.setPalette(paleta)


# --- Funções Auxiliares Privadas ---


def _forcar_esquema_claro_qt(aplicacao: QApplication) -> None:
    """Aciona QStyleHints.setColorScheme(Light) nas versões do Qt que o suportam."""
    dicas_estilo = aplicacao.styleHints()
    esquema_enum = getattr(Qt, "ColorScheme", None)
    if dicas_estilo is not None and esquema_enum is not None:
        definir_esquema = getattr(dicas_estilo, "setColorScheme", None)
        if callable(definir_esquema):
            definir_esquema(esquema_enum.Light)


def _construir_paleta_clara() -> QPalette:
    """Cria uma QPalette explícita com cores claras para todas as funções de cor."""
    paleta = QPalette()
    cor_janela = QColor(COR_FUNDO_JANELA)
    cor_base = QColor(COR_FUNDO_PAINEL)
    cor_texto = QColor(COR_TEXTO_PRINCIPAL)
    cor_inativo = QColor(COR_TEXTO_DESABILITADO)
    _configurar_cores_principais(paleta, cor_janela, cor_base, cor_texto)
    _configurar_cores_selecao_e_inativo(paleta, cor_inativo)
    return paleta


def _configurar_cores_principais(
    paleta: QPalette, cor_janela: QColor, cor_base: QColor, cor_texto: QColor
) -> None:
    """Define as cores de superfície e texto padrão na paleta."""
    paleta.setColor(QPalette.ColorRole.Window, cor_janela)
    paleta.setColor(QPalette.ColorRole.WindowText, cor_texto)
    paleta.setColor(QPalette.ColorRole.Base, cor_base)
    paleta.setColor(QPalette.ColorRole.AlternateBase, cor_janela)
    paleta.setColor(QPalette.ColorRole.ToolTipBase, cor_base)
    paleta.setColor(QPalette.ColorRole.ToolTipText, cor_texto)
    paleta.setColor(QPalette.ColorRole.Text, cor_texto)
    paleta.setColor(QPalette.ColorRole.Button, cor_janela)
    paleta.setColor(QPalette.ColorRole.ButtonText, cor_texto)


def _configurar_cores_selecao_e_inativo(
    paleta: QPalette, cor_inativo: QColor
) -> None:
    """Define as cores de destaque de seleção e de estado desabilitado."""
    paleta.setColor(QPalette.ColorRole.Highlight, QColor(COR_DESTAQUE_SELECAO))
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor(COR_TEXTO_SELECAO))
    paleta.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, cor_inativo
    )
    paleta.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, cor_inativo
    )
    paleta.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, cor_inativo
    )
