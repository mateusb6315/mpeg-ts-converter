# Prompt: Refatoração Modular de Script Python com Interface Gráfica PyQt6 (MVC + SRP + Baixo Acoplamento)

## 1. Papel

Você é um engenheiro de software sênior especialista em Python, arquitetura de software, código limpo e **interfaces gráficas desktop com PyQt6 (Windows)**. Sua missão é analisar um script Python monolítico (ou mal organizado) que converte arquivos de vídeo `.ts`, refatorá-lo em uma estrutura modular, legível, extensível e de fácil manutenção e **acoplá-lo a uma interface gráfica simples de arrastar e soltar (drag & drop)**, **sem alterar o comportamento da conversão em si**.

---

## 2. Objetivo

Receber o script Python fornecido, entender o que ele faz e reorganizá-lo em módulos separados por responsabilidade, aplicando:

- **MVC** (Model, View, Controller) como organização macro.
- **SRP (Princípio da Responsabilidade Única) de forma pragmática**, ou seja, não de forma extremista (ver seção 5.2).
- **Arquitetura de baixo acoplamento** e alta coesão.
- **Código limpo, legível e extensível.**
- **Padronização rigorosa** de escrita, distribuição de módulos e tamanho de funções.
- **Interface gráfica PyQt6** conforme os requisitos da **seção 6**: janela pequena e horizontal, modo claro, entrada por drag & drop, conversão em segundo plano, barra de progresso verde estilo Windows e popup de conclusão.

---

## 3. Entrada

O script Python a ser refatorado será fornecido abaixo (ou anexado) pelo usuário:

```
[COLE AQUI O SCRIPT PYTHON OU INDIQUE O ARQUIVO ANEXADO]
```

Informações complementares (preencher se souber; caso contrário, deduza a partir do código):

- **Versão do Python alvo:** 3.10+ (padrão, se não informado)
- **Sistema operacional alvo:** Windows 10/11
- **Tipo de aplicação:** GUI desktop (PyQt6) que envolve um script de conversão de arquivos `.ts`
- **Dependências externas permitidas:** apenas as já usadas no script **+ `PyQt6`** (autorizada explicitamente pelo usuário para a interface). Nenhuma outra biblioteca nova sem justificativa.
- **Pontos de dor conhecidos:** [ex.: funções gigantes, variáveis globais, difícil de testar]

> Se algo essencial estiver ambíguo e impedir uma decisão arquitetural segura, faça **no máximo 3 perguntas objetivas** antes de começar. Se o problema for menor, tome a decisão mais razoável, **registre a suposição** e siga em frente.

---

## 4. Processo obrigatório (siga na ordem)

### Etapa 1: Análise do script original

Antes de escrever qualquer código novo, produza um diagnóstico curto contendo:

1. **Resumo funcional:** o que o script faz, em 3 a 6 linhas.
2. **Mapa de responsabilidades:** liste os blocos/funções existentes e classifique cada um como:
   - dados / regras de negócio → candidato a **Model**
   - entrada/saída com usuário (print, input, GUI, formatação) → candidato a **View**
   - orquestração / fluxo / decisões → candidato a **Controller**
   - infraestrutura (arquivos, rede, banco, APIs externas, subprocessos) → candidato a **Serviço/Repositório**
   - utilitários genéricos → candidato a **Utilitários**
   - configuração / constantes → candidato a **Configuração**
3. **Problemas encontrados:** variáveis globais, funções longas, duplicação de código, acoplamento forte, números/strings mágicos, tratamento de erro inexistente, efeitos colaterais ocultos, mistura de I/O com lógica.
4. **Riscos de refatoração:** pontos em que a mudança poderia alterar o comportamento (ordem de execução, estado global, efeitos colaterais).
5. **Pontos de integração com a GUI** (obrigatório neste projeto):
   - Como a conversão é executada (subprocesso como `ffmpeg`, biblioteca Python, outro)?
   - Como o arquivo `.ts` de entrada era informado (argumento, `input()`, caminho fixo)?
   - Onde e com qual nome o arquivo convertido é gravado?
   - Existem `input()`, `print()` para o usuário, `sys.exit()` ou laços bloqueantes que impeçam rodar dentro de uma GUI?
   - **Como o progresso pode ser medido** (ver estratégias na seção 6.7)?

### Etapa 2: Planejamento da arquitetura

Apresente, antes do código:

1. **Árvore de diretórios proposta** (ver seção 7 como referência).
2. **Responsabilidade de cada módulo** em uma linha.
3. **Diagrama textual de dependências** (quem importa quem), demonstrando o sentido do fluxo (ex.: `main → controlador → modelo/serviço`; a View nunca importa o Model diretamente, e o Model nunca importa View ou Controller).
4. **Fluxo da interface:** estados da janela (seção 6.2) e os sinais Qt que ligam View, Controller e o trabalhador em segundo plano.
5. **Mapa de migração:** tabela relacionando cada função/bloco do script original ao módulo/função novo onde ele passou a viver. Inclua uma seção "Elementos novos (sem origem no script)" para tudo que pertence à GUI.

### Etapa 3: Implementação

Escreva o código completo de **todos os arquivos**, um por bloco de código, identificado pelo caminho relativo. Nenhum arquivo pode ficar com `...`, `# TODO` ou trechos omitidos. Inclua o `requirements.txt` com `PyQt6` (e as demais dependências já usadas).

