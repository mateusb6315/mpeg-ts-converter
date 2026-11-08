"""Verifica artefato explícito; publicação remota exige --publicar."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.distribuicao.manifesto import hash_arquivo
from scripts.distribuicao.compilador import NOME

RAIZ = Path(__file__).resolve().parents[1]


def comando(*args: str) -> str:
    """Executa CLI com prazo e falha explícita."""
    return subprocess.check_output(args, cwd=RAIZ, text=True, encoding="utf-8", timeout=120)


def verificar(pasta: Path) -> dict:
    """Confere esquema, caminhos, hashes, tamanhos e recursos obrigatórios."""
    dados = json.loads((pasta / "build.json").read_text(encoding="utf-8"))
    if not isinstance(dados, dict):
        raise ValueError("Manifesto deve ser objeto JSON.")
    versao = dados.get("versao")
    nome_esperado = f"{NOME} {versao}" if isinstance(versao, str) else ""
    if dados.get("esquema") != 1 or pasta.name != nome_esperado:
        raise ValueError("Manifesto incompatível com o artefato.")
    arquivos = dados.get("arquivos", {})
    if not isinstance(arquivos, dict):
        raise ValueError("Inventário deve ser objeto JSON.")
    obrigatorios = {f"{NOME}.exe", "LICENSE", "README.md"}
    if not obrigatorios <= arquivos.keys():
        raise ValueError("Recursos obrigatórios ausentes do manifesto.")
    for nome, item in arquivos.items():
        arquivo = (pasta / nome).resolve()
        if not arquivo.is_relative_to(pasta.resolve()) or not arquivo.is_file():
            raise ValueError(f"Caminho inválido: {nome}")
        if arquivo.stat().st_size != item["bytes"] or hash_arquivo(arquivo) != item["sha256"]:
            raise ValueError(f"Integridade divergente: {nome}")
    presentes = {p.relative_to(pasta).as_posix() for p in pasta.rglob("*") if p.is_file()}
    if presentes != set(arquivos) | {"build.json"}:
        raise ValueError("Pacote contém arquivos fora do manifesto.")
    return dados


def compactar(pasta: Path, arquivo: Path) -> None:
    """Cria ZIP exclusivo com conteúdo verificado."""
    verificar(pasta)
    with zipfile.ZipFile(arquivo, "x", zipfile.ZIP_DEFLATED) as zipado:
        for item in sorted(pasta.rglob("*")):
            if item.is_file():
                zipado.write(item, item.relative_to(pasta))


def publicar(pasta: Path, notas: Path) -> None:
    """Prepara rascunho vinculado ao commit, recusando colisões remotas."""
    dados = verificar(pasta)
    if dados.get("git_sujo") or not dados.get("commit"):
        raise ValueError("Publicação exige artefato de commit limpo identificado.")
    tag = dados["versao"]
    comando("git", "check-ref-format", "refs/tags/" + tag)
    if comando("git", "ls-remote", "--tags", "origin", "refs/tags/" + tag).strip():
        raise ValueError("Tag já existe; conferir a release antes de qualquer retomada.")
    with tempfile.TemporaryDirectory() as temporario:
        arquivo = Path(temporario) / f"mpeg-ts-converter_{tag}.zip"
        compactar(pasta, arquivo)
        checksum = arquivo.with_suffix(".zip.sha256")
        checksum.write_text(hash_arquivo(arquivo) + "  " + arquivo.name + "\n")
        args = ["gh", "release", "create", tag, str(arquivo), str(checksum),
                "--target", dados["commit"], "--title", tag, "--draft",
                "--notes-file", str(notas.resolve())]
        if dados["canal"] == "beta":
            args.append("--prerelease")
        comando(*args)


def principal() -> int:
    """Verifica localmente por padrão; nunca escolhe versão ou pasta implicitamente."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artefato", type=Path, required=True)
    parser.add_argument("--publicar", action="store_true")
    parser.add_argument("--notas", type=Path)
    args = parser.parse_args()
    try:
        dados = verificar(args.artefato)
        print(f"Artefato verificado: {dados['versao']} ({dados['commit']})")
        if args.publicar:
            if not args.notas or not args.notas.is_file():
                raise ValueError("Publicação exige --notas apontando para um arquivo.")
            publicar(args.artefato, args.notas)
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as erro:
        print(f"[release] ERRO: {erro}")
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(principal())
