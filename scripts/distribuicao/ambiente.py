"""Ambiente mínimo de build para evitar DLLs de aplicativos no PATH."""
import os
from pathlib import Path
import sys


def ambiente_compilacao() -> dict[str, str]:
    """Preserva variáveis do sistema, isolando caminhos Python e Qt."""
    ambiente = os.environ.copy()
    for nome in ("PYTHONPATH", "PYTHONHOME", "QT_PLUGIN_PATH", "QML2_IMPORT_PATH",
                 "QT_QPA_PLATFORM_PLUGIN_PATH"):
        ambiente.pop(nome, None)
    windows = Path(ambiente.get("SystemRoot", r"C:\Windows"))
    qt = Path(sys.prefix) / "Lib/site-packages/PyQt6/Qt6/bin"
    caminhos = [qt, Path(sys.executable).parent, Path(sys.base_prefix),
                windows / "System32", windows]
    ambiente["PATH"] = os.pathsep.join(str(p) for p in caminhos)
    return ambiente
