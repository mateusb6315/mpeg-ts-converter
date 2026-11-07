---
name: compilacao-distribuicao-executavel
description: >-
  Use this skill when creating, refactoring, reviewing or testing a build,
  packaging and release-versioning script (PyInstaller or similar bundler) for
  any Python application (GUI or CLI). Covers terminal status messages,
  PyInstaller output suppression with failure tail diagnostics, atomic JSON
  history, crash reconciliation, file locking, sys.frozen runtime paths and
  fast unit tests for the build pipeline.
---

# Compilação, Empacotamento e Versionamento de Executáveis (Generalista)

Esta skill generaliza o pipeline de compilação de [scripts/compilar.py](file:///c:/Projetos/projeto%20broadcast/scripts/compilar.py) e sua suíte de testes [tests/test_compilar.py](file:///c:/Projetos/projeto%20broadcast/tests/test_compilar.py) para qualquer projeto Python (desktop GUI com PyQt/PySide/Tkinter ou CLI).

Consulte o modelo completo de código e de testes em [padroes_compilacao_e_testes.md](./references/padroes_compilacao_e_testes.md) ou gere a estrutura inicial com [gerar_script_compilacao.py](./scripts/gerar_script_compilacao.py).

---

## 1. Princípios do Pipeline de Compilação

1. **Saída limpa e previsível no terminal (`status`):**
   - Todas as mensagens de andamento passam por uma única função `status(mensagem: str)` com prefixo padronizado e `flush=True`:
     ```python
     def status(mensagem: str) -> None:
         print(f"[compilação] {mensagem}", flush=True)
     ```
   - Etapas anunciadas em ordem:
     1. `"Verificando pré-requisitos..."`
     2. `"Verificando histórico e versões existentes..."`
     3. `"Histórico recuperado: N versão(ões)."` *(somente se reconciliar)*
     4. `"Próxima versão: <versao>."`
     5. `"Executando PyInstaller..."`
     6. `"Fazendo a compilação..."`
     7. `"Publicando <versao>..."`
     8. `"Registrando versão no histórico..."`
     9. `"Compilação concluída."`
   - Códigos de saída em `principal()`: `0` (sucesso), `1` (`[compilação] ERRO: <detalhe>`), `130` (`KeyboardInterrupt` → `"Compilação interrompida pelo usuário."`).

2. **Supressão de ruído do PyInstaller e diagnóstico sob demanda:**
   - Execute o PyInstaller via função injetável (`executar=subprocess.run`) com `capture_output=True, text=True, encoding="utf-8", errors="replace", check=True`.
   - **No sucesso:** toda a saída verbosa do PyInstaller permanece oculta.
   - **Na falha (`subprocess.CalledProcessError`):** exiba apenas as últimas 30 linhas combinadas de `stdout` e `stderr` após `status("Últimas linhas do PyInstaller:")` e relance a exceção.

3. **Isolamento em diretório temporário e flags seguras do PyInstaller:**
   - Construa dentro de `tempfile.TemporaryDirectory(prefix=".compilacao-", dir=diretorio_destino)` (no mesmo disco/volume do destino para que o `rename` final seja atômico).
   - Passe `--distpath <temp>/dist`, `--workpath <temp>/work` e `--specpath <temp>` para nunca poluir a raiz do repositório com pastas `build/`, `dist/` ou `.spec`.
   - Use sempre `sys.executable, "-u", "-m", "PyInstaller"`, `--noconfirm`, `--clean`, `--onedir` (ou `--onefile` se exigido), `--windowed` (para GUI) e **`--noupx`** (evita corrupção de DLLs Qt/Python e falsos positivos de antivírus).
   - Verifique explicitamente se o executável esperado (`<pasta>/<NOME>.exe`) foi gerado antes de publicar.

---

## 2. Versionamento Monotônico, Atomicidade e Reconciliação

1. **Cálculo da próxima versão (`proxima_versao`):**
   - Combine os nomes das pastas existentes no diretório de saída **e** as versões registradas em `historico.json`.
   - Extraia o número inteiro via regex (ex.: `r"beta 0\.([1-9][0-9]*)"` ou prefixo do projeto) e retorne `max(numeros, default=0) + 1`.
   - **Regra crítica:** versões cujas pastas foram apagadas manualmente continuam no `historico.json` e **nunca são reutilizadas**; a numeração é inteira (`0.9` → `0.10`).

2. **Escrita atômica de JSON (`gravar_json`) e leitura estrita (`ler_historico`):**
   - Grave sempre em `NamedTemporaryFile(dir=arquivo.parent, delete=False, suffix=".tmp")`, execute `flush()` + `os.fsync()` e substitua com `os.replace(temporario, arquivo)`.
   - Em `ler_historico`: arquivo inexistente, vazio ou contendo apenas espaços em branco (`" \n\t"`) retorna `[]`. Se o JSON estiver corrompido, fora do formato de lista ou contiver versões duplicadas/inválidas, levante `ValueError` **sem sobrescrever** o arquivo.

3. **Publicação em duas fases e reconciliação pós-interrupção (`reconciliar_historico`):**
   - Fase 1: Grave `<pasta_temp>/build.json` com os metadados da versão (`versao`, `data` ISO-8601 com fuso, `caminho`, `python`, `pyinstaller`) e mova a pasta para o destino final (`pasta.rename(destino)`).
   - Fase 2: Adicione o item ao `historico.json` e salve atomicamente.
   - Se o processo cair entre a Fase 1 e a Fase 2, na execução seguinte `reconciliar_historico` encontra pastas com `<NOME>.exe` e `build.json` válido que ainda não constam em `historico.json`, ordena-as pelo número de versão e atualiza o `historico.json` antes de calcular a próxima versão.

4. **Bloqueio contra compilações simultâneas (`bloqueio`):**
   - Use um `@contextmanager` sobre `<diretorio>/.compilacao.lock` com `msvcrt.locking(..., msvcrt.LK_NBLCK, 1)` no Windows e `fcntl.flock(..., LOCK_EX | LOCK_NB)` em sistemas POSIX, levantando `RuntimeError` amigável se outra compilação estiver rodando.

---

## 3. Adaptações no Aplicativo para Executável Empacotado (`sys.frozen`)

Quando empacotado pelo PyInstaller (`getattr(sys, "frozen", False)` é `True`):
- **Logs e dados graváveis:** Não escreva no diretório de trabalho atual (o app pode estar em `C:\Program Files`). Grave em `Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / NOME_APP`.
- **Diretório base do executável:** Use `Path(sys.executable).resolve().parent` quando `sys.frozen` for `True`, e `Path(__file__).resolve().parent` em desenvolvimento.

---

## 4. Suíte de Testes de Compilação (`tests/test_compilar.py`)

Os testes do script de compilação **nunca** executam o PyInstaller real; eles injetam um dublê `executar=_compilador_falso` que lê `--distpath` da lista de comando e cria o `.exe` falso em `tmp_path`.

Cobertura mínima obrigatória (15 cenários):
1. **Numeração inteira:** `beta 0.2` e `beta 0.9` no disco → próxima é `10` (`beta 0.10`).
2. **Desativação do UPX:** comando enviado ao PyInstaller contém `"--noupx"`.
3. **Supressão no sucesso:** `capture_output=True`, exibe `"Fazendo a compilação..."` e **não** vaza o `stdout` do PyInstaller no terminal (`capsys`).
4. **Diagnóstico na falha:** quando `executar` levanta `CalledProcessError`, as últimas linhas da saída do PyInstaller aparecem no terminal.
5. **Compilação sequencial:** duas chamadas seguidas criam `beta 0.1` e `beta 0.2`, registram ambas em `historico.json` e emitem mensagens de status.
6. **Histórico vazio (`""`):** gera primeira versão `beta 0.1`.
7. **Histórico só com espaços (`" \n\t\n"`):** gera primeira versão `beta 0.1`.
8. **Histórico inexistente:** gera primeira versão `beta 0.1`.
9. **Versão apagada não reutilizada:** `historico.json` com `beta 0.12` (sem pasta) → gera `beta 0.13`.
10. **Falha atômica:** erro no PyInstaller não cria pasta final, não cria `historico.json` e não consome o número `beta 0.1`.
11. **Histórico corrompido:** levanta `ValueError` e preserva o conteúdo inválido intacto no disco.
12. **Reconciliação de publicação interrompida:** pasta `beta 0.4` com `.exe` e `build.json` (ausente do `historico.json`) é recuperada antes de publicar `beta 0.5`.
13. **Executável ausente pós-build:** se o PyInstaller terminar com código 0 mas não gerar `<NOME>.exe`, levanta `RuntimeError` e não publica a pasta.
14. **Bloqueio de concorrência:** entrar em `bloqueio(tmp_path)` duas vezes simultâneas levanta `RuntimeError("... em andamento ...")` e libera ao sair do bloco `with`.
15. **Caminho de log em modo `sys.frozen`:** com `sys.frozen = True` e `LOCALAPPDATA=tmp_path`, o log aponta para `<tmp_path>/<NOME>/<arquivo>.log`.

---

## 5. Passo a Passo para Criar ou Auditar em Outro Projeto

1. Gere o esqueleto inicial executando [gerar_script_compilacao.py](./scripts/gerar_script_compilacao.py):
   ```powershell
   python .agents/skills/compilacao-distribuicao-executavel/scripts/gerar_script_compilacao.py --nome "Meu App" --entrada main.py --destino releases
   ```
2. Ajuste os módulos obrigatórios na verificação de pré-requisitos (`("PyInstaller", ...)`).
3. Execute a suíte de testes de compilação:
   ```powershell
   python -m pytest tests/test_compilar.py -v
   ```
