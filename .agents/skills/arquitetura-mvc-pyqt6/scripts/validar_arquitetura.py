"""Script de auditoria estática (AST) para validar as regras arquiteturais do PROMPT.md."""

import ast
from pathlib import Path
import unicodedata

CAMADAS_SEM_PYQT = {"config", "utilitarios", "modelos", "servicos"}
IMPORTS_PROIBIDOS_POR_CAMADA = {
    "config": {"utilitarios", "modelos", "servicos", "visoes", "controladores"},
    "utilitarios": {"modelos", "servicos", "visoes", "controladores"},
    "modelos": {"servicos", "visoes", "controladores"},
    "servicos": {"visoes", "controladores"},
    "visoes": {"modelos", "controladores", "servicos"},
}
ARQUIVOS_AUDITADOS = (
    "main.py",
    "config/configuracoes.py",
    "config/interface.py",
    "utilitarios/formatacao.py",
    "modelos/conversao.py",
    "servicos/arquivo_servico.py",
    "servicos/conversao_servico.py",
    "servicos/nvenc_config_servico.py",
    "visoes/tema_visao.py",
    "visoes/estilos_visao.py",
    "visoes/componentes_visao.py",
    "visoes/janela_principal.py",
    "controladores/conversao_trabalhador.py",
    "controladores/conversao_controlador.py",
    "controladores/verificador_nvenc_trabalhador.py",
)


def possui_acento_ou_cedilha(identificador: str) -> bool:
    """Detecta se um identificador Python contém caracteres acentuados ou cedilha."""
    normalizado = unicodedata.normalize("NFD", identificador)
    return any(unicodedata.category(c) == "Mn" for c in normalizado)


def contar_linhas_codigo_funcao(no_funcao: ast.FunctionDef, linhas_arquivo: list[str]) -> int:
    """Conta as linhas de código de uma função ignorando docstring e linhas em branco."""
    inicio = no_funcao.lineno
    fim = no_funcao.end_lineno or inicio
    inicio_corpo = inicio + 1
    if (
        no_funcao.body
        and isinstance(no_funcao.body[0], ast.Expr)
        and isinstance(no_funcao.body[0].value, ast.Constant)
        and isinstance(no_funcao.body[0].value.value, str)
    ):
        inicio_corpo = (no_funcao.body[0].end_lineno or inicio) + 1
    trecho = linhas_arquivo[inicio_corpo - 1 : fim]
    return sum(
        1 for linha in trecho if linha.strip() and not linha.strip().startswith("#")
    )


def auditar_arquivo(raiz: Path, caminho_relativo: str) -> list[str]:
    """Audita um arquivo Python em busca de violações de tamanho, imports e docstrings."""
    erros: list[str] = []
    caminho = raiz / caminho_relativo
    texto = caminho.read_text(encoding="utf-8")
    linhas = texto.splitlines()
    camada = caminho_relativo.split("/")[0] if "/" in caminho_relativo else "raiz"

    if len(linhas) > 255:
        erros.append(f"{caminho_relativo}: módulo com {len(linhas)} linhas (máximo ~250)")

    for indice, linha in enumerate(linhas, start=1):
        if len(linha) > 100:
            erros.append(f"{caminho_relativo}:{indice}: linha com {len(linha)} colunas (>100)")

    arvore = ast.parse(texto, filename=caminho_relativo)
    if not ast.get_docstring(arvore):
        erros.append(f"{caminho_relativo}: módulo sem docstring")

    for no in ast.walk(arvore):
        if isinstance(no, (ast.Import, ast.ImportFrom)):
            modulo = (
                no.module
                if isinstance(no, ast.ImportFrom)
                else no.names[0].name
            ) or ""
            topo = modulo.split(".")[0]
            if camada in CAMADAS_SEM_PYQT and topo == "PyQt6":
                erros.append(f"{caminho_relativo}: import proibido de PyQt6 na camada {camada}")
            proibidos = IMPORTS_PROIBIDOS_POR_CAMADA.get(camada, set())
            if topo in proibidos:
                erros.append(
                    f"{caminho_relativo}: camada '{camada}' não pode importar '{topo}'"
                )
        elif isinstance(no, ast.FunctionDef):
            if possui_acento_ou_cedilha(no.name):
                erros.append(f"{caminho_relativo}: função '{no.name}' possui acento/cedilha")
            total_params = len(no.args.args) + len(no.args.kwonlyargs)
            if total_params > 4:
                erros.append(
                    f"{caminho_relativo}: função '{no.name}' tem {total_params} parâmetros (>4)"
                )
            qtd_linhas = contar_linhas_codigo_funcao(no, linhas)
            if qtd_linhas > 30:
                erros.append(
                    f"{caminho_relativo}: função '{no.name}' tem {qtd_linhas} linhas (>30)"
                )
            if not no.name.startswith("_") and not ast.get_docstring(no):
                erros.append(f"{caminho_relativo}: função pública '{no.name}' sem docstring")
    return erros


def executar_auditoria() -> int:
    """Executa a auditoria em todos os módulos da arquitetura e imprime o resultado."""
    raiz = Path(__file__).resolve().parents[4]
    todos_erros: list[str] = []
    for arquivo in ARQUIVOS_AUDITADOS:
        todos_erros.extend(auditar_arquivo(raiz, arquivo))
    if todos_erros:
        print("FALHA NA AUDITORIA ARQUITETURAL:")
        for erro in todos_erros:
            print(f" - {erro}")
        return 1
    print(f"OK: {len(ARQUIVOS_AUDITADOS)} módulos auditados com 0 violações arquiteturais.")
    return 0


if __name__ == "__main__":
    raise SystemExit(executar_auditoria())