### Etapa 4: Revisão final

Execute mentalmente o checklist da seção 12 e inclua o resultado no final da resposta.

---

## 5. Princípios de arquitetura

### 5.1 MVC aplicado a scripts Python

- **Model (`modelos/`)**: estruturas de dados e regras de negócio puras. Não conhece View, Controller, Qt, `print`, `input` nem detalhes de I/O. Deve ser testável isoladamente.
- **View (`visoes/`)**: tudo que interage com o usuário (janela PyQt6, widgets, estilos, mensagens, popups, formatação visual). Não contém regra de negócio.
- **Controller (`controladores/`)**: coordena o fluxo; recebe eventos da View, aciona Models/Serviços e devolve resultados à View. É "fino": orquestra, não calcula. Também hospeda o objeto trabalhador que executa a conversão em thread separada (seção 6.3).
- **Serviços (`servicos/`)**: acesso a recursos externos (arquivos, subprocessos, sistema operacional). Isolam a infraestrutura do restante e **não conhecem Qt**.
- **Configuração (`config/`)**: constantes, caminhos, parâmetros, cores, dimensões e textos fixos da interface que antes estavam "mágicos" no código.
- **Utilitários (`utilitarios/`)**: funções genéricas, sem estado e sem dependência do domínio (ex.: formatação de tamanho, duração e percentual).

> Adapte o MVC ao contexto, **sem criar camadas vazias só para cumprir formalidade**.

### 5.2 SRP, de forma pragmática ("não totalmente")

- Cada **módulo** deve ter **um motivo principal para mudar**.
- Cada **função** deve fazer **uma coisa bem definida**, descrita em uma frase sem usar "e".
- **Não fragmente em excesso:** evite criar classes/arquivos de 5 linhas apenas para "purismo". Agrupe no mesmo módulo funções intimamente relacionadas.
- Regra prática: se separar não melhora legibilidade, testabilidade ou extensibilidade de forma clara, **não separe**.
- Prefira **funções simples** a classes quando não houver estado a gerenciar. Use classes quando houver estado, identidade ou polimorfismo real (widgets Qt, controlador com estado da conversão e trabalhador em thread são casos legítimos).

### 5.3 Baixo acoplamento

- **Injeção de dependências** via parâmetros de função ou construtor (nunca instanciar dependências pesadas dentro de funções de negócio).
- **Dependa de abstrações simples** (funções, `Callable`, `Protocol` ou classes base leves) quando houver mais de uma implementação possível ou necessidade de teste com *mocks*. Não crie abstrações sem necessidade real.
- **Proibido** estado global mutável. Constantes globais são aceitas apenas em `config/`.
- Módulos se comunicam por **dados bem definidos** (`dataclass`, `dict` documentado ou tipos simples), não por conhecimento dos detalhes internos uns dos outros.
- **Sem importações circulares.** O fluxo de dependência deve ser sempre unidirecional: `main → controlador → (modelo | serviço | visão)`.
- A **View e o Model não se conhecem.** Quem os conecta é o Controller. A View recebe e emite apenas **tipos simples** (`str`, `int`, `float`, `Path`) e **sinais Qt**.
- **`main.py` é a raiz de composição**: é o único ponto autorizado a importar todas as camadas para criar os objetos e injetar as dependências.
- **Imports de `PyQt6` são permitidos somente em `main.py`, `visoes/` e `controladores/`.** Nunca em `modelos/`, `servicos/`, `utilitarios/` ou `config/`.

### 5.4 Extensibilidade

- Estruture o código de modo que **adicionar um novo recurso** (novo formato de saída, nova regra, novo campo informativo na janela) exija **criar ou estender**, e não **editar muitos pontos existentes** (princípio aberto/fechado).
- Use dicionários de despacho, estratégias simples ou registro de funções no lugar de longas cadeias de `if/elif` quando houver variações de comportamento.
- Deixe pontos de extensão claros e comentados.

---

## 6. Requisitos da interface gráfica (PyQt6)

Esta seção descreve o comportamento **obrigatório** da GUI. Não adicione botões, menus, abas ou recursos visuais além dos descritos.

### 6.1 Janela

- **Framework:** `PyQt6` (>= 6.5). Nenhum outro toolkit gráfico.
- **Título da janela:** deve conter **"Projeto Broadcast"**. Sugestão: `"Projeto Broadcast - Conversor TS"` (ajuste o sufixo ao que a conversão realmente faz). O texto fica em constante em `config/`.
- **Modo claro, sempre:** a aparência não pode seguir o modo escuro do Windows. Aplique o estilo `Fusion` com uma `QPalette` clara explícita e, quando disponível na versão instalada do Qt, force também o esquema de cores claro (`QStyleHints.setColorScheme(Qt.ColorScheme.Light)`, protegido por verificação de existência). Essa lógica vive em `visoes/tema_visao.py`, na função `aplicar_tema_claro(aplicacao)`.
- **Tamanho:** janela **pequena e horizontal**, tamanho fixo (sem redimensionar nem maximizar), sugestão **560 × 170 px** (proporção aproximada 3,3:1). Dimensões em `config/`.
- **Layout (de cima para baixo):**
  1. **Linha superior, duas colunas lado a lado:**
     - **Esquerda, zona de arraste:** retângulo com borda tracejada e o texto *"Arraste um arquivo .ts aqui"*. Durante a conversão exibe o nome do arquivo em processamento e fica visualmente desabilitada (tom apagado).
     - **Direita, painel de informações**, em pares rótulo/valor (ver seção 6.6).
  2. **Linha inferior, largura total:** barra de progresso verde com o percentual centralizado.
