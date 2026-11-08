"""Inventário verificável e recursos da distribuição."""
import hashlib
import importlib.metadata
import shutil
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def hash_arquivo(caminho: Path) -> str:
    """Calcula SHA-256 sem carregar o pacote inteiro na memória."""
    with caminho.open("rb") as fluxo:
        return hashlib.file_digest(fluxo, "sha256").hexdigest()


def preparar_pacote(pasta: Path, versao: str, canal: str) -> dict:
    """Inclui documentação, licenças e proveniência antes de publicar a pasta."""
    for nome in ("LICENSE", "README.md"):
        shutil.copy2(RAIZ / nome, pasta / nome)
    licencas = pasta / "licencas"
    licencas.mkdir()
    dependencias = {}
    for pacote in ("PyQt6", "PyQt6-Qt6", "PyQt6_sip", "pyinstaller", "pyinstaller-hooks-contrib"):
        dist = importlib.metadata.distribution(pacote)
        dependencias[pacote] = dist.version
        for arquivo in dist.files or []:
            if any(termo in arquivo.name.lower() for termo in ("license", "copying", "notice")):
                destino = licencas / pacote / arquivo.name
                destino.parent.mkdir(exist_ok=True)
                shutil.copy2(dist.locate_file(arquivo), destino)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip()
    sujo = subprocess.check_output(["git", "status", "--porcelain"], cwd=RAIZ, text=True)
    arquivos = {p.relative_to(pasta).as_posix(): {"sha256": hash_arquivo(p),
                "bytes": p.stat().st_size} for p in pasta.rglob("*") if p.is_file()}
    return {"esquema": 1, "canal": canal, "commit": commit, "git_sujo": bool(sujo),
            "dependencias": dependencias, "arquivos": arquivos}
