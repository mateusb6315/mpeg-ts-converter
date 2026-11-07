---
name: interface-desktop-padroes
description: >-
  Use this skill when designing, building, reviewing or extending any desktop/GUI
  application (PyQt/PySide, Tkinter, web-like or other toolkits) and you need a
  reusable interface structure: window layout, state machine, drag & drop, file
  pickers, popups, clickable links, conditional widgets, background work,
  theming and user-facing texts. Generalizes the patterns used in Projeto Broadcast.
---

# Padrões de Interface Desktop (generalistas)

Exemplos em PyQt6; os princípios valem para qualquer toolkit. Detalhes e trechos em
[padroes_pyqt6.md](./references/padroes_pyqt6.md).

## 1. Estrutura geral da interface

1. **Janela única, enxuta e previsível.** Só adicione widgets que o requisito pede.
   Layout típico: linha superior (entrada à esquerda, informações à direita) + barra de
   progresso/status em largura total.
2. **View "burra".** Não contém regra de negócio, não importa Model nem Controller.
   Expõe métodos `exibir_*`, `atualizar_*`, `limpar_*` e **sinais** com tipos simples
   (`str`, `int`, `float`, `Path`). Regras (ex.: "é arquivo válido?") entram por injeção
   (`Callable`).
3. **Divisão de arquivos da view** (quando passar de ~250 linhas):
   `janela_*.py` (composição + eventos), `componentes_*.py` (widgets reutilizáveis e
   diálogos), `estilos_*.py` (QSS/CSS gerado de constantes), `tema_*.py` (paleta/tema).
4. **Tudo textual e visual vem de `config/`**: textos, cores, dimensões, títulos. Nenhum
   literal de UI espalhado no código.
5. **Tema fixo e explícito** (ex.: claro sempre) em um único ponto (`aplicar_tema_*`).

## 2. Máquina de estados da janela

Defina estados num `Enum` do Model (ex.: AGUARDANDO → OCUPADO → CONCLUIDO/FALHOU →
AGUARDANDO). Regras:
- Toda transição passa por **um método** do controlador (`_restaurar_estado_inicial`).
- A View tem um flag `_ocupada`; eventos de entrada (drop, clique) **ignoram** quando ocupada.
- Ao terminar (sucesso ou erro), a janela volta ao estado inicial **sem recriar** widgets.

## 3. Entradas do usuário

- **Drag & drop:** validar em `dragEnterEvent` (rejeitar cedo) **e** reproteger em
  `dropEvent`. Aceitar exatamente o que o requisito pede (ex.: 1 arquivo, extensão X).
  Rejeição = aviso discreto no status, sem popup.
- **Clique que abre seletor de arquivos:** o widget emite `clicada`; a janela traduz em
  `selecao_*_solicitada`; o **controlador** decide se abre o diálogo. Só botão esquerdo, só
  quando livre; cursor de mão quando clicável, seta quando bloqueado.
- **Seletor de arquivo:** método da View recebe `(diretorio_inicial, filtro)` e devolve
  `str` (vazio = cancelado). Filtro e título vêm de `config/`. **Cancelar nunca é erro.**
  Lembrar a última pasta usada na sessão.
- Drop e clique convergem no **mesmo** tratador (`_ao_receber_arquivo`) → uma única
  validação e um único caminho de início.

## 4. Popups, links e mensagens

| Tipo | Regra |
|---|---|
| Informação/erro | `QMessageBox` modal, pai = janela, título fixo, botão único OK, texto curto |
| Pergunta | Botões personalizados "Sim"/"Não" (`addButton` + `clickedButton`), padrão = opção segura ("Não") |
| Link clicável | `setTextFormat(RichText)` + `TextBrowserInteraction`, link em `<a href>` no texto vindo de `config/` |
| Aviso não bloqueante | Campo de status no painel, nunca popup |
| Confirmação ao fechar | Só se houver trabalho em andamento; se confirmado, cancelar o trabalho via callback injetado e aguardar a thread |

Popups são **funções/métodos da View** (`exibir_popup_*`, `perguntar_*`); o controlador só
os solicita e reage ao retorno (`bool`).

## 5. Widgets condicionais (evitar bugs)

- Um widget que depende de uma condição (ex.: botão "Selecionar X" só se X não foi
  detectado) tem **uma única fonte de verdade**: método `definir_visibilidade_*` +
  consulta `esta_*_visivel()` (use `isHidden()`, não `isVisible()`, pois este depende da
  janela estar exibida).
- Todo caminho que **resolve** a condição esconde o widget; todo caminho que **falha**
  mantém/mostra. Liste os caminhos (sim/não/cancelou/arquivo inválido) e teste cada um.
- Quando a condição está pendente, **bloqueie as ações dependentes** (ex.: iniciar
  conversão) com mensagem no status, em *todos* os pontos de entrada.
- Reaplique o status pendente ao restaurar o estado inicial.

## 6. Trabalho em segundo plano

- Padrão `QThread` + `QObject` trabalhador (`moveToThread`), sem sobrescrever `run`.
- Trabalhador traduz callbacks do serviço em sinais (`progresso`, `concluida`, `falhou`,
  `finalizado`); captura exceções específicas e uma genérica logada (nada morre calado).
- Conexões `QueuedConnection`; limitar atualizações visuais (~10/s).
- Verificações de inicialização (ex.: detectar dependência externa) também rodam em thread
  e a GUI abre antes; popups só aparecem no retorno do sinal.
- Cleanup em `finalizado`: `quit`, `wait`, `deleteLater`.

## 7. Checklist de revisão de interface

- [ ] Todos os textos/cores/tamanhos em `config/`; idioma e acentuação corretos.
- [ ] View não importa Model/Controller; recebe validadores por injeção.
- [ ] Estados e transições documentados; volta ao inicial sem reiniciar.
- [ ] Entradas bloqueadas quando ocupado; cancelamento de diálogo tratado.
- [ ] Popups: um por evento, título fixo, botões corretos, link clicável quando houver.
- [ ] Widgets condicionais cobrem todos os caminhos (resolveu/falhou/cancelou).
- [ ] Nada bloqueia a thread da UI; atualização de widgets só via sinais.
- [ ] Testes headless (`QT_QPA_PLATFORM=offscreen`) com diálogos substituídos por lambdas.