- **Barra de progresso (verde do Windows):** `QProgressBar` de 0 a 100, altura aproximada de 20 px, preenchimento verde `#06B025`, fundo cinza claro `#E6E6E6`, borda fina `#BCBCBC`, cantos pouco ou nada arredondados, texto do percentual centralizado e legível sobre as duas cores. Estilo via QSS gerado a partir das constantes de `config/` (módulo `visoes/estilos_visao.py`). Sem animações decorativas.
- **Todos os textos visíveis ao usuário em português do Brasil**, com acentuação correta.

### 6.2 Estados e fluxo (drag & drop)

| Estado | O que a janela mostra | Transição |
|---|---|---|
| **Inicial (aguardando)** | Zona de arraste ativa; campos de informação com `—`; barra em 0%; status *"Aguardando arquivo .ts"* | Soltar um `.ts` válido → *Convertendo* |
| **Convertendo** | Nome do arquivo na zona de arraste (apagada); informações do arquivo preenchidas; barra avançando; tempos atualizados | Fim com sucesso → *Concluída*; erro → *Falhou* |
| **Concluída** | Barra em 100%; status *"Concluído"*; **popup de conclusão** (seção 6.4) | Usuário clica em OK → *Inicial* |
| **Falhou** | Status *"Falha na conversão"*; popup de erro com mensagem curta e botão OK | Usuário clica em OK → *Inicial* |

Regras do drag & drop:

- A janela inteira aceita o arraste. O **início da conversão é automático** ao soltar um arquivo válido; não existe botão "Iniciar".
- Aceite **exatamente um arquivo local** cuja extensão seja `.ts` (comparação **sem diferenciar maiúsculas/minúsculas**, existente e não sendo diretório). A regra `eh_arquivo_ts` é pura e vive no Model (ou em utilitários); a View a recebe **injetada como `Callable[[Path], bool]`**, sem importar o Model.
- Durante o `dragEnterEvent`, rejeite (cursor de proibido) o que for inválido **e tudo o que chegar enquanto uma conversão estiver em andamento**. Proteja também o `dropEvent` contra esse caso.
- Soltou algo inválido (outra extensão, vários arquivos, pasta)? Mostre aviso discreto no campo de status (*"Solte um único arquivo .ts"*), **sem popup**, e permaneça no estado atual.
- Concluída a conversão (ou falha) e fechado o popup, a janela volta **exatamente ao estado inicial**, pronta para receber outro `.ts`, **sem reiniciar o aplicativo e sem recriar a janela**.

### 6.3 Execução em segundo plano

- A conversão **nunca** roda na thread da interface. Use o padrão **`QThread` + objeto trabalhador (`QObject`) movido para a thread** (`moveToThread`), sem sobrescrever `QThread.run`.
- O trabalhador fica em `controladores/` (ex.: `conversao_trabalhador.py`) e **traduz os callbacks do serviço em sinais Qt**: `progresso(float)`, `concluida(str)`, `falhou(str)` e `finalizado()`.
- O **serviço de conversão não conhece Qt**: recebe um *callback* `ao_progredir(percentual: float)` por injeção e levanta uma exceção específica (ex.: `ErroConversao`) em caso de falha. O trabalhador captura essa exceção e emite `falhou`; nenhuma exceção pode morrer silenciosamente na thread.
- A atualização da interface ocorre **somente via sinais/slots** (conexões em fila entre threads). Limite as atualizações visuais a cerca de **10 por segundo** para não sobrecarregar a GUI.
- **Tempo decorrido** atualizado por um `QTimer` de 1 s no controlador (continua correndo mesmo que o progresso fique parado por instantes).
- O controlador mantém referências à thread e ao trabalhador enquanto a conversão durar (evita coleta de lixo prematura) e faz a limpeza (`quit`, `wait`, `deleteLater`) ao receber `finalizado`.
- **Fechar a janela durante a conversão:** pergunte confirmação ao usuário; se confirmar, encerre o subprocesso/trabalho de forma limpa e aguarde a thread terminar antes de sair (sem deixar processos órfãos). Esse mecanismo não pode acoplar a View ao Controller (use `Callable` injetado ou sinal).
- **Windows + subprocesso:** se a conversão usa um executável externo (ex.: `ffmpeg`), inicie-o com `creationflags=subprocess.CREATE_NO_WINDOW` para não abrir janela de console. Isso é infraestrutura e fica no serviço, isolado por verificação de plataforma.

### 6.4 Popups (janela de mensagem do Windows)

- **Conclusão:** `QMessageBox` modal, ícone de informação (`Icon.Information`), pai = janela principal, título **"Projeto Broadcast"**, texto exatamente **"Conversão concluída"** e **um único botão "OK"** (`StandardButton.Ok`). Exibido uma única vez por conversão, só depois de a barra chegar a 100%.
- **Erro (premissa a registrar em "Decisões e suposições"):** `QMessageBox` com `Icon.Critical`, mesmo título, mensagem curta e botão único "OK".
- Os popups são criados pela **View** (ex.: `exibir_popup_conclusao()`, `exibir_popup_erro(mensagem)`); o Controller apenas os solicita. Ao retornar do popup, o Controller reinicia a View ao estado inicial.

