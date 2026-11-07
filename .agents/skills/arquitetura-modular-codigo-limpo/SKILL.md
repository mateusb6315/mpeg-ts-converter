---
name: arquitetura-modular-codigo-limpo
description: >-
  Use this skill when starting, refactoring, reviewing or extending any
  application codebase and you need a reusable architecture and writing style:
  MVC with pragmatic SRP and low coupling, module/function distribution, size
  limits, naming, docstrings, comments, error handling, dependency injection
  and extensibility, focused on readability and maintainability.
---

# Arquitetura Modular e Código Limpo (generalista)

Detalhes e exemplos: [guia_estilo.md](./references/guia_estilo.md). Auditoria automática
adaptável: [auditar_codigo.py](./scripts/auditar_codigo.py).

## 1. Camadas e responsabilidades

| Camada | Contém | Pode importar | Nunca |
|---|---|---|---|
| `config/` | Constantes (caminhos, parâmetros, textos, cores) | stdlib | outras camadas, toolkit de UI |
| `utilitarios/` | Funções puras genéricas (formatação) | `config` | domínio, UI, I/O |
| `modelos/` | `dataclass`, `Enum`, regras de negócio puras | `config` | I/O, UI, serviços |
| `servicos/` | Infraestrutura: arquivos, rede, subprocessos, SO, registro | `config`, `modelos`, `utilitarios` | UI/Qt |
| `visoes/` | Tudo que o usuário vê | `config` | modelos, controladores, serviços |
| `controladores/` | Orquestração, estado, threads | todas as anteriores | regra de negócio nova, I/O direto |
| `main.py` | **Raiz de composição**: cria objetos e injeta dependências | tudo | lógica |

Fluxo único: `main → controlador → (modelo | serviço | visão)`. Sem ciclos. Não crie
camada vazia por formalidade.

## 2. Distribuição de módulos e funções

- **Módulo:** um motivo para mudar; alvo 80–200 linhas, máx. ~250. Passou? Divida por
  responsabilidade (ex.: widgets vs. diálogos vs. estilos), não por tamanho cego.
- **Função:** faz uma coisa (descrita sem "e"); alvo 5–20 linhas, máx. 30 (sem docstring
  e brancos); máx. 4 parâmetros (senão `dataclass`); indentação ≤ 3 (early return).
- **Classe:** só quando há estado, identidade ou polimorfismo (widgets, controlador,
  trabalhador). Caso contrário, função.
- **Pragmatismo:** não fragmente em excesso. Se separar não melhora leitura, teste ou
  extensão, não separe.
- **Ordem interna do módulo:** docstring → imports (stdlib → terceiros → projeto) →
  constantes locais → API pública → auxiliares privadas (`_`) ao final. Uma convenção só.

## 3. Padrões de escrita

- Identificadores no **idioma do projeto, sem misturar** (aqui: português, sem acentos/ç);
  funções começam com verbo (`carregar_`, `validar_`, `calcular_`, `exibir_`); booleanas
  com `eh_/possui_/tem_/deve_`; mesma palavra para o mesmo conceito.
- `snake_case` / `PascalCase` / `MAIUSCULAS`; PEP 8, linhas ≤ 100.
- Type hints em toda função pública; `dataclass` no lugar de dict/tupla misteriosa;
  `pathlib.Path`; f-strings; `with` para recursos.
- **Docstring** (Args/Returns/Raises) em módulo, classe e função pública; privadas
  podem ter uma linha. Comentário inline explica o **porquê** (workarounds, armadilhas).
- Cabeçalhos de seção `# --- Nome ---` e marcador `# EXTENSÃO: como adicionar aqui`.
- Sem números/strings mágicos, sem código morto, sem `print` de depuração.

## 4. Acoplamento e injeção de dependências

- Dependências entram por parâmetro/construtor, com padrão sensato:
  `def __init__(self, janela, verificar=verificar_ambiente, salvar=salvar_manual)`.
  Isso permite substituir por dublês nos testes sem `mock` pesado.
- Sem estado global mutável. Constantes só em `config/`.
- Comunicação entre camadas por dados simples (`dataclass`, `str`, `Path`) e sinais/callbacks.
- Serviço levanta **exceção específica** (`ErroConversao`); quem decide o que fazer é o
  controlador; quem mostra é a view.

## 5. Erros e logging

- Nunca `except:` nu nem `except Exception: pass`. Capturas específicas; uma genérica só
  em fronteira de thread, **logada** (`logger.exception`) e convertida em sinal de falha.
- `logging` configurado em **um único ponto** (`main.py`), em arquivo se não há console.
- Falhas de infraestrutura opcionais (ex.: ferramenta de sondagem ausente) degradam com
  fallback documentado, não derrubam o fluxo.

## 6. Extensibilidade

- Abra para extensão, feche para edição: tuplas/dicionários de configuração, despacho por
  dicionário em vez de `if/elif` longo, pontos `# EXTENSÃO`.
- Novo recurso = criar/estender módulo, não editar muitos pontos.
- Ao adicionar recurso: (1) constantes em `config`, (2) regra pura em `modelos`/`utilitarios`,
  (3) infraestrutura em `servicos`, (4) método na `visao`, (5) fiação no `controlador`,
  (6) composição em `main`, (7) testes, (8) auditoria, (9) atualizar memória/docs.

## 7. Procedimento de revisão

1. Rodar a auditoria ([auditar_codigo.py](./scripts/auditar_codigo.py)) — ajuste
   `CONFIG` no topo para o projeto (camadas, proibições, limites, arquivos).
2. Conferir imports por camada e ciclos.
3. Conferir tamanhos; se um módulo estourou, dividir **por responsabilidade**.
4. Revisar nomes, docstrings e comentários (porquê, não o quê).
5. Registrar decisões e suposições em `MEMORY.md`/README.

## 8. Armadilhas comuns

- Compactar código só para caber no limite prejudica legibilidade: prefira dividir módulos.
- Mover validação para a View "porque é rápido" quebra o isolamento: injete a função.
- Lógica nova no controlador → extraia para `modelos`/`servicos`.
