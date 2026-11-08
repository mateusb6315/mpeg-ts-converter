"""Compila e versiona as distribuições do Projeto Broadcast."""

import json
import shutil
import time
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
from scripts.distribuicao.ambiente import ambiente_compilacao

NOME = "mpeg-ts-converter"
ICONE = RAIZ / "modelos" / "logo" / "icon.png"

def status(mensagem: str) -> None:
    """Escreve o progresso imediatamente no terminal."""
    print(f"[compilação] {mensagem}", flush=True)


def _converter_icone(temporario: Path) -> Path:
    """Converte o ícone PNG para ICO dentro da pasta temporária do build."""
    from PIL import Image

    if not ICONE.is_file():
        raise FileNotFoundError(f"Ícone do executável não encontrado: {ICONE}")
    destino = temporario / "mpeg-ts-converter.ico"
    with Image.open(ICONE) as imagem:
        imagem.convert("RGBA").save(destino, format="ICO",
                                     sizes=[(16, 16), (32, 32), (48, 48),
                                            (64, 64), (128, 128), (256, 256)])
    return destino


def _montar_comando_pyinstaller(temporario: Path, console: bool = False) -> list[str]:
    """Monta a linha de comando do PyInstaller no diretório temporário informado."""
    icone = _converter_icone(temporario)
    return [
        sys.executable,
        "-u",
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--console" if console else "--windowed",
        "--noupx",
        "--name",
        NOME,
        "--icon",
        str(icone),
        "--distpath",
        str(temporario / "dist"),
        "--workpath",
        str(temporario / "work"),
        "--specpath",
        str(temporario),
        str(RAIZ / "main.py"),
    ]


def executar_pyinstaller(temporario: Path, executar, console: bool = False) -> Path:
    """Executa o PyInstaller em silêncio e mostra a saída somente em caso de falha."""
    status("Executando PyInstaller...")
    status("Fazendo a compilação...")
    try:
        executar(
            _montar_comando_pyinstaller(temporario, console),
            cwd=RAIZ,
            env=ambiente_compilacao(),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError as erro:
        _exibir_saida_falha(erro)
        raise
    pasta = temporario / "dist" / NOME
    if not (pasta / f"{NOME}.exe").is_file():
        raise RuntimeError("PyInstaller não gerou o executável esperado.")
    return pasta


def _exibir_saida_falha(erro: subprocess.CalledProcessError) -> None:
    """Mostra as últimas linhas capturadas do PyInstaller para diagnosticar a falha."""
    linhas = f"{erro.stdout or ''}\n{erro.stderr or ''}".strip().splitlines()
    status("Últimas linhas do PyInstaller:")
    for linha in linhas[-30:]:
        print(linha, flush=True)


def compilar(diretorio: Path, executar=subprocess.run,
             versao: str = "", console: bool = False) -> Path:
    """Gera uma distribuição sem consultar histórico de versões."""
    from scripts.distribuicao.versoes import validar_nome
    from scripts.distribuicao.manifesto import preparar_pacote

    validar_nome(versao)
    diretorio.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".compilacao-", dir=diretorio) as temp:
        pasta = executar_pyinstaller(Path(temp), executar, console)
        item = {"versao": versao}
        item.update(preparar_pacote(pasta, versao, diretorio.name))
        (pasta / "build.json").write_text(
            json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
        destino = diretorio / f"{NOME} {versao}"
        numero = 2
        while destino.exists():
            destino = diretorio / f"{NOME} {versao} ({numero})"
            numero += 1
        _publicar_pasta(pasta, destino)
    status(f"Compilação concluída: {destino}")
    return destino


def _publicar_pasta(pasta: Path, destino: Path) -> None:
    """Tenta novamente bloqueios temporários e recorre à cópia quando necessário."""
    for tentativa in range(10):
        try:
            pasta.rename(destino)
            return
        except PermissionError:
            if destino.exists():
                raise FileExistsError(f"Destino já existe: {destino}")
            if tentativa < 9:
                time.sleep(0.5)
    status("Movimentação bloqueada; tentando copiar a distribuição...")
    # mkdir exclusivo evita sobrescrever uma pasta criada por outro processo.
    destino.mkdir()
    try:
        shutil.copytree(pasta, destino, dirs_exist_ok=True)
    except Exception:
        shutil.rmtree(destino, ignore_errors=True)
        raise
