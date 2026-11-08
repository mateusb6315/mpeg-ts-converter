"""Compilador beta com versão livre informada manualmente."""
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.distribuicao.cli import principal

if __name__ == "__main__":
    raise SystemExit(principal("beta"))
