# Memória do Projeto Broadcast (`MEMORY.md`)

## 1. Visão Geral
Refatoração modular do script monolítico `60 fps BWDIF Python.py` (conversor de vídeo MPEG-TS 60i para HEVC 10-bit 60p MKV via NVIDIA NVEncC com filtro BWDIF bob) para uma arquitetura limpa em Python com interface gráfica desktop **PyQt6** seguindo **MVC + SRP pragmático + Baixo Acoplamento**, conforme especificado em `PROMPT.md`.

## 2. Módulos da Arquitetura
- **Configuração (`config/`):**
  - `configuracoes.py`: Caminhos padrão, nomes de binários (`nvenc64.exe`, `NVEncC64.exe`), filtros de diálogo do Windows Explorer, chave do Registro (`Environment`), URL oficial de download (`https://github.com/rigaya/NVEnc/releases`) e argumentos fixos do `NVEncC`.
  - `interface.py`: Dimensões fixas (`560×170`), paleta clara, cores da barra verde (`#06B025`), textos da zona clicável (*"Selecione ou arraste um arquivo .ts aqui"*), botão *"Selecionar nvenc64"* e mensagens dos popups.
- **Utilitários (`utilitarios/formatacao.py`):** `formatar_tamanho`, `formatar_duracao`, `formatar_percentual`, `truncar_texto_meio`, `citar_argumento_comando`.
- **Model (`modelos/conversao.py`):** `EstadoConversao`, `InformacoesArquivo`, `SegmentoProgresso`, `LinhaLog`, `eh_arquivo_ts`, `gerar_caminho_saida`, `calcular_total_quadros`, `calcular_percentual_progresso`, `calcular_tempo_restante`, `parsear_segmento_progresso`, `selecionar_argumentos_audio`, `construir_argumentos_nvenc`, `validar_fluxos_audio`.
- **Serviços (`servicos/`):**
  - `arquivo_servico.py`: `validar_arquivo_ts_local`, `ler_informacoes_arquivo`, `sondar_duracao_arquivo`, `sondar_fluxos_midia`, `localizar_executavel_nvenc`, `resolver_candidato_executavel`.
  - `conversao_servico.py`: `converter_arquivo`, `ErroConversao`, leitura assíncrona dos pipes `stdout`/`stderr` com `CREATE_NO_WINDOW` e gravação de `<saida>_encode_<timestamp>.log`.
  - `nvenc_config_servico.py`: `verificar_ambiente_nvenc` (inspeciona `os.environ`, Registro do Windows `HKCU`/`HKLM`, `PATH`, pasta local e pasta padrão), `validar_executavel_nvenc_selecionado` (`nvenc64.exe` e `NVEncC64.exe`), `salvar_executavel_nvenc_manual` (atualiza sessão e `HKCU\Environment`) e `obter_diretorio_program_files`.
- **View (`visoes/`):**
  - `tema_visao.py`: `aplicar_tema_claro`.
  - `estilos_visao.py`: QSS da janela, zona de arraste clicável, botão `"Selecionar nvenc64"` e barra verde `#06B025`.
  - `componentes_visao.py`: `ZonaArraste` (com sinal `clicada` no botão esquerdo do mouse e cursor `PointingHandCursor`), `PainelInformacoes`, `criar_botao_selecionar_nvenc`, `exibir_caixa_mensagem` (com suporte a link HTML clicável) e `exibir_pergunta_sim_nao`.
  - `janela_principal.py`: `JanelaPrincipal` com drag & drop, seletores do Windows Explorer para `.ts` e `nvenc64` e visibilidade controlada do botão `"Selecionar nvenc64"`.
