"""Estruturas de dados e regras de negócio puras para conversão de arquivos .ts."""

from dataclasses import dataclass
from enum import Enum
import math
from pathlib import Path
import re

from config.configuracoes import (
    ARGUMENTOS_BASE_NVENC,
    ARGUMENTOS_CODIFICACAO_HEVC,
    EXTENSAO_ENTRADA_VALIDA,
    PERCENTUAL_MAXIMO_EM_ANDAMENTO,
    PERCENTUAL_MINIMO,
    SUFIXO_ARQUIVO_SAIDA,
    TAXA_QUADROS_SAIDA,
    TOLERANCIA_DESLOCAMENTO_AV_SEGUNDOS,
)

# --- Expressões Regulares de Progresso do NVEncC ---
PADRAO_QUADROS_LEGADO = re.compile(r"(?i)(?P<f>\d+)\s+frames\b")
PADRAO_QUADROS_CODIFICADOS = re.compile(r"(?i)encoded\s+(?P<f>\d+)")
PADRAO_TAXA_QUADROS = re.compile(r"(?P<v>\d+(?:\.\d+)?)\s*fps", re.IGNORECASE)
PADRAO_TAXA_BITS = re.compile(
    r"(?P<v>\d+(?:\.\d+)?)\s*(?P<u>kbps|kb/s|Mbps)", re.IGNORECASE
)
PADRAO_PERCENTUAL_LINHA = re.compile(r"\[?\s*(?P<p>\d+(?:\.\d+)?)\s*%\s*\]?")


# --- Enumerações e Estruturas de Dados ---


class EstadoConversao(Enum):
    """Estados possíveis do fluxo de conversão na interface."""

    AGUARDANDO = "aguardando"
    CONVERTENDO = "convertendo"
    CONCLUIDA = "concluida"
    FALHOU = "falhou"


@dataclass(frozen=True)
class InformacoesArquivo:
    """Metadados do arquivo de vídeo de entrada."""

    caminho: Path
    tamanho_bytes: int
    duracao_segundos: float | None = None
    total_quadros: int | None = None


@dataclass(frozen=True)
class SegmentoProgresso:
    """Dados extraídos de uma linha de progresso emitida pelo NVEncC."""

    quadros_codificados: int
    quadros_por_segundo: float
    taxa_bits: str
    percentual_direto: float | None = None


@dataclass(frozen=True)
class LinhaLog:
    """Linha comum de saída do codificador que não representa progresso."""

    texto: str


SegmentoSaida = SegmentoProgresso | LinhaLog | None


# --- Validações e Regras de Caminho ---


def eh_arquivo_ts(caminho: Path) -> bool:
    """Verifica de forma pura se o caminho possui nome válido e extensão .ts."""
    if not isinstance(caminho, Path) or not caminho.name:
        return False
    return bool(caminho.stem) and caminho.suffix.lower() == EXTENSAO_ENTRADA_VALIDA


def gerar_caminho_saida(caminho_entrada: Path) -> Path:
    """Gera o caminho do arquivo MKV de saída no mesmo diretório do original."""
    return caminho_entrada.parent / f"{caminho_entrada.stem}{SUFIXO_ARQUIVO_SAIDA}"


# --- Cálculos de Quadros, Progresso e Tempo ---


def calcular_total_quadros(
    duracao_segundos: float | None, taxa_quadros: float = TAXA_QUADROS_SAIDA
) -> int | None:
    """Estima o total de quadros de saída após o desentrelaçamento bob (59,94 fps)."""
    if duracao_segundos is None or not math.isfinite(duracao_segundos):
        return None
    if duracao_segundos <= 0 or taxa_quadros <= 0:
        return None
    return math.floor(duracao_segundos * taxa_quadros + 0.5)


def calcular_percentual_progresso(
    quadros_codificados: int,
    total_quadros: int | None,
    percentual_anterior: float = 0.0,
    percentual_direto: float | None = None,
) -> float:
    """Calcula o percentual de andamento garantindo monotonia no intervalo [0, 99.9]."""
    base = max(
        PERCENTUAL_MINIMO, min(PERCENTUAL_MAXIMO_EM_ANDAMENTO, percentual_anterior)
    )
    if total_quadros and total_quadros > 0 and quadros_codificados >= 0:
        calculado = (quadros_codificados / total_quadros) * 100.0
    elif percentual_direto is not None and math.isfinite(percentual_direto):
        calculado = percentual_direto
    else:
        return base
    limitado = max(PERCENTUAL_MINIMO, min(PERCENTUAL_MAXIMO_EM_ANDAMENTO, calculado))
    return max(base, limitado)


def calcular_tempo_restante(
    percentual: float, segundos_decorridos: float
) -> float | None:
    """Estima o tempo restante em segundos com base no percentual e tempo decorrido."""
    if not math.isfinite(percentual) or not math.isfinite(segundos_decorridos):
        return None
    if percentual < 0.5 or percentual >= 100.0 or segundos_decorridos < 1.0:
        return None
    return segundos_decorridos * (100.0 - percentual) / percentual


# --- Parsing e Construção de Comandos NVEncC ---