### 6.5 Mapeamento da GUI no MVC

| Camada | Responsabilidade na GUI | Restrições |
|---|---|---|
| **Model** | `dataclass` das informações do arquivo e do progresso, enum de estados, `eh_arquivo_ts`, cálculo do tempo restante | Sem Qt, sem I/O |
| **Serviço** | Ler tamanho/duração do arquivo, executar a conversão (preservando o comportamento original) e reportar progresso via callback | Sem Qt |
| **View** | Janela, zona de arraste, painel de informações, barra de progresso, popups, QSS e tema; expõe métodos `exibir_*`, `limpar_*` e sinais (`arquivo_solto(str)`) | Sem regra de negócio; não importa Model nem Controller |
| **Controller** | Conecta sinais, valida a soltura, cria thread/trabalhador, converte eventos em chamadas à View, controla o estado e reinicia a janela | Fino; sem cálculo nem I/O direto |
| **`main.py`** | Cria `QApplication`, aplica o tema claro, configura `logging`, monta e injeta dependências, exibe a janela e entra em `aplicacao.exec()` | Raiz de composição |

Se um módulo de View passar de ~250 linhas, divida em: `janela_principal.py` (composição e eventos), `componentes_visao.py` (zona de arraste, painel de informações) e `estilos_visao.py` / `tema_visao.py`.

### 6.6 Informações exibidas (mínimo)

Exiba **somente o que puder ser obtido de forma confiável** (não invente campos):

- **Arquivo:** nome (se longo, truncar no meio com `…` e colocar o caminho completo em *tooltip*), tamanho formatado em pt-BR (ex.: `1,2 GB`) e duração `hh:mm:ss` quando o motor de conversão permitir obtê-la. Se o script original já determina outras propriedades (codec, resolução, formato de saída), pode exibi-las.
- **Processo:** status textual, percentual, tempo decorrido e **tempo restante estimado** (mostrar *"calculando…"* até haver dados suficientes).

Funções de formatação (`formatar_tamanho`, `formatar_duracao`, `formatar_percentual`) são puras e ficam em `utilitarios/`.

### 6.7 Como obter o progresso (decida na Etapa 1 e registre)

Avalie as estratégias na ordem e use a primeira viável:

1. **Motor `ffmpeg`:** obtenha a duração total com `ffprobe` e leia o progresso em tempo real pela saída estruturada (`-progress pipe:1 -nostats`), calculando `percentual = tempo_processado / duracao_total * 100`. Esses parâmetros **não alteram o arquivo gerado**, mas devem ser listados em "Riscos" e "Decisões".
2. **Biblioteca Python com callback ou iterador de progresso:** adapte-o ao callback `ao_progredir`.
3. **Sem progresso mensurável:** use barra em modo indeterminado (`setRange(0, 0)`) com o texto *"Convertendo…"*, vá a 100% ao concluir e **registre essa limitação em "Observações"**.

Regras: o percentual é sempre limitado ao intervalo 0–100 e **nunca regride**; a barra só chega a 100% quando a conversão termina com sucesso. O parser da saída de progresso é uma **função pura** (testável sem ffmpeg instalado).

### 6.8 Requisitos específicos de Windows

- Use `pathlib.Path` e suporte caminhos com espaços e caracteres Unicode (arquivos arrastados do Explorer).
- Nenhuma janela de console deve aparecer durante a conversão (seção 6.3).
- Instruções de execução devem citar `python main.py` e, opcionalmente, `pythonw main.py` para rodar sem console. Como não haverá console visível, `logging` deve gravar em arquivo (caminho em `config/`), configurado em um único ponto (`main.py`).

### 6.9 Testes da camada de interface

- Não exija servidor gráfico nos testes. Teste apenas lógica pura: `eh_arquivo_ts`, formatadores, cálculo de percentual/tempo restante e parser de progresso.
- A GUI em si pode ser verificada manualmente; descreva em "Como executar" um roteiro curto de verificação (arrastar `.ts`, arrastar arquivo inválido, arrastar durante conversão, concluir e arrastar outro).

---

## 7. Estrutura de diretórios de referência

Adapte conforme o script, removendo o que não for necessário:

```
projeto/
├── main.py                        # raiz de composição: QApplication, tema, logging, injeção e janela
├── config/
│   ├── __init__.py
│   ├── configuracoes.py           # constantes, caminhos, parâmetros da conversão
│   └── interface.py               # título, textos, cores, dimensões e caminho do log
├── modelos/
│   ├── __init__.py
│   └── conversao.py               # dataclasses, enum de estados, eh_arquivo_ts, tempo restante
├── servicos/
│   ├── __init__.py
│   ├── conversao_servico.py       # motor de conversão original + callback de progresso
│   └── arquivo_servico.py         # tamanho e duração do arquivo de entrada
├── visoes/
│   ├── __init__.py
│   ├── janela_principal.py        # janela, eventos de drag & drop e popups
│   ├── componentes_visao.py       # zona de arraste e painel de informações
│   ├── estilos_visao.py           # QSS (barra de progresso verde, zona tracejada)
│   └── tema_visao.py              # aplicar_tema_claro
├── controladores/
│   ├── __init__.py
│   ├── conversao_controlador.py   # orquestração do fluxo e dos estados
│   └── conversao_trabalhador.py   # QObject executado em QThread
├── utilitarios/
│   ├── __init__.py
│   └── formatacao.py              # tamanho, duração e percentual em pt-BR
├── tests/                         # opcional (ver seção 10)
├── requirements.txt               # PyQt6 + dependências já usadas pelo script
└── README.md                      # breve: como executar e visão da arquitetura
```

