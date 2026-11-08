"""Interface compartilhada dos compiladores interativos e do CI."""
import argparse
import importlib.util
import os
import subprocess
from scripts.distribuicao.compilador import RAIZ, compilar, status
from scripts.distribuicao.versoes import validar_nome, validar_producao


def principal(canal: str) -> int:
    """Solicita versão manual quando ausente e compila sem publicar remotamente."""
    parser = argparse.ArgumentParser(description=f"Compilar {canal}")
    parser.add_argument("--versao")
    parser.add_argument("--console", action="store_true", help="Diagnóstico com console")
    args = parser.parse_args()
    try:
        exemplo = "0.0.3-beta1" if canal == "beta" else "0.0.3"
        versao = args.versao
        if versao is None:
            if os.environ.get("CI"):
                raise ValueError("No CI informe --versao explicitamente.")
            versao = input(f"Versão (recomendado {exemplo}): ")
        (validar_nome if canal == "beta" else validar_producao)(versao)
        if os.name != "nt":
            raise RuntimeError("Compile o executável Windows no Windows.")
        for nome in ("PyInstaller", "PyQt6"):
            if not importlib.util.find_spec(nome):
                raise RuntimeError(f"Instale requirements-build.txt: ausente {nome}")
        raiz = RAIZ / "prototypes" / "beta" if canal == "beta" else RAIZ / "dist" / canal
        compilar(raiz, versao=versao, console=args.console)
        return 0
    except (EOFError, OSError, ValueError, RuntimeError, subprocess.SubprocessError) as erro:
        status(f"ERRO: {erro}")
        return 1
    except KeyboardInterrupt:
        status("Compilação interrompida pelo usuário.")
        return 130
