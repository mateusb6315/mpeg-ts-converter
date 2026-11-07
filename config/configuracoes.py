"""Constantes, caminhos e parâmetros do motor de conversão NVEncC."""

from pathlib import Path

# --- Localização e Configuração do Executável NVEncC ---
DIRETORIO_PADRAO_NVENC = Path(r"C:\Program Files\NVEncC_9.31_x64")
DIRETORIO_PADRAO_PROGRAM_FILES = Path(r"C:\Program Files")
NOMES_EXECUTAVEL_NVENC = ("NVEncC64.exe", "NVEncC.exe", "nvenc64.exe")
NOMES_ACEITOS_SELECAO_NVENC = ("nvenc64.exe", "nvencc64.exe")
VARIAVEL_AMBIENTE_NVENC = "nvenc64"
CHAVE_REGISTRO_AMBIENTE_USUARIO = "Environment"
URL_DOWNLOAD_NVENC = "https://github.com/rigaya/NVEnc/releases"
VERSAO_MINIMA_NVENC_SINCRONIA = (9, 18)

# --- Filtros de Seleção do Windows Explorer ---
FILTRO_DIALOGO_NVENC = "Executável nvenc64 (nvenc64.exe NVEncC64.exe)"
FILTRO_DIALOGO_TS = "Arquivos MPEG-TS (*.ts)"

# --- Localização do Executável ffprobe ---
NOMES_EXECUTAVEL_FFPROBE = ("ffprobe", "ffprobe.exe")

# --- Parâmetros de Vídeo e Conversão ---
TAXA_QUADROS_SAIDA = 59.94
EXTENSAO_ENTRADA_VALIDA = ".ts"
SUFIXO_ARQUIVO_SAIDA = "_60fps_bwdif.mkv"
EXTENSAO_SAIDA_PADRAO = ".mkv"
CARACTERES_INVALIDOS_NOME = frozenset('<>:\\|?*')

# --- Argumentos Fixos do Codificador NVEncC ---
# EXTENSÃO: Adicione novos perfis ou filtros de vídeo aqui mantendo a tupla imutável.
ARGUMENTOS_BASE_NVENC = (
    "--log-level",
    "error,core_progress=info,core_result=info",
    "--avhw",
    "--interlace",
    "tff",
    "--vpp-bwdif",
    "mode=bob,order=tff",
    "--avsync",
    "forcecfr",
    "--input-analyze",
    "60",
)

ARGUMENTOS_CODIFICACAO_HEVC = (
    "-c",
    "hevc",
    "-u",
    "p7",
    "--qvbr",
    "18",
    "--output-depth",
    "10",
    "--profile",
    "main10",
    "--aq",
    "--aq-temporal",
    "--colormatrix",
    "auto",
    "--colorprim",
    "auto",
    "--transfer",
    "auto",
    "--chromaloc",
    "auto",
    "--video-metadata",
    "copy",
    "--audio-metadata",
    "copy",
)

# --- Limites e Tolerâncias Técnicas ---
TOLERANCIA_DESLOCAMENTO_AV_SEGUNDOS = 0.100
LIMITE_BUFFER_SEGMENTO_BYTES = 32768
MAXIMO_LINHAS_ERRO_LOG = 30
TIMEOUT_SONDAGEM_SEGUNDOS = 10
PERCENTUAL_MINIMO = 0.0
PERCENTUAL_MAXIMO_EM_ANDAMENTO = 99.9
PERCENTUAL_CONCLUIDO = 100.0
