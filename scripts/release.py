"""Publica no GitHub o prototype mais recente em uma nova release beta."""

import json
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PADRAO = re.compile(r"beta[ -]0\.([1-9][0-9]*)", re.IGNORECASE)


def comando(*args: str) -> str:
    """Executa o GitHub CLI e informa a causa de falhas."""
    resultado = subprocess.run(
        args,
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if resultado.returncode:
        raise RuntimeError(resultado.stderr.strip() or "Comando falhou.")
    return resultado.stdout


def releases() -> list[dict]:
    """Lista todas as releases, incluindo pré-releases e rascunhos."""
    saida = comando(
        "gh",
        "api",
        "--paginate",
        "--slurp",
        "repos/{owner}/{repo}/releases?per_page=100",
    )
    return [item for pagina in json.loads(saida) for item in pagina]


def preparar() -> tuple[str, Path]:
    """Seleciona uma versão livre e o prototype com maior número."""
    versoes = [
        int(m.group(1))
        for item in releases()
        if (m := PADRAO.fullmatch(item["tag_name"]))
    ]
    # Tags podem existir sem uma release associada.
    tags = comando("git", "ls-remote", "--tags", "origin")
    for linha in tags.splitlines():
        nome = linha.split("refs/tags/", 1)[-1].removesuffix("^{}")
        if achado := PADRAO.fullmatch(nome):
            versoes.append(int(achado.group(1)))
    pastas = [
        (int(m.group(1)), p)
        for p in (RAIZ / "prototypes").iterdir()
        if p.is_dir() and (m := PADRAO.fullmatch(p.name))
    ]
    if not pastas:
        raise RuntimeError("Nenhum prototype beta encontrado.")
    pasta = max(pastas, key=lambda item: item[0])[1]
    if not list(pasta.glob("*.exe")):
        raise RuntimeError(f"O prototype {pasta.name} não contém executável.")
    return f"beta-0.{max(versoes, default=0) + 1}", pasta


def compactar(pasta: Path, arquivo: Path) -> None:
    """Compacta o conteúdo completo do prototype."""
    with zipfile.ZipFile(arquivo, "w", zipfile.ZIP_DEFLATED) as zipado:
        for item in pasta.rglob("*"):
            if item.is_file():
                zipado.write(item, item.relative_to(pasta))


def publicar(tag: str, arquivo: Path) -> None:
    """Cria ou retoma a mesma release após falha parcial de publicação."""
    existentes = [r for r in releases() if r["tag_name"] == tag]
    if not existentes:
        comando(
            "gh",
            "release",
            "create",
            tag,
            str(arquivo),
            "--title",
            tag,
            "--notes",
            "Distribuição beta do MPEG-TS Converter.",
        )
    elif not any(a["name"] == arquivo.name for a in existentes[0]["assets"]):
        comando("gh", "release", "upload", tag, str(arquivo))
    dados = json.loads(
        comando("gh", "release", "view", tag, "--json", "tagName,isDraft,assets,url")
    )
    if dados["isDraft"] or not any(a["name"] == arquivo.name for a in dados["assets"]):
        raise RuntimeError("Release ou arquivo não confirmado no GitHub.")
    print(f"[release] Publicada: {dados['url']}", flush=True)


def principal() -> int:
    """Interrompe sem conexão e tenta publicar no máximo duas vezes."""
    try:
        print("[release] Verificando conexão e acesso ao repositório...", flush=True)
        comando("gh", "api", "repos/{owner}/{repo}")
        tag, pasta = preparar()
        print(f"[release] {tag}; prototype: {pasta.name}", flush=True)
        with tempfile.TemporaryDirectory() as temporario:
            arquivo = Path(temporario) / f"mpeg-ts-converter_{tag}.zip"
            compactar(pasta, arquivo)
            for tentativa in range(1, 3):
                try:
                    publicar(tag, arquivo)
                    return 0
                except (OSError, RuntimeError, subprocess.TimeoutExpired) as erro:
                    print(f"[release] Tentativa {tentativa} falhou: {erro}", flush=True)
        return 1
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as erro:
        print(f"[release] ERRO: {erro}", flush=True)
        return 1
    except KeyboardInterrupt:
        print("[release] Operação interrompida.", flush=True)
        return 130


if __name__ == "__main__":
    raise SystemExit(principal())