---

## 8. Padrões de código (obrigatórios e uniformes)

### 8.1 Idioma e nomenclatura

- **Funções, variáveis, classes, módulos, parâmetros, constantes e sinais Qt próprios em português.**
- Convenções:
  - funções e variáveis: `snake_case` → `calcular_total_pedido`, `lista_clientes`
  - classes: `PascalCase` → `Pedido`, `ServicoArquivo`
  - constantes: `MAIUSCULAS_COM_UNDERSCORE` → `TAXA_PADRAO`, `CAMINHO_ENTRADA`
  - módulos/arquivos: `snake_case` → `pedido_controlador.py`
- **Sem acentos e sem `ç` em identificadores** (ex.: `configuracao`, não `configuração`) para evitar problemas de compatibilidade. Acentos são permitidos em comentários, docstrings e textos exibidos ao usuário.
- Nomes **descritivos e sem abreviações obscuras**. Funções começam com **verbo no infinitivo** (`carregar_`, `validar_`, `calcular_`, `exibir_`, `salvar_`, `converter_`). Funções booleanas começam com `eh_`, `possui_`, `tem_` ou `deve_`.
- Palavras-chave e APIs da biblioteca padrão/terceiros permanecem como são (`def`, `self`, `open`, `json.load`...). **Isso inclui os métodos do Qt que precisam ser sobrescritos** (`dragEnterEvent`, `dropEvent`, `closeEvent`) e as chamadas da API do PyQt6. Apenas o código de autoria própria é traduzido.
- Use a **mesma palavra para o mesmo conceito** em todo o projeto (ex.: sempre `carregar`, nunca alternar entre `carregar`, `buscar` e `obter` para a mesma ideia).

### 8.2 Tamanho e forma das funções

- **Alvo:** 5 a 20 linhas de código por função.
- **Limite máximo:** 30 linhas (sem contar docstring e linhas em branco). Passou disso, divida. Em widgets, separe a montagem em métodos privados (`_criar_zona_arraste`, `_criar_painel_informacoes`, `_criar_barra_progresso`, `_montar_layout`).
- **Máximo de 4 parâmetros** por função. Se precisar de mais, agrupe em `dataclass` ou objeto de configuração.
- **Nível de indentação máximo:** 3. Use *early return* (cláusulas de guarda) para reduzir aninhamento.
- **Complexidade baixa:** evite funções com muitos ramos; extraia ramificações em funções auxiliares nomeadas.
- Retornos consistentes: a função sempre retorna o mesmo tipo (evite alternar entre `None`, `str` e `dict`).
- Funções "puras" sempre que possível (mesma entrada → mesma saída, sem efeitos colaterais).

### 8.3 Tamanho e distribuição dos módulos

- **Alvo:** 80 a 200 linhas por módulo. **Máximo:** ~250 linhas.
- Módulos de mesma camada seguem **a mesma estrutura interna**, nesta ordem:
  1. docstring do módulo
  2. imports (biblioteca padrão → terceiros, incluindo `PyQt6` → módulos do projeto, separados por linha em branco)
  3. constantes locais (se houver)
  4. classes/funções públicas
  5. funções auxiliares privadas (prefixo `_`) ao final, ou imediatamente antes de quem as usa. **Escolha uma convenção e mantenha em todo o projeto.**
- Imports **absolutos** a partir da raiz do projeto, sem `import *`.

### 8.4 Estilo geral

- Seguir **PEP 8** (linhas de até 100 caracteres, 4 espaços de indentação, duas linhas em branco entre definições de topo).
- **Type hints** em todas as assinaturas de funções públicas.
- Use `dataclass` para estruturas de dados no lugar de dicionários soltos ou tuplas misteriosas.
- Use `pathlib.Path` em vez de concatenação de strings para caminhos.
- Use *f-strings*; use `with` para recursos; prefira *comprehensions* simples a laços verbosos quando mantiverem a legibilidade.
- Substitua **números e textos mágicos** (incluindo cores, tamanhos e mensagens da interface) por constantes nomeadas em `config/`.
- Elimine código morto, `print` de depuração e comentários obsoletos.

### 8.5 Tratamento de erros e logging

- Capture **exceções específicas** (nunca `except:` nu ou `except Exception: pass`).
- Erros de infraestrutura são tratados/traduzidos nos **serviços**; decisões sobre o que fazer com o erro ficam no **controlador**; a mensagem ao usuário é exibida pela **view**.
- Se o script original usa `print` para diagnóstico, substitua por `logging` configurado em um único ponto (`main.py`), gravando em arquivo (seção 6.8). Mensagens destinadas ao usuário final passam a ser elementos da View (status, popups).
- Use `if __name__ == "__main__":` em `main.py`, chamando uma função `principal()` que retorna código de saída (o valor de `aplicacao.exec()`).

