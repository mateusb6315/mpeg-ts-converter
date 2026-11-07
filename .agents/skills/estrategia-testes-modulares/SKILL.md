---
name: estrategia-testes-modulares
description: >-
  Use this skill when creating, organizing or maintaining automated tests for
  any project: modular/unit tests, integration and headless GUI tests, contract
  and architecture tests, regression, stress/load/soak and robustness tests,
  doubles and fixtures, naming, coverage priorities and the test-run routine
  before delivering changes.
---

# Estratégia de Testes Modulares (generalista)

Exemplos detalhados: [catalogo_testes.md](./references/catalogo_testes.md). Gerador de
esqueleto: [novo_teste.py](./scripts/novo_teste.py).

## 1. Pirâmide e organização

| Nível | Alvo | Velocidade | Dependências |
|---|---|---|---|
| **Unitário** | função/classe pura (`modelos`, `utilitarios`) | ms | nenhuma |
| **Modular** | um serviço/controlador isolado com dublês | ms | dublês injetados |
| **Integração** | várias camadas juntas (trabalhador + controlador + view offscreen) | <1 s | UI offscreen, `tmp_path` |
| **Contrato/Arquitetura** | regras estruturais (imports, tamanhos, docstrings) | s | AST |
| **Regressão** | bug já corrigido não volta | ms | caso mínimo reproduzível |
| **Robustez/Fuzz** | entradas hostis (vazio, unicode, enormes, `None`, NaN) | s | geradores simples |
| **Estresse/Carga/Soak** | volume, repetição, concorrência, tempo longo | s–min | marcador `slow` |
| **Manual/E2E** | roteiro curto documentado no README | — | ambiente real |

Estrutura: `tests/test_<modulo>.py` espelhando as camadas; integração em
`test_integracao_*.py`; estresse em `test_estresse_*.py` com `@pytest.mark.slow`.

## 2. Regras de ouro

- Testes **não** exigem rede, GPU, binários externos nem servidor gráfico real: injete
  dublês (`lambda`, `monkeypatch`, classes falsas) — a arquitetura com DI existe para isso.
- Nome descreve comportamento: `test_<unidade>_<condicao>_<resultado>` (no idioma do projeto).
- Um conceito por teste; Arrange–Act–Assert; mensagens de falha úteis.
- Use `tmp_path` para arquivos; **nunca** escreva em pastas reais do usuário.
- Teste **caminhos de decisão**, não linhas: cada ramo (sim/não/cancelou/inválido/vazio).
- Determinismo: sem `sleep` real; injete relógio/gerador aleatório com *seed*.
- Efeitos globais (variáveis de ambiente, registro) → `monkeypatch` e **stub** da
  persistência (ex.: substituir `_persistir_*` antes de testar).
- Cada bug corrigido ganha um teste de regressão antes/junto do conserto.

## 3. O que cobrir por camada

- **Modelo/utilitários:** valores típicos, limites, vazios, negativos, NaN/inf, unicode,
  idempotência, monotonicidade (ex.: progresso nunca regride), parsers com linhas reais
  e lixo.
- **Serviços:** caminhos felizes com arquivos temporários; ausência do recurso externo
  (fallback); códigos de erro; timeouts (com dublê de `subprocess`).
- **Controladores:** cada transição de estado; cancelamento; dupla ação (soltar enquanto
  ocupado); fluxo condicional completo.
- **Visão (offscreen):** textos/títulos/tamanho fixo, sinais emitidos, cursor/flags,
  eventos sintéticos (`QMouseEvent`) e diálogos substituídos por `lambda`.
- **Threads:** executar o `executar()` do trabalhador **síncrono** para sinais; usar
  `QSignalSpy`/`processEvents` só quando o teste for realmente de fila.

## 4. Estresse, carga e robustez

Marque como lentos e mantenha fora do ciclo rápido (`pytest -m "not slow"`).
- **Volume:** parser/formatador com 10⁵–10⁶ entradas; medir tempo com margem generosa.
- **Repetição (soak):** 1.000 ciclos de iniciar → concluir → reiniciar da janela; checar
  que o estado final é idêntico ao inicial e que não há threads/objetos pendentes.
- **Concorrência:** várias threads emitindo progresso; verificar monotonicidade e ausência
  de exceções.
- **Fuzz simples:** entradas aleatórias com *seed* fixa (strings, bytes, caminhos
  estranhos, linhas de 1 MB); o contrato é "não levanta exceção inesperada".
- **Fim de fluxo anômalo:** cancelar no meio, erro na primeira/última chamada, processo
  externo que morre.

## 5. Testes de arquitetura

Reutilize o auditor AST (skill `arquitetura-modular-codigo-limpo`) como teste:
`assert auditar_projeto() == []`. Falha de build quando camada viola import, módulo
estoura limite ou função pública perde docstring.

## 6. Rotina antes de entregar

1. Auditoria de arquitetura → 0 violações.
2. `python -m pytest -v -m "not slow"` → tudo verde.
3. Quando mexer em desempenho/concorrência: `pytest -m slow`.
4. Se algo falhar: corrija a causa (não o teste, a menos que o teste esteja errado) e
   rode novamente a suíte **inteira**.
5. Registrar o resultado (contagem e data) na memória do projeto.

## 7. Manutenção

- Mudou um texto/constante de `config`? Testes devem importar a constante, não copiar a string.
- Teste frágil por ordem/estado global → isole com fixture; nunca dependa de ordem.
- Remova testes redundantes; mantenha a suíte rápida (<5 s o ciclo padrão).
- Um `QApplication` por processo: crie via helper que reutiliza `QApplication.instance()`.
- No Windows sandbox: se `python` do Store falhar, use o interpretador real (ver pyenv).
