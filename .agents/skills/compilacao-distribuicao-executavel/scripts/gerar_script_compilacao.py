"""Gera scripts/compilar.py, requirements-build.txt e tests/test_compilar.py para um projeto.

Uso:
  python gerar_script_compilacao.py --nome "Meu App" [--entrada main.py] [--destino prototypes]
Não sobrescreve arquivos existentes sem a flag --forcar.
"""

import argparse
from pathlib import Path
import sys


def _parsear_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gerador de pipeline de compilação PyInstaller.")
    parser.add_argument("--raiz", type=Path, default=Path.cwd(), help="Raiz do projeto alvo.")
    parser.add_argument("--nome", required=True, help="Nome do aplicativo e do executável.")
    parser.add_argument("--entrada", default="main.py", help="Arquivo de entrada principal.")
    parser.add_argument("--destino", default="prototypes", help="Pasta de saída das versões.")
    parser.add_argument("--console", action="store_true", help="Usar --console em vez de --windowed.")
    parser.add_argument("--forcar", action="store_true", help="Sobrescrever arquivos existentes.")
    return parser.parse_args()


def _gerar_requirements_build() -> str:
    return "-r requirements.txt\npyinstaller>=6.22,<7\n"


def _adaptar_template(caminho_origem: Path, args: argparse.Namespace) -> str:
    texto = caminho_origem.read_text(encoding="utf-8")
    texto = texto.replace('"Projeto Broadcast"', f'"{args.nome}"')
    texto = texto.replace("Projeto Broadcast.exe", f"{args.nome}.exe")
    texto = texto.replace('"main.py"', f'"{args.entrada}"')
    texto = texto.replace('"prototypes"', f'"{args.destino}"')
    if args.console:
        texto = texto.replace('"--windowed"', '"--console"')
    return texto


def _escrever_se_permitido(destino: Path, conteudo: str, forcar: bool) -> bool:
    if destino.exists() and not forcar:
        print(f"Ignorado (já existe): {destino}")
        return False
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(conteudo, encoding="utf-8")
    print(f"Gerado: {destino}")
    return True


def principal() -> int:
    """Ponto de entrada do gerador de scripts e testes de compilação."""
    args = _parsear_argumentos()
    raiz_ref = Path(__file__).resolve().parents[4]
    compilar_ref = raiz_ref / "scripts" / "compilar.py"
    teste_ref = raiz_ref / "tests" / "test_compilar.py"
    if not compilar_ref.is_file() or not teste_ref.is_file():
        print("Arquivos de referência scripts/compilar.py ou tests/test_compilar.py ausentes.")
        return 1

    _escrever_se_permitido(
        args.raiz / "requirements-build.txt", _gerar_requirements_build(), args.forcar
    )
    _escrever_se_permitido(
        args.raiz / "scripts" / "compilar.py",
        _adaptar_template(compilar_ref, args),
        args.forcar,
    )
    _escrever_se_permitido(
        args.raiz / "tests" / "test_compilar.py",
        _adaptar_template(teste_ref, args),
        args.forcar,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