---

## 9. Regras de comentários e documentação

- **Docstring em todo módulo, classe e função pública**, em português, no formato:

```python
def calcular_desconto(valor: float, percentual: float) -> float:
    """Calcula o valor do desconto a ser aplicado.

    Args:
        valor: Valor bruto original.
        percentual: Percentual de desconto entre 0 e 100.

    Returns:
        Valor do desconto em unidades monetárias.

    Raises:
        ValueError: Se o percentual estiver fora do intervalo permitido.
    """
```

- **Comentários inline explicam o "porquê", não o "o quê".** Evite comentar o óbvio (`i += 1  # incrementa i`). Comente decisões, regras de negócio, *workarounds* e armadilhas (ex.: por que a conexão de sinais é em fila, por que `CREATE_NO_WINDOW`).
- Use **cabeçalhos de seção** curtos em módulos maiores, por exemplo: `# --- Validações ---`.
- Marque **pontos de extensão** com o comentário padrão: `# EXTENSÃO: <como adicionar novo comportamento aqui>`.
- Preserve comentários úteis do código original (traduzindo-os para português, se necessário) e remova os obsoletos.
- Mantenha o **mesmo estilo e a mesma densidade de comentários** em todos os módulos.

---

## 10. Testes e verificação (opcional, mas recomendado)

- Se o código original não tiver testes, inclua uma pasta `tests/` com **testes básicos de unidade** (`pytest`) para as principais funções puras do Model e utilitários, demonstrando que a arquitetura é testável.
- Nomes de testes em português: `test_calcular_total_com_desconto_retorna_valor_correto`.
- Os testes **não devem exigir rede, banco, arquivos reais, ffmpeg instalado nem servidor gráfico**; use injeção de dependência e dublês simples.
- Cobertura mínima sugerida para este projeto: `eh_arquivo_ts` (maiúsculas, extensões erradas), formatadores, cálculo de percentual limitado a 0–100, tempo restante estimado e parser de progresso.
- Se o tempo/tamanho da resposta for limitado, priorize o código refatorado e indique quais testes seriam os mais importantes.

---

## 11. Restrições (o que NÃO fazer)

- ❌ **Não altere o comportamento da conversão** (parâmetros, formato e nome do arquivo gerado, local de saída, efeitos colaterais). As **únicas mudanças intencionais** são as descritas na seção 6 (entrada por drag & drop, execução em segundo plano, barra de progresso, popups). Se identificar um bug no original, **não o corrija silenciosamente**: preserve o comportamento e **liste o bug** em "Observações" com sugestão de correção.
- ❌ Não adicione bibliotecas ou *frameworks* novos além de `PyQt6` sem necessidade clara e justificativa.
- ❌ Não superengenheirar: evitar padrões de projeto desnecessários, hierarquias profundas de herança, fábricas e interfaces sem uso real.
- ❌ Não use variáveis globais mutáveis nem *singletons* ocultos.
- ❌ Não deixe trechos de código incompletos, `pass` sem propósito ou `...` no lugar de implementação.
- ❌ Não misture idiomas em identificadores próprios (nada de `calcular_total_item` ao lado de `get_user_name`).
- ❌ Não faça I/O (print/input/arquivo/rede) dentro de funções de regra de negócio.
- ❌ **Não bloqueie a thread da interface** (nada de `time.sleep`, `subprocess.run` ou laços longos na GUI).
- ❌ **Não importe `PyQt6`** em `modelos/`, `servicos/`, `utilitarios/` nem `config/`.
- ❌ **Não atualize widgets a partir de outra thread**; use sempre sinais e slots.
- ❌ **Não use tema escuro nem siga o tema do Windows**; a interface é sempre clara.
- ❌ **Não adicione elementos de interface não solicitados** (botão de iniciar/cancelar, menus, seletor de arquivo, histórico).
- ❌ Não feche nem recrie a janela entre uma conversão e a próxima; ela é reiniciada ao estado inicial.
- ❌ Não exiba o popup de conclusão antes de a conversão realmente terminar, nem mais de uma vez por conversão.

---

## 12. Checklist de qualidade (verifique antes de entregar)

**Arquitetura**
- [ ] Model não importa View, Controller nem faz I/O.
- [ ] View não contém regra de negócio e não importa Model nem Controller.
- [ ] Controller é fino e apenas orquestra.
- [ ] Infraestrutura isolada em `servicos/`.
- [ ] Sem importações circulares; fluxo de dependência unidirecional (exceto `main.py` como raiz de composição).
- [ ] Dependências injetadas, sem estado global mutável.
- [ ] Constantes e valores mágicos (inclusive cores, tamanhos e textos da GUI) movidos para `config/`.

**Padronização**
- [ ] Todos os identificadores próprios em português, `snake_case`/`PascalCase`/`MAIUSCULAS` conforme o tipo.
- [ ] Nenhuma função acima de 30 linhas; maioria entre 5 e 20.
- [ ] Nenhuma função com mais de 4 parâmetros.
- [ ] Nenhum módulo acima de ~250 linhas.
- [ ] Estrutura interna dos módulos uniforme.
- [ ] Type hints e docstrings nas funções públicas.

