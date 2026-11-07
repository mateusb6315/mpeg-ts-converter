"""Funções puras de formatação de tamanho, duração, percentual e texto em pt-BR."""

import math
import re

from config.interface import LIMITE_CARACTERES_NOME_ARQUIVO, TEXTO_VALOR_VAZIO

# --- Constantes Locais de Escala ---
BYTES_POR_KB = 1024
BYTES_POR_MB = 1024**2
BYTES_POR_GB = 1024**3


# --- Formatadores Públicos ---


def formatar_tamanho(tamanho_bytes: int) -> str:
    """Formata uma quantidade de bytes em escala legível no padrão pt-BR.

    Args:
        tamanho_bytes: Tamanho do arquivo em bytes.

    Returns:
        Texto formatado (ex.: '1,2 GB', '35,0 MB', '512 bytes').
    """
    if tamanho_bytes < 0:
        return TEXTO_VALOR_VAZIO
    if tamanho_bytes >= BYTES_POR_GB:
        return _formatar_decimal_ptbr(tamanho_bytes / BYTES_POR_GB, "GB")
    if tamanho_bytes >= BYTES_POR_MB:
        return _formatar_decimal_ptbr(tamanho_bytes / BYTES_POR_MB, "MB")
    if tamanho_bytes >= BYTES_POR_KB:
        return _formatar_decimal_ptbr(tamanho_bytes / BYTES_POR_KB, "KB")
    return f"{tamanho_bytes} bytes"


def formatar_duracao(segundos: float | None) -> str:
    """Converte uma duração em segundos para o formato 'hh:mm:ss'.

    Args:
        segundos: Quantidade de segundos ou None se desconhecida.

    Returns:
        Duração formatada como 'hh:mm:ss' ou '—' quando inválida.
    """
    if segundos is None or not math.isfinite(segundos) or segundos < 0:
        return TEXTO_VALOR_VAZIO
    total_inteiro = int(segundos)
    horas = total_inteiro // 3600
    minutos = (total_inteiro % 3600) // 60
    segundos_restantes = total_inteiro % 60
    return f"{horas:02d}:{minutos:02d}:{segundos_restantes:02d}"


def formatar_percentual(percentual: float) -> str:
    """Formata um valor percentual limitado ao intervalo de 0 a 100 em pt-BR.

    Args:
        percentual: Valor numérico do percentual.

    Returns:
        Percentual formatado com vírgula decimal (ex.: '45,5%').
    """
    if not math.isfinite(percentual):
        return "0,0%"
    limitado = max(0.0, min(100.0, percentual))
    return f"{limitado:.1f}%".replace(".", ",")


def truncar_texto_meio(
    texto: str, limite: int = LIMITE_CARACTERES_NOME_ARQUIVO
) -> str:
    """Trunca textos longos no meio inserindo reticências ('…').

    Args:
        texto: Texto original a ser exibido.
        limite: Quantidade máxima de caracteres desejada.

    Returns:
        Texto original se couber no limite, ou versão truncada no meio.
    """
    if limite < 5 or len(texto) <= limite:
        return texto
    metade_esquerda = (limite - 1) // 2
    metade_direita = limite - 1 - metade_esquerda
    return f"{texto[:metade_esquerda]}…{texto[-metade_direita:]}"


def citar_argumento_comando(argumento: str) -> str:
    """Envolve um argumento de linha de comando em aspas se contiver espaços.

    Args:
        argumento: Argumento individual a ser formatado para registro em log.

    Returns:
        Argumento escapado com aspas duplas quando necessário.
    """
    if re.search(r'[\s"]', argumento):
        escapado = argumento.replace('"', '\\"')
        return f'"{escapado}"'
    return argumento


# --- Funções Auxiliares Privadas ---


def _formatar_decimal_ptbr(valor: float, unidade: str) -> str:
    """Formata número com uma casa decimal trocando ponto por vírgula."""
    numero_texto = f"{valor:.1f}".replace(".", ",")
    return f"{numero_texto} {unidade}"
