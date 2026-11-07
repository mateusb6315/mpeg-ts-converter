# Referência de Código: Script de Compilação e Testes (`compilar.py` + `test_compilar.py`)

## 1. Parâmetros Customizáveis para Qualquer Projeto

Ao adaptar o script de compilação para outro projeto, configure as constantes de topo:

```python
RAIZ = Path(__file__).resolve().parent.parent
NOME = "NomeDoAplicativo"              # Nome do diretório e do .exe gerado
PONTO_ENTRADA = RAIZ / "main.py"       # Script principal
PASTA_SAIDA = RAIZ / "prototypes"      # Ou "releases", "distribuicoes"
PREFIXO_VERSAO = "beta 0."             # Ou "v1.", "rc 0."
PADRAO_VERSAO = re.compile(r"beta 0\.([1-9][0-9]*)", re.IGNORECASE)
MODULOS_OBRIGATORIOS = ("PyInstaller", "PyQt6")  # Dependências de build/runtime
MODO_JANELA = "--windowed"             # Use "--console" para aplicações CLI
```

---

## 2. Padrões Essenciais do `scripts/compilar.py`

### 2.1 Mensagens de Status e Diagnóstico de Falha do PyInstaller
```python
def status(mensagem: str) -> None:
    """Escreve o progresso imediatamente no terminal."""
    print(f"[compilação] {mensagem}", flush=True)


def _exibir_saida_falha(erro: subprocess.CalledProcessError) -> None:
    """Mostra as últimas linhas capturadas do PyInstaller para diagnosticar a falha."""
    linhas = f"{erro.stdout or ''}\n{erro.stderr or ''}".strip().splitlines()
    status("Últimas linhas do PyInstaller:")
    for linha in linhas[-30:]:
        print(linha, flush=True)
```

### 2.2 Execução Silenciosa e Isolada do PyInstaller
```python
def _montar_comando_pyinstaller(temporario: Path) -> list[str]:
    """Monta a linha de comando do PyInstaller isolada no diretório temporário."""
    return [
        sys.executable, "-u", "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onedir", MODO_JANELA, "--noupx",
        "--name", NOME,
        "--distpath", str(temporario / "dist"),
        "--workpath", str(temporario / "work"),
        "--specpath", str(temporario),
        str(PONTO_ENTRADA),
    ]


def executar_pyinstaller(temporario: Path, executar) -> Path:
    """Executa o PyInstaller em silêncio e mostra a saída somente em caso de falha."""
    status("Executando PyInstaller...")
    status("Fazendo a compilação...")
    try:
        executar(
            _montar_comando_pyinstaller(temporario),
            cwd=RAIZ, check=True, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
    except subprocess.CalledProcessError as erro:
        _exibir_saida_falha(erro)
        raise
    pasta = temporario / "dist" / NOME
    if not (pasta / f"{NOME}.exe").is_file():
        raise RuntimeError("PyInstaller não gerou o executável esperado.")
    return pasta
```

### 2.3 Escrita Atômica de JSON e Bloqueio de Processo
```python
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
```

### 2.4 Caminho de Log Seguro para Executável (`main.py`)
```python
def _obter_caminho_log() -> Path:
    """Mantém o log da distribuição na área de dados gravável do usuário."""
    if not getattr(sys, "frozen", False):
        return CAMINHO_ARQUIVO_LOG
    base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    diretorio = base / NOME_APLICACAO
    diretorio.mkdir(parents=True, exist_ok=True)
    return diretorio / CAMINHO_ARQUIVO_LOG.name
```

---

## 3. Modelo de Testes de Compilação (`tests/test_compilar.py`)

```python
@pytest.fixture(autouse=True)
def _versao_pyinstaller_falsa(monkeypatch):
    """Os testes simulados não exigem a instalação do PyInstaller."""
    monkeypatch.setattr("scripts.compilar.importlib.metadata.version", lambda _n: "teste")


def _compilador_falso(comando, **_kwargs):
    """Cria uma distribuição falsa no --distpath solicitado ao PyInstaller."""
    destino = Path(comando[comando.index("--distpath") + 1])
    pasta = destino / NOME
    pasta.mkdir(parents=True)
    (pasta / f"{NOME}.exe").write_bytes(b"MZ")
```

Com esse dublê, todos os 15 testes de versionamento, supressão de saída, diagnóstico de erro, reconciliação de `build.json` e bloqueio `.compilacao.lock` rodam em menos de `0.2s` sem invocar o PyInstaller real.
