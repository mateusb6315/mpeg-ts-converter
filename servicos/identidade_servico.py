"""Identidade exibida conforme manifesto da distribuição executada."""
import json
from pathlib import Path
import sys


def obter_titulo_aplicacao() -> str:
    """Lê versão do pacote, mantendo identificação útil no código-fonte."""
    versao = "0.0.3-beta1"
    if getattr(sys, "frozen", False):
        try:
            arquivo = Path(sys.executable).parent / "build.json"
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
            versao = str(dados["versao"])
        except (OSError, ValueError, KeyError, TypeError):
            versao = "versão indisponível"
    return f"MPEG-TS Converter {versao} (HEVC 60p BWDIF)"
