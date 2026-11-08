"""Compila e versiona as distribuições do Projeto Broadcast."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
from scripts.distribuicao.ambiente import ambiente_compilacao

NOME = "mpeg-ts-converter"
def status(mensagem: str) -> None:
    """Escreve o progresso imediatamente no terminal."""
    print(f"[compilação] {mensagem}", flush=True)


def _montar_comando_pyinstaller(temporario: Path, console: bool = False) -> list[str]:
    """Monta a linha de comando do PyInstaller no diretório temporário informado."""
    return [
        sys.executable,
        "-u",
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--console" if console else "--windowed",
        "--noupx",
        "--name",
        NOME,
        "--distpath",
        str(temporario / "dist"),
        "--workpath",
        str(temporario / "work"),
        "--specpath",
        str(temporario),
        str(RAIZ / "main.py"),
    ]


def executar_pyinstaller(temporario: Path, executar, console: bool = False) -> Path:
    """Executa o PyInstaller em silêncio e mostra a saída somente em caso de falha."""
    status("Executando PyInstaller...")
    status("Fazendo a compilação...")
    try:
        executar(
            _montar_comando_pyinstaller(temporario, console),
            cwd=RAIZ,
            env=ambiente_compilacao(),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError as erro:
        _exibir_saida_falha(erro)
        raise
    pasta = temporario / "dist" / NOME
    if not (pasta / f"{NOME}.exe").is_file():
        raise RuntimeError("PyInstaller não gerou o executável esperado.")
    return pasta


def _exibir_saida_falha(erro: subprocess.CalledProcessError) -> None:
    """Mostra as últimas linhas capturadas do PyInstaller para diagnosticar a falha."""
    linhas = f"{erro.stdout or ''}\n{erro.stderr or ''}".strip().splitlines()
    status("Últimas linhas do PyInstaller:")
    for linha in linhas[-30:]:
        print(linha, flush=True)


def compilar(diretorio: Path, executar=subprocess.run,
             versao: str = "", console: bool = False) -> Path:
    """Gera uma distribuição sem consultar histórico de versões."""
    from scripts.distribuicao.versoes import validar_nome
    from scripts.distribuicao.manifesto import preparar_pacote

    validar_nome(versao)
    diretorio.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".compilacao-", dir=diretorio) as temp:
        pasta = executar_pyinstaller(Path(temp), executar, console)
        item = {"versao": versao}
        item.update(preparar_pacote(pasta, versao, diretorio.name))
        (pasta / "build.json").write_text(
            json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
        destino = diretorio / f"{NOME} {versao}"
        numero = 2
        while destino.exists():
            destino = diretorio / f"{NOME} {versao} ({numero})"
            numero += 1
        pasta.rename(destino)
    status(f"Compilação concluída: {destino}")
    return destino
