"""Entrada de produção; API legada de compilação preservada para integração."""
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.distribuicao.compilador import (compilar, proxima_versao, bloqueio,
                                           ler_historico, gravar_json)
from scripts.distribuicao.cli import principal

if __name__ == "__main__":
    raise SystemExit(principal("producao"))
