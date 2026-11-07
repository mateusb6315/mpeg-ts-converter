"""Gera o esqueleto de um arquivo de teste pytest para um módulo.

Uso: python novo_teste.py <modulo.importavel> <funcao1> [funcao2 ...]
Exemplo: python novo_teste.py utilitarios.formatacao formatar_tamanho
Cria tests/test_<modulo>.py (não sobrescreve arquivo existente).
"""

from pathlib import Path
import sys

MODELO_ARQUIVO = '"""Testes de unidade de {modulo}."""\n\nfrom {modulo} import {importacoes}\n'
MODELO_TESTE = '''

def test_{funcao}_caso_tipico_retorna_resultado_esperado() -> None:
    """Cobre o caminho feliz de {funcao}."""
    raise NotImplementedError("Preencher Arrange-Act-Assert")


def test_{funcao}_entrada_limite_ou_invalida_nao_levanta_excecao() -> None:
    """Cobre limites (vazio, None, negativo, unicode) de {funcao}."""
    raise NotImplementedError("Preencher limites")
'''


def gerar(modulo: str, funcoes: list[str]) -> str:
    """Monta o conteúdo do arquivo de teste."""
    conteudo = MODELO_ARQUIVO.format(modulo=modulo, importacoes=", ".join(funcoes))
    for funcao in funcoes:
        conteudo += MODELO_TESTE.format(funcao=funcao)
    return conteudo


def principal() -> int:
    """Cria o arquivo de teste e informa o caminho."""
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    modulo, funcoes = sys.argv[1], sys.argv[2:]
    destino = Path("tests") / f"test_{modulo.split('.')[-1]}.py"
    if destino.exists():
        print(f"Já existe: {destino}")
        return 1
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(gerar(modulo, funcoes), encoding="utf-8")
    print(f"Criado: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