**Comportamento**
- [ ] Todas as funcionalidades do script original foram migradas (conferir pelo mapa de migração).
- [ ] Ordem de execução, parâmetros de conversão e arquivo gerado preservados.
- [ ] Ponto de entrada (`main.py`) abre a GUI e a conversão produz o mesmo resultado do script original.

**Interface gráfica (seção 6)**
- [ ] Título da janela contém "Projeto Broadcast".
- [ ] Modo claro forçado (Fusion + paleta clara), independente do tema do Windows.
- [ ] Janela pequena, horizontal e de tamanho fixo; informações do arquivo e do processo visíveis.
- [ ] Barra de progresso verde do Windows (`#06B025`) acompanha o progresso real, nunca regride e só chega a 100% ao concluir.
- [ ] Drag & drop aceita apenas um `.ts` válido e inicia a conversão automaticamente.
- [ ] Soltura inválida ou durante conversão é rejeitada sem popup e sem quebrar o estado.
- [ ] Conversão roda em `QThread` + trabalhador; a GUI nunca congela.
- [ ] Serviço sem Qt, comunicando-se por callback; exceções viram sinal `falhou`.
- [ ] Popup "Conversão concluída" com único botão OK, exibido uma vez; erro tratado com popup crítico.
- [ ] Após o OK, a janela volta ao estado inicial e aceita novo `.ts` sem reiniciar.
- [ ] Fechamento durante a conversão tratado sem deixar processos órfãos; sem janela de console.

**Legibilidade**
- [ ] Comentários explicam o "porquê".
- [ ] Sem código morto, sem `print` de depuração.
- [ ] Tratamento de exceções específico e coerente.

---

## 13. Formato da resposta

Entregue a resposta **em português**, exatamente nesta ordem:

1. **Diagnóstico do script original** (Etapa 1, incluindo pontos de integração com a GUI e a estratégia de progresso escolhida).
2. **Arquitetura proposta**: árvore de diretórios, responsabilidade de cada módulo, diagrama textual de dependências e fluxo da interface (estados e sinais).
3. **Mapa de migração** (tabela: *elemento original → destino na nova estrutura*, mais a seção de elementos novos da GUI).
4. **Código completo**: um bloco por arquivo, cada um precedido pelo caminho relativo em negrito (ex.: **`modelos/conversao.py`**), seguindo a ordem: `config` → `utilitarios` → `modelos` → `servicos` → `visoes` → `controladores` → `main.py` → `requirements.txt`.
5. **Como executar**: comandos para instalar (`pip install -r requirements.txt`), rodar o projeto (e os testes, se houver) e o roteiro curto de verificação manual da GUI.
6. **Decisões e suposições**: justificativas das principais escolhas arquiteturais e quaisquer premissas assumidas (título exato, dimensões, comportamento em erro, comportamento ao fechar a janela, estratégia de progresso).
7. **Observações**: bugs ou riscos detectados no original que foram preservados, limitações (ex.: progresso indeterminado) e sugestões de melhorias futuras.
8. **Checklist final** (seção 12) marcado.

Seja objetivo nas explicações; o foco da resposta é o código refatorado de alta qualidade.

---

## 14. Exemplo de padrão desejado (referência de estilo)

### 14.1 Separação MVC em um script simples

**Antes (script monolítico):**

```python
import json
total = 0
dados = json.load(open("pedidos.json"))
for p in dados:
    if p["status"] == "ok":
        total += p["valor"] * 0.9 if p["valor"] > 100 else p["valor"]
print("Total:", total)
```

**Depois (separação por responsabilidade, em estilo uniforme):**

**`config/configuracoes.py`**
```python
"""Constantes e parâmetros globais da aplicação."""
from pathlib import Path

CAMINHO_PEDIDOS = Path("pedidos.json")
STATUS_VALIDO = "ok"
LIMITE_DESCONTO = 100.0
FATOR_DESCONTO = 0.9
```

**`servicos/pedidos_servico.py`**
```python
"""Acesso aos dados de pedidos armazenados em arquivo JSON."""
import json
from pathlib import Path


def carregar_pedidos(caminho: Path) -> list[dict]:
    """Lê o arquivo JSON e devolve a lista bruta de pedidos."""
    with caminho.open(encoding="utf-8") as arquivo:
        return json.load(arquivo)
```

**`modelos/pedido.py`**
```python
"""Regras de negócio relacionadas a pedidos."""
from config.configuracoes import FATOR_DESCONTO, LIMITE_DESCONTO, STATUS_VALIDO


def eh_pedido_valido(pedido: dict) -> bool:
    """Indica se o pedido está apto a entrar no cálculo."""
    return pedido["status"] == STATUS_VALIDO


def calcular_valor_final(valor: float) -> float:
    """Aplica desconto apenas para valores acima do limite configurado."""
    # Regra de negócio: desconto vale somente acima do limite.
    return valor * FATOR_DESCONTO if valor > LIMITE_DESCONTO else valor


def calcular_total(pedidos: list[dict]) -> float:
    """Soma o valor final de todos os pedidos válidos."""
    return sum(calcular_valor_final(p["valor"]) for p in pedidos if eh_pedido_valido(p))
```

**`visoes/relatorio_visao.py`**
```python
"""Exibição de resultados ao usuário."""


def exibir_total(total: float) -> None:
    """Mostra o total calculado no terminal."""
    print(f"Total: {total:.2f}")
```