def parsear_segmento_progresso(linha: str) -> SegmentoSaida:
    """Analisa uma linha de saída do NVEncC e classifica como progresso ou log."""
    if not linha or not linha.strip():
        return None
    quadros_legado = PADRAO_QUADROS_LEGADO.search(linha)
    eh_progresso = bool(re.search("encoded", linha, re.IGNORECASE)) or (
        quadros_legado is not None and "%" in linha and "fps" in linha.lower()
    )
    if not eh_progresso:
        return LinhaLog(linha)
    return _extrair_dados_progresso(linha, quadros_legado)


def selecionar_argumentos_audio(
    fluxos_midia: list[dict] | None,
) -> tuple[list[str], list[dict] | None]:
    """Monta os argumentos de cópia de áudio para o NVEncC a partir dos fluxos lidos."""
    if fluxos_midia is None:
        return ["--audio-copy"], None
    faixas_audio = [f for f in fluxos_midia if f.get("codec_type") == "audio"]
    if not faixas_audio:
        return [], []
    # O NVEncC numera as faixas de áudio de 1..N (e não pelo índice global do ffprobe).
    seletores = ",".join(str(indice) for indice in range(1, len(faixas_audio) + 1))
    return ["--audio-copy", seletores], faixas_audio


def construir_argumentos_nvenc(
    caminho_entrada: Path, caminho_saida: Path, argumentos_audio: list[str]
) -> list[str]:
    """Constrói a lista completa de parâmetros de linha de comando do NVEncC."""
    return [
        *ARGUMENTOS_BASE_NVENC,
        "-i",
        str(caminho_entrada),
        *ARGUMENTOS_CODIFICACAO_HEVC,
        *argumentos_audio,
        "-o",
        str(caminho_saida),
    ]


def validar_fluxos_audio(
    fluxos_origem: list[dict], fluxos_saida: list[dict]
) -> list[str]:
    """Compara quantidade, layout de canais e sincronia A/V entre origem e saída."""
    audio_origem = [f for f in fluxos_origem if f.get("codec_type") == "audio"]
    audio_saida = [f for f in fluxos_saida if f.get("codec_type") == "audio"]
    problemas = _comparar_layouts_audio(audio_origem, audio_saida)
    problemas.extend(_comparar_sincronia_av(fluxos_origem, fluxos_saida))
    return problemas


# --- Funções Auxiliares Privadas ---


def _extrair_dados_progresso(
    linha: str, quadros_legado: re.Match[str] | None
) -> SegmentoProgresso:
    """Extrai contagem de quadros, FPS, bitrate e percentual de uma linha de progresso."""
    match_quadros = PADRAO_QUADROS_CODIFICADOS.search(linha) or quadros_legado
    match_fps = PADRAO_TAXA_QUADROS.search(linha)
    match_bitrate = PADRAO_TAXA_BITS.search(linha)
    match_pct = PADRAO_PERCENTUAL_LINHA.search(linha)
    return SegmentoProgresso(
        quadros_codificados=int(match_quadros.group("f")) if match_quadros else -1,
        quadros_por_segundo=float(match_fps.group("v")) if match_fps else 0.0,
        taxa_bits=match_bitrate.group(0).strip() if match_bitrate else "",
        percentual_direto=float(match_pct.group("p")) if match_pct else None,
    )


def _comparar_layouts_audio(
    audio_origem: list[dict], audio_saida: list[dict]
) -> list[str]:
    """Verifica diferenças na contagem de faixas e nos layouts de canais de áudio."""
    problemas: list[str] = []
    if len(audio_origem) != len(audio_saida):
        problemas.append(
            f"faixas de áudio: origem {len(audio_origem)}, saída {len(audio_saida)}"
        )
    for indice, (origem, saida) in enumerate(zip(audio_origem, audio_saida), start=1):
        if origem.get("channels") != saida.get("channels") or origem.get(
            "channel_layout"
        ) != saida.get("channel_layout"):
            orig_l = origem.get("channel_layout", origem.get("channels"))
            dest_l = saida.get("channel_layout", saida.get("channels"))
            problemas.append(f"faixa {indice}: layout origem {orig_l}, saída {dest_l}")
    return problemas


def _comparar_sincronia_av(
    fluxos_origem: list[dict], fluxos_saida: list[dict]
) -> list[str]:
    """Compara o deslocamento de start_time entre áudio e vídeo antes e pós-conversão."""
    problemas: list[str] = []
    v_orig = next((f for f in fluxos_origem if f.get("codec_type") == "video"), {})
    v_dest = next((f for f in fluxos_saida if f.get("codec_type") == "video"), {})
    a_orig = [f for f in fluxos_origem if f.get("codec_type") == "audio"]
    a_dest = [f for f in fluxos_saida if f.get("codec_type") == "audio"]
    for indice, (orig, dest) in enumerate(zip(a_orig, a_dest), start=1):
        try:
            valores = [float(f["start_time"]) for f in (v_orig, v_dest, orig, dest)]
            if not all(math.isfinite(valor) for valor in valores):
                raise ValueError
            off_orig = valores[2] - valores[0]
            off_dest = valores[3] - valores[1]
            if abs(off_orig - off_dest) > TOLERANCIA_DESLOCAMENTO_AV_SEGUNDOS:
                problemas.append(f"faixa {indice}: deslocamento A/V mudou em "
                                 f"{off_orig:.3f}s → {off_dest:.3f}s")
        except (KeyError, TypeError, ValueError):
            problemas.append(f"faixa {indice}: sincronia A/V não verificável")
    return problemas