- **Controller (`controladores/`):**
  - `conversao_trabalhador.py`: `ConversaoTrabalhador` (`QObject` em `QThread`).
  - `verificador_nvenc_trabalhador.py`: `VerificadorNvencTrabalhador` (`QObject` em `QThread`) e `VerificadorNvencControlador` (orquestra a verificação inicial em segundo plano, os popups *"Sim"*/*"Não"*, o seletor em `Program Files`, o popup de download e a visibilidade exclusiva do botão `"Selecionar nvenc64"`).
  - `conversao_controlador.py`: `ConversaoControlador` (coordena seleção de `.ts` por clique ou arraste, proteção contra início sem `nvenc64`, `QTimer` de 1s e estados da janela).
- **Composição (`main.py`):** Inicializa `logging`, `QApplication`, tema claro, `ConversaoControlador` e `VerificadorNvencControlador`.

## 3. Skills Desenvolvidas no Workspace (`.agents/skills/`)
1. **`arquitetura-mvc-pyqt6`** (`.agents/skills/arquitetura-mvc-pyqt6/SKILL.md` + `scripts/validar_arquitetura.py`)
2. **`conversao-nvencc-bwdif`** (`.agents/skills/conversao-nvencc-bwdif/SKILL.md` + `references/parametros_nvencc.md`)
3. **`testes-internos`** (`.agents/skills/testes-internos/SKILL.md`)

### Skills generalistas (reutilizáveis em outros projetos)
4. **`interface-desktop-padroes`** (+ `references/padroes_pyqt6.md`): estrutura de janela, máquina de estados, drag & drop, clique + seletor de arquivos, popups, links, widgets condicionais, trabalho em segundo plano e checklist.
5. **`arquitetura-modular-codigo-limpo`** (+ `references/guia_estilo.md`, `scripts/auditar_codigo.py`): camadas, distribuição de módulos/funções, limites, nomenclatura, DI, erros/logging, extensibilidade. Auditor AST configurável via `CONFIG` e argumentos de ignorar (validado: 15 módulos, 0 violações).
6. **`estrategia-testes-modulares`** (+ `references/catalogo_testes.md`, `scripts/novo_teste.py`): pirâmide (unitário, modular, integração, arquitetura, regressão, fuzz, estresse/soak), regras de ouro, rotina pré-entrega e gerador de esqueleto de testes.
7. **`compilacao-distribuicao-executavel`** (`.agents/skills/compilacao-distribuicao-executavel/SKILL.md` + `references/padroes_compilacao_e_testes.md` + `scripts/gerar_script_compilacao.py`): generaliza o pipeline de compilação e versionamento ([scripts/compilar.py](file:///c:/Projetos/projeto%20broadcast/scripts/compilar.py)) e seus 15 testes automatizados ([tests/test_compilar.py](file:///c:/Projetos/projeto%20broadcast/tests/test_compilar.py)), cobrindo mensagens `[compilação]`, supressão de ruído do PyInstaller com diagnóstico das últimas 30 linhas na falha, `--noupx`, escrita atômica de JSON, reconciliação `build.json` → `historico.json`, bloqueio `.compilacao.lock` e suporte a `sys.frozen` com `LOCALAPPDATA`.

## 4. Resultado dos Testes Internos
- **Auditoria Arquitetural AST (`validar_arquitetura.py`):** `OK: 15 módulos auditados com 0 violações arquiteturais.`
- **Suíte de Testes (`pytest -v`):** `45 passed in 1.12s` (incluindo os 15 testes de compilação em `tests/test_compilar.py`).

## 5. Status das Etapas
- [x] Refatoração modular MVC + GUI PyQt6 base (`PROMPT.md`)
- [x] Desenvolvimento de Skills do workspace em `.agents/skills/`
- [x] Cenário 1: Verificação do `nvenc64` em segundo plano, popups guiados, botão condicional `"Selecionar nvenc64"` e persistência no ambiente do Windows
- [x] Cenário 2: Clique na zona de arraste para selecionar `.ts` no Windows Explorer e atualização do texto para `"Selecione ou arraste um arquivo .ts aqui"`
- [x] Validação arquitetural AST (15 módulos) e testes automatizados (30 testes passando)
