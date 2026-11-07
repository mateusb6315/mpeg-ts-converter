"""Compila e versiona as distribuições do Projeto Broadcast."""

import importlib.metadata
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOME = "Projeto Broadcast"
PADRAO_VERSAO = re.compile(r"beta 0\.([1-9][0-9]*)", re.IGNORECASE)


def status(mensagem: str) -> None:
    """Escreve o progresso imediatamente no terminal."""
    print(f"[compilação] {mensagem}", flush=True)


def proxima_versao(diretorio: Path, historico: list[dict]) -> int:
    """Retorna o primeiro número após a maior versão registrada ou existente."""
    nomes = [entrada.name for entrada in diretorio.iterdir()]
    nomes.extend(item["versao"] for item in historico)
    numeros = [
        int(achado.group(1))
        for nome in nomes
        if (achado := PADRAO_VERSAO.fullmatch(nome))
    ]
    return max(numeros, default=0) + 1


@contextmanager
def bloqueio(diretorio: Path):
    """Impede compilações simultâneas e libera o bloqueio ao encerrar o processo."""
    with (diretorio / ".compilacao.lock").open("a+b") as arquivo:
        if arquivo.tell() == 0:
            arquivo.write(b"0")
            arquivo.flush()
        arquivo.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(arquivo.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(arquivo.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as erro:
            raise RuntimeError(
                "Outra compilação está em andamento; aguarde e tente novamente."
            ) from erro
        try:
            yield
        finally:
            if os.name == "nt":
                arquivo.seek(0)
                msvcrt.locking(arquivo.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(arquivo.fileno(), fcntl.LOCK_UN)


def ler_historico(diretorio: Path) -> list[dict]:
    """Lê o histórico validado; arquivo ausente ou vazio equivale a nenhuma versão."""
    arquivo = diretorio / "historico.json"
    if not arquivo.exists():
        return []
    try:
        texto = arquivo.read_text(encoding="utf-8")
        if not texto.strip():
            return []
        dados = json.loads(texto)
        if not isinstance(dados, list):
            raise ValueError
        if any(
            not isinstance(item, dict)
            or not isinstance(item.get("versao"), str)
            or not PADRAO_VERSAO.fullmatch(item["versao"])
            for item in dados
        ):
            raise ValueError
        if len({item["versao"].lower() for item in dados}) != len(dados):
            raise ValueError
        return dados
    except (ValueError, UnicodeError) as erro:
        raise ValueError(
            f"O histórico {arquivo} está inválido; corrija-o antes de continuar."
        ) from erro


def gravar_json(arquivo: Path, dados) -> None:
    """Salva JSON por substituição atômica no mesmo diretório."""
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=arquivo.parent, delete=False, suffix=".tmp"
        ) as fluxo:
            temporario = Path(fluxo.name)
            json.dump(dados, fluxo, ensure_ascii=False, indent=2)
            fluxo.write("\n")
            fluxo.flush()
            os.fsync(fluxo.fileno())
        os.replace(temporario, arquivo)
    finally:
        if temporario is not None:
            temporario.unlink(missing_ok=True)


def reconciliar_historico(diretorio: Path, historico: list[dict]) -> None:
    """Recupera registros das pastas publicadas antes de uma interrupção."""
    conhecidas = {item["versao"].lower() for item in historico}
    recuperados = []
    for pasta in diretorio.iterdir():
        if not pasta.is_dir() or not PADRAO_VERSAO.fullmatch(pasta.name):
            continue
        if pasta.name.lower() in conhecidas or not (pasta / f"{NOME}.exe").is_file():
            continue
        metadados = pasta / "build.json"
        if not metadados.is_file():
            continue
        try:
            item = json.loads(metadados.read_text(encoding="utf-8"))
            if not isinstance(item, dict) or item.get("versao") != pasta.name:
                raise ValueError
        except (ValueError, UnicodeError) as erro:
            raise ValueError(
                f"Metadados inválidos em {metadados}; corrija-os."
            ) from erro
        recuperados.append(item)
    if recuperados:
        historico.extend(
            sorted(recuperados, key=lambda item: int(item["versao"].split(".")[-1]))
        )
        gravar_json(diretorio / "historico.json", historico)
        status(f"Histórico recuperado: {len(recuperados)} versão(ões).")


def _montar_comando_pyinstaller(temporario: Path) -> list[str]:
    """Monta a linha de comando do PyInstaller no diretório temporário informado."""
    return [
        sys.executable,
        "-u",
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
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


def executar_pyinstaller(temporario: Path, executar) -> Path:
    """Executa o PyInstaller em silêncio e mostra a saída somente em caso de falha."""
    status("Executando PyInstaller...")
    status("Fazendo a compilação...")
    try:
        executar(
            _montar_comando_pyinstaller(temporario),
            cwd=RAIZ,
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


def compilar(diretorio: Path, executar=subprocess.run) -> Path:
    """Gera uma versão e registra apenas a distribuição publicada com sucesso."""
    diretorio.mkdir(parents=True, exist_ok=True)
    with bloqueio(diretorio):
        status("Verificando histórico e versões existentes...")
        historico = ler_historico(diretorio)
        reconciliar_historico(diretorio, historico)
        versao = f"beta 0.{proxima_versao(diretorio, historico)}"
        destino = diretorio / versao
        status(f"Próxima versão: {versao}.")
        with tempfile.TemporaryDirectory(prefix=".compilacao-", dir=diretorio) as temp:
            pasta = executar_pyinstaller(Path(temp), executar)
            item = {
                "versao": versao,
                "data": datetime.now().astimezone().isoformat(),
                "caminho": versao,
                "python": sys.version.split()[0],
                "pyinstaller": importlib.metadata.version("pyinstaller"),
            }
            gravar_json(pasta / "build.json", item)
            status(f"Publicando {versao}...")
            if destino.exists():
                raise FileExistsError(
                    f"A pasta {destino} já existe; não será sobrescrita."
                )
            pasta.rename(destino)
        status("Registrando versão no histórico...")
        historico.append(item)
        gravar_json(diretorio / "historico.json", historico)
        status("Compilação concluída.")
        return destino


def principal() -> int:
    """Valida os pré-requisitos e executa a compilação no Windows."""
    status("Verificando pré-requisitos...")
    try:
        if os.name != "nt":
            raise RuntimeError(
                "A compilação do executável Windows deve ser feita no Windows."
            )
        faltantes = [
            nome
            for nome in ("PyInstaller", "PyQt6")
            if not importlib.util.find_spec(nome)
        ]
        if faltantes:
            raise RuntimeError(
                "Dependências ausentes: "
                + ", ".join(faltantes)
                + ". Instale requirements-build.txt."
            )
        compilar(RAIZ / "prototypes")
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as erro:
        status(f"ERRO: {erro}")
        return 1
    except KeyboardInterrupt:
        status("Compilação interrompida pelo usuário.")
        return 130


if __name__ == "__main__":
    raise SystemExit(principal())
