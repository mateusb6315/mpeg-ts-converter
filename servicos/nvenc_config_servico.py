"""Serviço de verificação em segundo plano e persistência do executável nvenc64."""

import logging
import os
from pathlib import Path
import subprocess

from config.configuracoes import (
    CHAVE_REGISTRO_AMBIENTE_USUARIO,
    DIRETORIO_PADRAO_PROGRAM_FILES,
    NOMES_ACEITOS_SELECAO_NVENC,
    VARIAVEL_AMBIENTE_NVENC,
)
from servicos.arquivo_servico import (
    localizar_executavel_nvenc,
    resolver_candidato_executavel,
)

REGISTRADOR = logging.getLogger(__name__)
CHAVE_REGISTRO_AMBIENTE_SISTEMA = (
    r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
)


# --- Verificação e Persistência do Executável nvenc64 ---


def verificar_ambiente_nvenc() -> Path | None:
    """Inspeciona variáveis de ambiente do Windows e locais padrão em busca do nvenc64.

    Returns:
        Caminho absoluto do executável nvenc64 encontrado ou None caso ausente.
    """
    _sincronizar_variavel_do_registro_windows()
    encontrado = localizar_executavel_nvenc()
    if encontrado is not None and encontrado.is_file():
        os.environ[VARIAVEL_AMBIENTE_NVENC] = str(encontrado)
        REGISTRADOR.info("Executável nvenc64 identificado: %s", encontrado)
        return encontrado
    REGISTRADOR.warning("Executável nvenc64 não foi identificado automaticamente.")
    return None


def validar_executavel_nvenc_selecionado(caminho: Path) -> bool:
    """Verifica se o arquivo escolhido pelo usuário é um executável nvenc64 válido.

    Args:
        caminho: Caminho selecionado no Windows Explorer.

    Returns:
        True se o arquivo existir e tiver nome nvenc64.exe ou NVEncC64.exe.
    """
    if not isinstance(caminho, Path) or not caminho.name:
        return False
    if caminho.name.lower() not in NOMES_ACEITOS_SELECAO_NVENC:
        return False
    try:
        return caminho.is_file()
    except OSError:
        return False


def salvar_executavel_nvenc_manual(caminho: Path) -> bool:
    """Registra o executável selecionado na sessão atual e no ambiente do Windows.

    Args:
        caminho: Caminho do executável nvenc64 validado.

    Returns:
        True se o caminho for válido e tiver sido aplicado na sessão atual.
    """
    if not validar_executavel_nvenc_selecionado(caminho):
        return False
    resolvido = caminho.resolve()
    os.environ[VARIAVEL_AMBIENTE_NVENC] = str(resolvido)
    _persistir_variavel_usuario_windows(VARIAVEL_AMBIENTE_NVENC, str(resolvido))
    REGISTRADOR.info("Executável nvenc64 configurado manualmente: %s", resolvido)
    return True


def obter_diretorio_program_files() -> Path:
    """Retorna o diretório Program Files do Windows para iniciar a seleção manual.

    Returns:
        Caminho para 'C:\\Program Files' ou pasta equivalente do sistema.
    """
    valor_ambiente = os.environ.get("ProgramFiles")
    if valor_ambiente:
        candidato = Path(valor_ambiente)
        if candidato.is_dir():
            return candidato
    return DIRETORIO_PADRAO_PROGRAM_FILES


# --- Funções Auxiliares Privadas ---


def _sincronizar_variavel_do_registro_windows() -> None:
    """Lê a variável nvenc64 do Registro do Windows caso não esteja em os.environ."""
    atual = resolver_candidato_executavel(os.environ.get(VARIAVEL_AMBIENTE_NVENC))
    if atual is not None:
        return
    valor_registro = _ler_variavel_registro_windows(VARIAVEL_AMBIENTE_NVENC)
    resolvido = resolver_candidato_executavel(valor_registro)
    if resolvido is not None:
        os.environ[VARIAVEL_AMBIENTE_NVENC] = str(resolvido)


def _ler_variavel_registro_windows(nome_variavel: str) -> str | None:
    """Busca uma variável de ambiente nas chaves de usuário (HKCU) e sistema (HKLM)."""
    if os.name != "nt":
        return None
    try:
        import winreg

        locais = (
            (winreg.HKEY_CURRENT_USER, CHAVE_REGISTRO_AMBIENTE_USUARIO),
            (winreg.HKEY_LOCAL_MACHINE, CHAVE_REGISTRO_AMBIENTE_SISTEMA),
        )
        for raiz, subchave in locais:
            valor = _consultar_chave_registro(winreg, raiz, subchave, nome_variavel)
            if valor:
                return valor
    except (ImportError, OSError):
        return None
    return None


def _consultar_chave_registro(
    modulo_winreg, raiz: int, subchave: str, nome: str
) -> str | None:
    """Lê um valor textual específico dentro de uma chave do Registro do Windows."""
    try:
        with modulo_winreg.OpenKey(raiz, subchave) as chave:
            valor, _ = modulo_winreg.QueryValueEx(chave, nome)
            return str(valor) if valor else None
    except OSError:
        return None


def _persistir_variavel_usuario_windows(nome: str, valor: str) -> None:
    """Grava a variável de ambiente do usuário no Registro do Windows ou via setx."""
    if os.name != "nt":
        return
    if _gravar_no_registro_usuario(nome, valor):
        return
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.run(
            ["setx", nome, valor],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            creationflags=flags,
        )
    except (OSError, subprocess.SubprocessError) as erro:
        REGISTRADOR.warning("Não foi possível persistir variável %s: %s", nome, erro)


def _gravar_no_registro_usuario(nome: str, valor: str) -> bool:
    """Salva a variável diretamente em HKCU\\Environment sem invocar console."""
    try:
        import winreg

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER, CHAVE_REGISTRO_AMBIENTE_USUARIO
        ) as chave:
            winreg.SetValueEx(chave, nome, 0, winreg.REG_SZ, valor)
        return True
    except (ImportError, OSError):
        return False
