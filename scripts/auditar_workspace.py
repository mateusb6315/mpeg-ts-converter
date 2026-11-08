"""Auditoria descoberta automaticamente para incluir novos módulos de camadas."""
import importlib.util
from pathlib import Path


def principal() -> int:
    """Aplica regras locais sem alterar a skill protegida."""
    raiz = Path(__file__).resolve().parents[1]
    script = raiz / ".agents/skills/arquitetura-mvc-pyqt6/scripts/validar_arquitetura.py"
    spec = importlib.util.spec_from_file_location("auditor", script)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    erros = []
    for camada in ("config", "utilitarios", "modelos", "servicos", "visoes", "controladores"):
        for arquivo in (raiz / camada).rglob("*.py"):
            if arquivo.name != "__init__.py":
                erros.extend(modulo.auditar_arquivo(raiz, arquivo.relative_to(raiz).as_posix()))
    for erro in erros:
        print(erro)
    print(f"Auditoria descoberta: {len(erros)} violações.")
    return int(bool(erros))


if __name__ == "__main__":
    raise SystemExit(principal())
