"""Folhas de estilo QSS da janela principal, zona de arraste, botão e barra."""

from config.interface import (
    COR_BARRA_BORDA,
    COR_BARRA_FUNDO,
    COR_BARRA_PREENCHIMENTO,
    COR_BARRA_TEXTO,
    COR_BORDA_ZONA_ATIVA,
    COR_BORDA_ZONA_INATIVA,
    COR_BOTAO_BORDA,
    COR_BOTAO_FUNDO,
    COR_BOTAO_HOVER,
    COR_FUNDO_JANELA,
    COR_FUNDO_PAINEL,
    COR_FUNDO_ZONA_ATIVA,
    COR_FUNDO_ZONA_INATIVA,
    COR_TEXTO_DESABILITADO,
    COR_TEXTO_PRINCIPAL,
    COR_TEXTO_SECUNDARIO,
)


# --- Geradores Públicos de QSS ---


def gerar_estilo_janela() -> str:
    """Retorna o QSS base da janela principal em modo claro."""
    return (
        f"QWidget#JanelaPrincipal {{ background-color: {COR_FUNDO_JANELA}; "
        f"color: {COR_TEXTO_PRINCIPAL}; font-family: 'Segoe UI', sans-serif; "
        f"font-size: 11px; }}"
    )


def gerar_estilo_zona_arraste(ocupada: bool) -> str:
    """Gera o QSS da zona de arraste conforme o estado ativo ou em conversão.

    Args:
        ocupada: True para aplicar aparência desabilitada durante a conversão.

    Returns:
        String contendo a regra QSS para o QFrame e seu QLabel interno.
    """
    fundo = COR_FUNDO_ZONA_INATIVA if ocupada else COR_FUNDO_ZONA_ATIVA
    borda = COR_BORDA_ZONA_INATIVA if ocupada else COR_BORDA_ZONA_ATIVA
    cor_texto = COR_TEXTO_DESABILITADO if ocupada else COR_TEXTO_SECUNDARIO
    return (
        f"QFrame#ZonaArraste {{ background-color: {fundo}; "
        f"border: 1.5px dashed {borda}; border-radius: 4px; }} "
        f"QLabel#RotuloZonaArraste {{ color: {cor_texto}; font-size: 11px; "
        f"font-weight: 600; background: transparent; border: none; }}"
    )


def gerar_estilo_botao_nvenc() -> str:
    """Retorna o QSS do botão de seleção manual do executável nvenc64."""
    return (
        f"QPushButton#BotaoSelecionarNvenc {{ background-color: {COR_BOTAO_FUNDO}; "
        f"color: {COR_BOTAO_BORDA}; border: 1px solid {COR_BOTAO_BORDA}; "
        f"border-radius: 3px; font-size: 11px; font-weight: 600; padding: 2px 6px; }} "
        f"QPushButton#BotaoSelecionarNvenc:hover {{ background-color: {COR_BOTAO_HOVER}; }}"
    )


def gerar_estilo_painel_informacoes() -> str:
    """Retorna o QSS do painel lateral de informações do arquivo e do processo."""
    return (
        f"QFrame#PainelInformacoes {{ background-color: {COR_FUNDO_PAINEL}; "
        f"border: 1px solid {COR_BARRA_BORDA}; border-radius: 4px; }} "
        f"QLabel[papel='titulo'] {{ color: {COR_TEXTO_SECUNDARIO}; "
        f"font-size: 11px; font-weight: 600; background: transparent; }} "
        f"QLabel[papel='valor'] {{ color: {COR_TEXTO_PRINCIPAL}; "
        f"font-size: 11px; background: transparent; }}"
    )


def gerar_estilo_barra_progresso() -> str:
    """Retorna o QSS da barra de progresso no estilo verde clássico do Windows."""
    return (
        f"QProgressBar#BarraProgresso {{ background-color: {COR_BARRA_FUNDO}; "
        f"border: 1px solid {COR_BARRA_BORDA}; border-radius: 2px; "
        f"text-align: center; color: {COR_BARRA_TEXTO}; "
        f"font-size: 11px; font-weight: 600; }} "
        f"QProgressBar#BarraProgresso::chunk {{ "
        f"background-color: {COR_BARRA_PREENCHIMENTO}; border-radius: 0px; }}"
    )
