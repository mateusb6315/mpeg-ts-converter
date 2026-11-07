"""Auditoria estática genérica (AST) de camadas, tamanhos e documentação.

Uso: python auditar_codigo.py [raiz_do_projeto] [nome_a_ignorar ...]
Ajuste o dicionário CONFIG para o projeto. Sem dependências externas.
"""

import ast
from pathlib import Path
import sys

CONFIG = {
    "limite_linhas_modulo": 250,
    "limite_linhas_funcao": 30,
    "limite_parametros": 4,
    "limite_colunas": 100,
    # camada -> módulos de topo que ela NÃO pode importar
    "proibicoes": {
        "config": {"utilitarios", "modelos", "servicos", "visoes", "controladores"},
        "utilitarios": {"modelos", "servicos", "visoes", "controladores"},
        "modelos": {"servicos", "visoes", "controladores"},
        "servicos": {"visoes", "controladores"},
        "visoes": {"modelos", "controladores", "servicos"},
    },
    # camadas que não podem importar o toolkit de UI
    "camadas_sem_ui": {"config", "utilitarios", "modelos", "servicos"},
    "toolkits_ui": {"PyQt6", "PySide6", "tkinter"},
    "ignorar": {"tests", ".agents", ".venv", "venv", "__pycache__"},
}


def listar_arquivos(raiz: Path) -> list[Path]:
    """Lista os .py auditáveis (exclui testes, ambientes e __init__)."""
    return [
        p for p in raiz.rglob("*.py")
        if p.name != "__init__.py"
        and not (set(p.relative_to(raiz).parts) & CONFIG["ignorar"])
    ]


def contar_linhas_funcao(no: ast.FunctionDef, linhas: list[str]) -> int:
    """Conta linhas de código da função sem docstring, brancos e comentários."""
    inicio = no.lineno + 1
    if (no.body and isinstance(no.body[0], ast.Expr)
            and isinstance(no.body[0].value, ast.Constant)
            and isinstance(no.body[0].value.value, str)):
        inicio = (no.body[0].end_lineno or no.lineno) + 1
    trecho = linhas[inicio - 1:(no.end_lineno or no.lineno)]
    return sum(1 for t in trecho if t.strip() and not t.strip().startswith("#"))


def auditar_imports(no: ast.AST, camada: str, nome: str) -> list[str]:
    """Verifica imports proibidos por camada."""
    if not isinstance(no, (ast.Import, ast.ImportFrom)):
        return []
    modulo = (no.module if isinstance(no, ast.ImportFrom) else no.names[0].name) or ""
    topo = modulo.split(".")[0]
    erros = []
    if camada in CONFIG["camadas_sem_ui"] and topo in CONFIG["toolkits_ui"]:
        erros.append(f"{nome}: camada '{camada}' não pode importar UI ({topo})")
    if topo in CONFIG["proibicoes"].get(camada, set()):
        erros.append(f"{nome}: camada '{camada}' não pode importar '{topo}'")
    return erros


def auditar_funcao(no: ast.FunctionDef, linhas: list[str], nome: str) -> list[str]:
    """Verifica tamanho, parâmetros e docstring de uma função."""
    erros = []
    params = len(no.args.args) + len(no.args.kwonlyargs)
    if params > CONFIG["limite_parametros"]:
        erros.append(f"{nome}: '{no.name}' tem {params} parâmetros")
    total = contar_linhas_funcao(no, linhas)
    if total > CONFIG["limite_linhas_funcao"]:
        erros.append(f"{nome}: '{no.name}' tem {total} linhas")
    if not no.name.startswith("_") and not ast.get_docstring(no):
        erros.append(f"{nome}: função pública '{no.name}' sem docstring")
    return erros


def auditar_arquivo(raiz: Path, caminho: Path) -> list[str]:
    """Executa todas as verificações em um arquivo."""
    rel = caminho.relative_to(raiz)
    nome = rel.as_posix()
    camada = rel.parts[0] if len(rel.parts) > 1 else "raiz"
    texto = caminho.read_text(encoding="utf-8")
    linhas = texto.splitlines()
    erros = []
    if len(linhas) > CONFIG["limite_linhas_modulo"] + 5:
        erros.append(f"{nome}: {len(linhas)} linhas (máx. ~{CONFIG['limite_linhas_modulo']})")
    erros += [f"{nome}:{i}: linha > {CONFIG['limite_colunas']} colunas"
              for i, l in enumerate(linhas, 1) if len(l) > CONFIG["limite_colunas"]]
    arvore = ast.parse(texto)
    if not ast.get_docstring(arvore):
        erros.append(f"{nome}: módulo sem docstring")
    for no in ast.walk(arvore):
        erros += auditar_imports(no, camada, nome)
        if isinstance(no, ast.FunctionDef):
            erros += auditar_funcao(no, linhas, nome)
    return erros


def principal() -> int:
    """Audita o projeto e imprime o resultado."""
    raiz = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    CONFIG["ignorar"] |= set(sys.argv[2:])  # nomes extras (arquivos/pastas) a ignorar
    arquivos = listar_arquivos(raiz)
    erros = [e for a in arquivos for e in auditar_arquivo(raiz, a)]
    if erros:
        print("FALHA NA AUDITORIA:", *erros, sep="\n - ")
        return 1
    print(f"OK: {len(arquivos)} módulos auditados, 0 violações.")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