**`controladores/pedidos_controlador.py`**
```python
"""Orquestra o fluxo de cálculo do total de pedidos."""
from config.configuracoes import CAMINHO_PEDIDOS
from modelos.pedido import calcular_total
from servicos.pedidos_servico import carregar_pedidos
from visoes.relatorio_visao import exibir_total


def executar() -> None:
    """Carrega os pedidos, calcula o total e o exibe."""
    pedidos = carregar_pedidos(CAMINHO_PEDIDOS)
    exibir_total(calcular_total(pedidos))
```

**`main.py`**
```python
"""Ponto de entrada da aplicação."""
from controladores.pedidos_controlador import executar


def principal() -> int:
    """Inicia a aplicação e retorna o código de saída."""
    executar()
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
```

### 14.2 Padrão para a camada gráfica PyQt6

Trechos de **referência de estilo e de contrato entre camadas** (não são a implementação completa; a implementação real deve cobrir todos os requisitos da seção 6).

**`visoes/janela_principal.py`** (View: emite sinal com tipos simples e recebe o validador por injeção)
```python
"""Janela principal: recebe arquivos por arrastar e soltar e exibe o andamento."""
from pathlib import Path
from typing import Callable

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QWidget

from config.interface import TITULO_JANELA


class JanelaPrincipal(QWidget):
    """Janela que emite `arquivo_solto` quando o usuário solta um arquivo válido."""

    arquivo_solto = pyqtSignal(str)

    def __init__(self, validar_arquivo: Callable[[Path], bool]) -> None:
        super().__init__()
        self._validar_arquivo = validar_arquivo
        self._ocupada = False
        self.setAcceptDrops(True)
        self.setWindowTitle(TITULO_JANELA)

    def dragEnterEvent(self, evento: QDragEnterEvent) -> None:
        """Aceita o arraste só se houver um único arquivo válido e a janela estiver livre."""
        caminho = self._extrair_caminho(evento)
        if not self._ocupada and caminho is not None and self._validar_arquivo(caminho):
            evento.acceptProposedAction()

    def dropEvent(self, evento: QDropEvent) -> None:
        """Informa ao controlador o arquivo solto, sem decidir o que fazer com ele."""
        caminho = self._extrair_caminho(evento)
        if not self._ocupada and caminho is not None:
            self.arquivo_solto.emit(str(caminho))

    @staticmethod
    def _extrair_caminho(evento: QDragEnterEvent | QDropEvent) -> Path | None:
        """Devolve o caminho local se o arraste contiver exatamente um arquivo."""
        urls = evento.mimeData().urls()
        if len(urls) != 1 or not urls[0].isLocalFile():
            return None
        return Path(urls[0].toLocalFile())
```

**`controladores/conversao_trabalhador.py`** (traduz callbacks do serviço em sinais Qt)
```python
"""Executa a conversão fora da thread da interface e emite sinais Qt."""
from pathlib import Path
from typing import Callable

from PyQt6.QtCore import QObject, pyqtSignal

from servicos.conversao_servico import ErroConversao

FuncaoConversao = Callable[[Path, Callable[[float], None]], Path]


class ConversaoTrabalhador(QObject):
    """Roda a conversão em uma QThread; o serviço não conhece Qt."""

    progresso = pyqtSignal(float)
    concluida = pyqtSignal(str)
    falhou = pyqtSignal(str)
    finalizado = pyqtSignal()

    def __init__(self, converter: FuncaoConversao, origem: Path) -> None:
        super().__init__()
        self._converter = converter
        self._origem = origem

    def executar(self) -> None:
        """Converte o arquivo e emite exatamente um resultado seguido de `finalizado`."""
        try:
            destino = self._converter(self._origem, self.progresso.emit)
        except ErroConversao as erro:
            self.falhou.emit(str(erro))
        else:
            self.concluida.emit(str(destino))
        finally:
            self.finalizado.emit()
```

**`main.py`** (raiz de composição)
```python
"""Ponto de entrada: monta as dependências e inicia a aplicação gráfica."""
import sys

from PyQt6.QtWidgets import QApplication

from controladores.conversao_controlador import ConversaoControlador
from modelos.conversao import eh_arquivo_ts
from servicos.arquivo_servico import ler_informacoes_arquivo
from servicos.conversao_servico import converter_arquivo
from visoes.janela_principal import JanelaPrincipal
from visoes.tema_visao import aplicar_tema_claro


def principal() -> int:
    """Cria a aplicação Qt, liga view e controlador e entra no laço de eventos."""
    aplicacao = QApplication(sys.argv)
    aplicar_tema_claro(aplicacao)
    janela = JanelaPrincipal(validar_arquivo=eh_arquivo_ts)
    controlador = ConversaoControlador(janela, converter_arquivo, ler_informacoes_arquivo)
    controlador.iniciar()
    janela.show()
    return aplicacao.exec()


if __name__ == "__main__":
    raise SystemExit(principal())
```

> Estes exemplos são apenas **referência de estilo, proporção e granularidade**. A estrutura real deve ser derivada do script analisado.

---

## 15. Instrução final

Comece agora pela **Etapa 1 (Diagnóstico)** e siga o processo completo até a entrega do checklist final. Priorize **clareza, consistência, fidelidade ao comportamento da conversão original e conformidade total com a seção 6 (interface gráfica)** acima de sofisticação arquitetural.
