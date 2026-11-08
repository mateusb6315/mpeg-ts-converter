"""Serviço de leitura de metadados de arquivo, sondagem via ffprobe e busca do NVEncC."""

import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

from config.configuracoes import (
    DIRETORIO_PADRAO_NVENC,
    NOMES_EXECUTAVEL_FFPROBE,
    NOMES_EXECUTAVEL_NVENC,
    TAXA_QUADROS_SAIDA,
    TIMEOUT_SONDAGEM_SEGUNDOS,
    VARIAVEL_AMBIENTE_NVENC,
)
from modelos.conversao import InformacoesArquivo, calcular_total_quadros, eh_arquivo_ts


# --- Validação e Leitura de Metadados ---


def validar_arquivo_ts_local(caminho: Path) -> bool:
    """Confirma que o caminho corresponde a um arquivo .ts existente no disco.

    Args:
        caminho: Caminho local recebido da interface gráfica.

    Returns:
        True se o caminho existir, for um arquivo regular e tiver extensão .ts.
    """
    try:
        return eh_arquivo_ts(caminho) and caminho.is_file()
    except OSError:
        return False


def ler_informacoes_arquivo(caminho: Path) -> InformacoesArquivo:
    """Coleta tamanho em bytes, duração em segundos e total estimado de quadros.

    Args:
        caminho: Caminho do arquivo .ts de entrada.

    Returns:
        Objeto InformacoesArquivo preenchido com os metadados disponíveis.
    """
    try:
        tamanho_bytes = caminho.stat().st_size
    except OSError:
        tamanho_bytes = 0
    duracao = sondar_duracao_arquivo(caminho)
    total_quadros = calcular_total_quadros(duracao, TAXA_QUADROS_SAIDA)
    return InformacoesArquivo(
        caminho=caminho,
        tamanho_bytes=tamanho_bytes,
        duracao_segundos=duracao,
        total_quadros=total_quadros,
    )


# --- Sondagem de Mídia com ffprobe ---


def sondar_duracao_arquivo(caminho: Path) -> float | None:
    """Obtém a duração em segundos do arquivo de vídeo usando o ffprobe.

    Args:
        caminho: Caminho do arquivo de mídia a ser analisado.

    Returns:
        Duração em segundos ou None caso o ffprobe não esteja disponível ou falhe.
    """
    executavel = _localizar_ffprobe()
    if not executavel:
        return None
    comando = [
        executavel,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=nw=1:nk=1",
        "--",
        str(caminho),
    ]
    saida = _executar_sondagem_silenciosa(comando)
    if not saida:
        return None
    return _converter_duracao_valida(saida)


def sondar_fluxos_midia(caminho: Path) -> list[dict] | None:
    """Retorna a lista de fluxos (streams) de áudio e vídeo lida pelo ffprobe.

    Args:
        caminho: Caminho do arquivo de mídia.

    Returns:
        Lista de dicionários com metadados das faixas ou None se indisponível.
    """
    executavel = _localizar_ffprobe()
    if not executavel:
        return None
    comando = [
        executavel,
        "-v",
        "error",
        "-show_entries",
        "stream=codec_type,channels,channel_layout,start_time",
        "-of",
        "json",
        "--",
        str(caminho),
    ]
    saida = _executar_sondagem_silenciosa(comando)
    if not saida:
        return None
    try:
        dados = json.loads(saida)
        fluxos = dados.get("streams") if isinstance(dados, dict) else None
        if not isinstance(fluxos, list) or any(not isinstance(f, dict) for f in fluxos):
            return None
        return fluxos
    except ValueError:
        return None


# --- Localização do Executável NVEncC ---


def localizar_executavel_nvenc() -> Path | None:
    """Procura o executável do NVEncC em variável de ambiente, PATH, pasta local e padrão.

    Returns:
        Caminho resolvido do executável NVEncC ou None se não encontrado.
    """
    # EXTENSÃO: Adicione novos diretórios candidatos à busca automática abaixo.
    da_variavel = resolver_candidato_executavel(os.environ.get(VARIAVEL_AMBIENTE_NVENC))
    if da_variavel:
        return da_variavel
    do_path_ou_local = _buscar_nvenc_em_path_e_diretorio_local()
    if do_path_ou_local:
        return do_path_ou_local
    do_padrao = resolver_candidato_executavel(str(DIRETORIO_PADRAO_NVENC))
    if do_padrao:
        os.environ[VARIAVEL_AMBIENTE_NVENC] = str(do_padrao)
    return do_padrao


def resolver_candidato_executavel(caminho_bruto: str | None) -> Path | None:
    """Resolve um caminho de arquivo ou diretório candidato ao executável do NVEncC.

    Args:
        caminho_bruto: Caminho informado em variável de ambiente ou configuração.

    Returns:
        Caminho absoluto do executável válido ou None se não existir.
    """
    if not caminho_bruto or not caminho_bruto.strip():
        return None
    limpo = os.path.expandvars(caminho_bruto.strip().strip('"').strip("'"))
    caminho = Path(limpo).expanduser()
    try:
        if caminho.is_file():
            return caminho.resolve()
        if caminho.is_dir():
            return _procurar_binario_na_pasta(caminho)
    except (OSError, ValueError):
        return None
    return None


# --- Funções Auxiliares Privadas ---


def _localizar_ffprobe() -> str | None:
    """Retorna o caminho do executável ffprobe presente no PATH do sistema."""
    for nome in NOMES_EXECUTAVEL_FFPROBE:
        encontrado = shutil.which(nome)
        if encontrado:
            return encontrado
    return None


def _executar_sondagem_silenciosa(comando: list[str]) -> str | None:
    """Executa um subprocesso rápido sem abrir janela de console no Windows."""
    # CREATE_NO_WINDOW impede que o ffprobe pisque uma janela preta durante a GUI.
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_SONDAGEM_SEGUNDOS,
            check=False,
            creationflags=flags,
        )
        if resultado.returncode != 0:
            return None
        return resultado.stdout
    except (OSError, subprocess.SubprocessError):
        return None


def _converter_duracao_valida(saida_texto: str) -> float | None:
    """Extrai e valida o primeiro número de duração positivo da saída do ffprobe."""
    try:
        primeira_linha = saida_texto.strip().splitlines()[0]
        duracao = float(primeira_linha)
        if math.isfinite(duracao) and duracao > 0:
            return duracao
    except (IndexError, ValueError):
        return None
    return None


def _buscar_nvenc_em_path_e_diretorio_local() -> Path | None:
    """Procura o NVEncC no PATH do sistema e no diretório raiz da aplicação."""
    diretorio_base = _obter_diretorio_base()
    for nome in NOMES_EXECUTAVEL_NVENC:
        no_path = shutil.which(nome)
        if no_path:
            resolvido = resolver_candidato_executavel(no_path)
            if resolvido:
                return resolvido
        local = resolver_candidato_executavel(str(diretorio_base / nome))
        if local:
            return local
    return None


def _procurar_binario_na_pasta(pasta: Path) -> Path | None:
    """Verifica se algum dos nomes conhecidos do NVEncC existe dentro da pasta."""
    for nome in NOMES_EXECUTAVEL_NVENC:
        candidato = pasta / nome
        if candidato.is_file():
            return candidato.resolve()
    return None


def _obter_diretorio_base() -> Path:
    """Retorna o diretório raiz do projeto ou do executável empacotado."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent
