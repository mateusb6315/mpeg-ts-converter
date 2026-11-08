# Plano de implementação do workspace — beta 0.3

Data da revisão: **8 de novembro de 2026**. Base: commit local `6a27a8b`.
O Git estava limpo antes da análise. Este documento contém propostas; a implementação,
a compilação da beta 0.3 e a publicação ainda não foram realizadas.

## 1. Objetivo e escopo

Preparar o MPEG-TS Converter para a beta 0.3 com conversão mais robusta, scripts
separados para produção e beta, dependências coerentes, testes confiáveis,
documentação clara e um pipeline de integração e entrega verificável.

A revisão abrangeu os módulos da aplicação, os dois scripts de distribuição, os
quatro módulos de testes, os manifestos de dependências, o lockfile, o histórico Git,
os documentos versionados e os artefatos locais da beta 0.2. Não há workflows de
CI/CD nem changelogs versionados na base inspecionada. Nenhum estado remoto foi
consultado; tags, releases e configurações do GitHub precisarão ser conferidas no
momento da preparação da publicação.

Foram aplicadas as skills `codex-analise-planejamento`, `codex-casos-de-borda`,
`codex-changelogs`, `codex-otimizacao`, `codex-update-docs` e
`codex-scripts-compilacao`, incluindo seus exemplos de scripts Python. A análise
também considerou as skills locais de arquitetura MVC, conversão, compilação e testes.

### Restrições que orientam a implementação

* Manter Windows, Python 3.13, PyQt6, MVC e `main.py` como raiz de composição.
* Preservar um `.ts` por operação e o perfil TFF, BWDIF bob, HEVC Main10, preset p7,
  QVBR 18 e a cópia de áudio. Não introduzir uma opção explícita de 59,94 fps.
* Manter NVEncC externo e obrigatório e ffprobe externo e opcional. A ausência de
  sondagem deve continuar permitindo a conversão com limitações informadas.
* Preservar a pasta e o nome padrão de saída. Qualquer proteção de destino deve
  proteger arquivos existentes e informar claramente o resultado da operação.
* Preservar `prototypes/`, histórico, logs e demais artefatos locais existentes.
* Aplicar extrações por responsabilidade quando ajudarem a corrigir ou estender o
  fluxo; evitar uma migração geral para `src/` nesta beta.
* Manter os limites arquiteturais com pragmatismo: módulos próximos de 250 linhas,
  funções até 30 linhas de código, até quatro parâmetros e linhas até 100 caracteres.
* Testes com dublês e GUI offscreen não comprovam codificação real ou funcionamento
  de uma distribuição em outro Windows.

## 2. Referência atual e verificações executadas

### Ambiente e testes

| Verificação | Resultado observado nesta revisão |
| --- | --- |
| Interpretador do workspace | `.venv/Scripts/python.exe`, Python 3.13.3 |
| Bibliotecas locais | PyQt6 e Qt 6.12.0; PyQt6_sip 13.13.0; PyInstaller 6.22.3; hooks 2026.9 |
| Disponibilidade inicial de pytest | Ausente; instalado pytest 9.2.0 e suas dependências apenas na `.venv` ignorada |
| Auditoria arquitetural | 15 módulos auditados; nenhuma violação segundo as regras atuais do script |
| Suíte completa após ajuste do diretório temporário | **45 testes coletados: 36 aprovados e 9 falhas**, em aproximadamente 0,60 s reportados pelo pytest |
| Reprodução adicional | Verificações isoladas com `unittest.mock`, dados sintéticos, GUI offscreen e pastas temporárias |
| Conversão, build e publicação reais | Não executados |

O `python` disponível no PATH passa por um shim do pyenv sem versão selecionada.
Por isso, os comandos usaram explicitamente o Python da `.venv`. A primeira execução
do pytest teve 24 erros de preparação por acesso ao temporário do sandbox; esses
erros desapareceram com `--basetemp` em uma pasta nova dentro de `.pytest_cache`.
Eles não foram classificados como defeitos da aplicação.

Comandos utilizados, a partir da raiz, para a auditoria e a execução conclusiva:

```powershell
.\.venv\Scripts\python.exe .agents/skills/arquitetura-mvc-pyqt6/scripts/validar_arquitetura.py
$pastaTestesBeta03 = Join-Path '.pytest_cache' ('beta03-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -m pytest -v --tb=short --basetemp $pastaTestesBeta03
```

Use um nome novo em `--basetemp`: o pytest pode limpar o destino informado.
Não se deve apontá-lo para mídia, entregas ou uma pasta de trabalho existente.

### Distribuição local da beta 0.2

Medição feita sem modificar ou executar `prototypes/beta 0.2/` e seu ZIP.
O `build.json` informa Python 3.13.3 e PyInstaller 6.22.3; não registra o commit,
as versões de Qt ou o conjunto completo de dependências do build.

| Componente | Bytes medidos | Aproximação em MiB |
| --- | ---: | ---: |
| Pasta completa, 190 arquivos | 127.075.745 | 121,2 |
| ZIP local | 50.565.552 | 48,2 |
| `_internal/PyQt6`, incluídos os itens Qt abaixo | 72.570.225 | 69,2 |
| Traduções Qt, dentro de PyQt6 | 7.022.569 | 6,7 |
| `opengl32sw.dll`, dentro de PyQt6 | 20.639.888 | 19,7 |
| Plugins Qt, dentro de PyQt6 | 4.011.080 | 3,8 |
| `icudt78.dll`, fora da pasta PyQt6 | 33.126.192 | 31,6 |
| `python313.dll` | 6.099.960 | 5,8 |
| `p_broadcast.exe` | 1.853.386 | 1,8 |

MiB significa 1.048.576 bytes. Os subtotais de Qt se sobrepõem ao total de PyQt6;
não devem ser somados novamente para estimar economia.

O ZIP soma os mesmos 127.075.745 bytes descompactados. Seu SHA-256 medido é
`f267c6a61f70c0c099a8dd3cf6f9d9c5354e3bf17dd76f8cb1bf8cf2b71da159`.
Essa identificação não comprova sua origem no commit atual nem identidade com um
arquivo publicado remotamente.

A comparação de conteúdo por SHA-256 encontrou apenas três arquivos de tradução
idênticos de 33 bytes: economia máxima por deduplicação simples de **66 bytes**.
Não foram encontrados arquivos com `license`, `licence`, `copying` ou `notice` no
nome no pacote local. O script também não copia explicitamente a `LICENSE` do
projeto; o pacote precisa de uma etapa explícita de inclusão e conferência de licenças.

## 3. Achados e prioridades

**P0**: bloqueia a aprovação da beta 0.3. **P1**: melhoria planejada após os bloqueios,
antes do fechamento de escopo. **P2**: estudo ou evolução posterior. A prioridade
expressa a ordem de entrega; não equivale a uma escala de vulnerabilidades.

### Defeitos reproduzidos com entradas controladas

| ID | Prioridade | Evidência e efeito | Direção da correção |
| --- | --- | --- | --- |
| B01 | P0 | `tests/test_compilar.py:18` cria `Projeto Broadcast/Projeto Broadcast.exe`; `scripts/compilar.py:17` e `:184` esperam `p_broadcast/p_broadcast.exe`. Nove testes falham com “PyInstaller não gerou o executável esperado”. | Atualizar o dublê para respeitar o nome passado em `--name` e atualizar as expectativas do contrato público. Não mudar o executável para satisfazer um teste obsoleto. |
| B02 | P0 | `servicos/conversao_servico.py:70` guarda em `fluxos_origem` somente as faixas devolvidas por `selecionar_argumentos_audio`, em `modelos/conversao.py:148`. O vídeo é descartado antes da comparação A/V. Com vídeo inicial em 1 s, áudio inicial em 1 s, e saída vídeo 0 s/áudio 0,5 s, a função com fluxos completos acusa 500 ms; com a entrada efetivamente repassada pelo serviço retorna `[]`. | Conservar todos os fluxos sondados para validação e calcular os argumentos de áudio separadamente. Cobrir o serviço inteiro, além da função pura. |
| B03 | P0 | `scripts/release.py:42` combina numeração remota e maior pasta local sem vínculo. Em simulação, release remota `beta-0.2` e pasta `beta 0.8/outro.exe` produzem tag `beta-0.3`; qualquer `.exe` basta. | Exigir artefato, versão, canal e commit explícitos e correspondentes ao manifesto. Validar o executável esperado e o pacote completo. |
| B04 | P1 | `controladores/conversao_controlador.py:122` arredonda 99,9 para 100. Na GUI offscreen a barra recebeu valor 100 com texto `99,9%`, antes da conclusão. | Limitar o preenchimento a menos de 100 durante o processamento; reservar 100 ao sucesso confirmado. |
| B05 | P1 | `servicos/arquivo_servico.py:121` assume objeto JSON e lista de dicionários. `[]` causa `AttributeError`; `{"streams":[null]}` chega às regras e também causa `AttributeError`. `{"streams":null}` já cai no fallback e não reproduziu exceção. | Validar a estrutura no serviço e representar sondagem inválida como indisponível, preservando o fallback de áudio. |
| B06 | P1 | `modelos/conversao.py:226` envolve todas as faixas em um único `try`. Com `start_time="N/A"` na primeira faixa, uma divergência de 1 s na segunda não foi reportada. | Tratar ausência e valores não finitos por faixa; prosseguir com as demais e distinguir “não verificável” de “sem divergências”. |

### Problemas confirmados na estrutura; consequências condicionais

Os caminhos abaixo foram conferidos no código. Onde indicado, houve reprodução
com dublês, sem atribuir o comportamento a uma execução real do NVEncC.

| ID | Prioridade | Evidência, pré-condição e risco | Implementação proposta |
| --- | --- | --- | --- |
| R01 | P0 | `_preparar_interface_para_conversao`, em `controladores/conversao_controlador.py:161`, chama `_ler_informacoes` antes de iniciar o worker. A composição injeta `ler_informacoes_arquivo`, que executa ffprobe síncrono com timeout de 10 s. Uma sondagem lenta bloqueia a thread da GUI; a duração é sondada novamente pelo serviço. Não foi medido congelamento com mídia real. | Sondagem em worker, resultado reutilizado e estado PREPARANDO; nenhum subprocesso ou stat potencialmente lento no fluxo principal da GUI. |
| R02 | P0 | `cancelar_conversao_ativa` aguarda 5 s na GUI e ignora o retorno de `wait`; a verificação inicial espera 2 s com o mesmo problema. A sondagem anterior ao Popen não consulta cancelamento. Um evento já sinalizado ainda alcançou a função de execução do processo em dublê. | Cancelar preparação, execução e validação; fechamento assíncrono; aguardar sinais de término antes de liberar objetos e permitir fechar. |
| R03 | P0 | `_consumir_fila_saida` termina quando os dois pipes chegam ao EOF; depois `_executar_processo_nvenc` chama `wait()` sem timeout. Uma fila com ambos os EOF retornou mesmo com `poll() is None` no dublê. Um processo vivo nessa situação deixa de receber verificação de cancelamento. | Monitorar vida do processo e pipes separadamente; espera limitada e cancelável, com escalonamento de encerramento e coleta dos leitores. |
| R04 | P0 | O destino é determinístico e vai diretamente ao NVEncC, sem política de colisão, reserva ou distinção de parcial. O serviço não verifica a existência da saída após exit code zero: com processo falso de retorno 0 houve sucesso sem arquivo. A reação real do codificador a destino existente não foi testada. | Recusar colisão por padrão, proteger contra duas instâncias e gravar em arquivo temporário único no volume de destino. Promover a saída somente após as verificações mínimas. |
| R05 | P1 | O log de codificação é gravado somente depois de `_executar_processo_nvenc`. Uma exceção simulada de cancelamento deixou zero logs. Listas de stdout/stderr e a fila não têm limite global; `read(1)` cria uma entrada por byte. O limite de 32 KiB protege apenas o segmento. | Log incremental e finalização garantida, leitura em blocos, fila com política de limite e diagnóstico limitado em memória. Medir CPU/RSS antes e depois. |
| R06 | P0 | `scripts/release.py:76` não vincula a tag a um SHA explícito e não pede marcação de pré-release no comando de criação. Retomada aceita asset apenas pelo nome; uma nova execução de `principal` recalcula a próxima tag e pode abandonar a tentativa anterior. Não há testes desse script. | Publicação explícita e retomável do mesmo manifesto, pré-release para beta, identidade do asset por tamanho/hash e commit verificado. |
| R07 | P0 | `scripts/compilar.py:143` empacota `main.py` sem etapa explícita para licença, instruções, dependências e inventário; o pacote beta 0.2 local não apresenta arquivos de licença nomeados. | Empacotar licença do projeto e avisos/licenças aplicáveis das dependências; validar conteúdo obrigatório antes de entregar. Conferir termos antes de distribuir. |
| R08 | P1 | `requirements.txt` usa PyQt6 >=6.5 e inclui pytest; pyproject usa PyQt6 >=6.12,<7 e não declara pytest. `poetry.lock` contém apenas dependências de execução. Instalações pip e Poetry não têm o mesmo contrato de desenvolvimento. | Fonte única de dependências, grupos de execução/desenvolvimento/build e instalações verificadas em ambiente limpo. |
| R09 | P1 | `pyproject.toml` mantém versão 0.1.0, nome interno antigo, descrição vazia e autor de exemplo. `build.json` não contém commit, canal, hashes, versões completas ou estado sujo do Git. A interface usa Projeto Broadcast. | Identidade e versão coerentes, com compatibilidade dos nomes e caminhos legados documentada. Não deduzir autoria além da evidência existente. |
| R10 | P1 | O auditor enumera manualmente 15 arquivos e não cobre `scripts/` ou novos módulos automaticamente. Também não demonstra ausência de I/O no model, português dos nomes ou responsividade. `scripts/compilar.py` tem 261 linhas, fora da lista auditada. | Descoberta automática das camadas, contratos arquiteturais e lint complementar, sem apresentar o auditor como prova integral da arquitetura. |
| R11 | P1 | O teste denominado integração interna chama workers diretamente e substitui trechos do controlador; não exercita um ciclo completo QThread + Popen. O teste de seleção manual altera `os.environ` pelo serviço sem preparar a variável com monkeypatch. | Isolar ambiente e adicionar testes de ciclo de vida Qt e processo controlado, com prazo máximo e ausência de dependência de ordem. |

### Hipóteses a investigar, sem falha real comprovada

| ID | Prioridade | Condição e investigação necessária |
| --- | --- | --- |
| H01 | P0 | A janela é liberada antes da limpeza final do worker; sinais em fila e popups modais permitem reentrância. Verificar se uma seleção rápida ou evento atrasado de uma operação pode limpar referências da seguinte. Bloquear nova operação até término efetivo e identificar a execução nos sinais. |
| H02 | P0 | Fechamento durante descoberta inicial ou sondagem longa pode destruir QThread ativa ou deixar subprocesso vivo. Reproduzir em processo isolado para evitar derrubar a sessão de teste. |
| H03 | P1 | Falha de criação do log da aplicação em `_configurar_logging` pode impedir a abertura da GUI. Testar permissão negada, disco cheio e indisponibilidade da pasta; definir fallback e mensagem útil. |
| H04 | P1 | A detecção inicial não tem estado explícito compartilhado; o bloqueio de seleção depende da visibilidade do botão, inicialmente oculto. Verificar recebimento de `.ts` antes de concluir a busca e erro tardio de descoberta durante outra operação. |
| H05 | P1 | TS multiprograma, PTS negativo, faixas surgindo tardiamente, fonte BFF/progressiva e mídia truncada podem exigir avisos ou revelar limites do perfil. Avaliar com corpus real, sem alterar automaticamente o perfil ou as faixas. |

## 4. Organização proposta para o workspace

Manter as camadas atuais e extrair responsabilidades conforme cada etapa as exigir.
Os caminhos abaixo são propostas; arquivos novos só devem surgir com necessidade
concreta e testes correspondentes.

```text
main.py                         composição e injeção dos serviços/controladores
config/                         perfil fixo, interface e identidade/versão
modelos/
  conversao.py                  contratos públicos e regras do fluxo
  progresso.py                  parser e cálculos, quando extraídos
  audio.py                      seleção e validação pura das faixas
  midia.py                      dados tipados de sondagem e resultado
servicos/
  arquivo_servico.py            arquivos e validação de entrada/saída
  sondagem_servico.py           ffprobe e normalização de metadados
  localizacao_executaveis.py    descoberta de ferramentas
  conversao_servico.py          orquestração da conversão sem Qt
  processo_nvenc_servico.py     subprocesso, pipes e cancelamento
  log_conversao_servico.py      registro incremental e diagnóstico
controladores/                  estados, workers e encerramento Qt
visoes/                         componentes, mensagens e callbacks injetados
utilitarios/                    somente formatação pura
scripts/
  compilar.py                   entrada de produção com versão explícita
  compilar_beta.py              entrada de beta/testes locais
  release.py                    publicação do artefato explicitamente selecionado
  distribuicao/                 núcleo compartilhado de build e validação
tests/
  unitarios/                    regras puras e parsers
  servicos/                     subprocessos e arquivos controlados
  interface/                    ciclo Qt offscreen
  distribuicao/                 build, manifesto, ZIP e release simulada
docs/                           plano, arquitetura, testes e distribuição
changelog/                      notas verificadas por versão
.github/workflows/              integração e preparação/publicação separadas
```

Fluxo de dependências preservado: views recebem dados e callbacks; controladores
coordenam modelos e serviços; serviços não importam Qt; modelos não fazem I/O.
O núcleo de distribuição fica em `scripts/`, sem imports da interface para obter
nome ou versão. Evitar hierarquias genéricas de plugins e abstrações sem dois usos reais.

Extrair `arquivo_servico.py` e `conversao_servico.py` junto das correções de sondagem e
processo. Extrair áudio/progresso quando os novos contratos exigirem espaço. Não é
necessário mover todos os testes existentes de uma vez; preservar descoberta e
comandos durante a transição. Imports públicos antigos podem ter adaptadores
temporários curtos, removidos depois de migrar todos os consumidores.

### Contratos e estados a tornar explícitos

* `MetadadosMidia`: duração opcional, todos os fluxos normalizados e condição da
  sondagem; distinguir indisponível, sem áudio e inválida sem confundir as situações.
* `ResultadoConversao`: caminho final, caminho do log, avisos e verificações que não
  puderam ser realizadas. Sucesso de processo não equivale sozinho a sucesso de arquivo.
* Estados: VERIFICANDO_AMBIENTE → AGUARDANDO → PREPARANDO → CONVERTENDO →
  VALIDANDO → CONCLUIDA/FALHOU/CANCELADA → AGUARDANDO, após liberar os recursos.
* CANCELANDO/ENCERRANDO impedem nova seleção. Cada operação tem uma identidade;
  sinais de operações anteriores não alteram o estado atual.
* A GUI transmite a intenção de cancelar ou fechar; o controlador só confirma o
  fechamento após término dos workers e subprocessos. Não usar `QThread.terminate()`.
* A sondagem continua opcional. Falha no ffprobe não deve remover a estratégia de
  fallback de áudio nem transformar ausência de validação em declaração de integridade.

## 5. Plano de execução por etapas

### Etapa 1 — Restabelecer a referência de desenvolvimento

**Prioridade:** P0 para B01; P1 para a padronização. **Depende de:** nenhuma etapa.

1. Corrigir dublê e expectativas obsoletas de build, preservando as verificações de
   bloqueio, histórico, atomicidade e recuperação.
2. Corrigir isolamento da variável `nvenc64` nos testes; criar fixture Qt com ciclo
   de vida explícito e timeouts para testes assíncronos.
3. Unificar o contrato das dependências em `pyproject.toml`, com grupos de dev/build;
   gerar requirements coerentes e documentar a política de atualização do lockfile.
   Recomenda-se manter pip como caminho simples e Poetry como alternativa validada.
4. Separar pytest das dependências de execução. Fixar o ambiente de distribuição,
   incluindo hooks do PyInstaller, e verificar instalação de cada grupo em ambiente novo.
5. Configurar lint/formatação e pytest no pyproject, sem usar correção automática
   ampla antes de separar as alterações funcionais.

**Arquivos:** `tests/test_compilar.py`, `tests/test_integracao_interna.py`,
`pyproject.toml`, `poetry.lock`, `requirements*.txt` e documentação de desenvolvimento.

**Aceite:** os 45 testes existentes passam por motivos corretos; nenhum teste depende
do ambiente deixado por outro; pip e Poetry instalam ferramentas de desenvolvimento
equivalentes. Um teste de ausência do executável continua falhando no caso apropriado.

**Riscos e recuperação:** resolver versões pode mudar Qt; separar essa mudança de
qualquer otimização do pacote e preservar a referência da beta 0.2 para comparação.

### Etapa 2 — Corrigir sondagem, áudio e progresso

**Prioridade:** P0/P1. **Depende de:** etapa 1.

1. Corrigir B02 preservando os fluxos completos até a validação final. Testar a cadeia
   `converter_arquivo` → seleção de áudio → validação com deslocamento conhecido.
2. Normalizar JSON, valores ausentes, duração inválida e horários por faixa no serviço.
   Cobrir B05/B06 e valores NaN/infinito sem gerar falsos “sem divergências”.
3. Mover toda a coleta de metadados para worker e reutilizar o resultado na conversão.
   Preferir uma consulta ffprobe com duração e fluxos, após testar o fallback.
4. Introduzir PREPARANDO e VALIDANDO; definir resposta ao cancelamento em cada fase.
5. Corrigir B04 e manter progresso monotônico. Duração ausente deve produzir estado
   honesto de progresso indeterminado ou usar o percentual emitido pelo codificador.
6. Preservar o comando fixo com teste de contrato completo dos argumentos, incluindo
   faixas, perfil e ausência de argumento explícito de taxa de saída.

**Arquivos:** modelos de mídia/áudio/progresso, `servicos/arquivo_servico.py`, serviço
de sondagem, `servicos/conversao_servico.py`, workers, controlador e textos da view.

**Aceite:** divergência sintética de 500 ms é reportada pelo fluxo do serviço;
uma faixa inválida não impede verificar outra; ffprobe ausente ou inválido permite o
fallback; uma sondagem simulada de 2 s não bloqueia o processamento de eventos Qt;
a barra nunca preenche 100 antes de confirmar a conclusão.

**Riscos e recuperação:** preservar as amostras de parser atuais e comparar o comando
antes/depois. A validação por `start_time` é limitada: não comprova sincronia ao longo
de todo o vídeo. Manter essa limitação nos textos e no roteiro de mídia real.

### Etapa 3 — Tornar execução, saída e encerramento seguros

**Prioridade:** P0. **Depende de:** etapa 2 e contratos de estado.

1. Consultar cancelamento antes/depois de cada fase e antes de criar subprocessos.
   Sondagem em andamento deve terminar por timeout curto definido ou ser interrompível.
2. Centralizar o ciclo do processo: criação, leitura, EOF, retorno, cancelamento,
   timeout de encerramento e liberação de leitores. Não impor um timeout total curto
   à conversão de vídeos longos; limitar esperas de encerramento.
3. Retirar `wait()` bloqueante da GUI e verificar resultados de término. Conectar a
   limpeza de QObject/QThread aos sinais corretos e impedir reentrada até concluí-la.
4. Definir reserva exclusiva do destino entre instâncias. Detectar colisão no serviço,
   mesmo quando a interface tiver feito uma verificação prévia.
5. Gravar em arquivo temporário único com extensão `.mkv`, no mesmo volume; validar
   existência/tamanho antes da promoção sem substituição do destino. Sondagem final
   continua opcional e seus avisos não serão transformados silenciosamente em erro.
6. Em falha ou cancelamento, identificar o parcial e oferecer seu caminho. Limpar
   apenas arquivos pertencentes à operação, conforme política documentada; nunca
   remover ou truncar um resultado anterior ou a mídia de entrada.
7. Gravar log desde o início, com identificador único, fases e desfecho, incluindo
   falhas de Popen e cancelamento. Definir fallback quando a pasta não aceitar log.

**Arquivos:** serviços de processo, conversão, arquivos e log; workers/controladores;
`JanelaPrincipal.closeEvent`; composição em `main.py`.

**Aceite:** fechar durante preparação, conversão, validação e busca de NVEncC não deixa
QThread ativa nem processo órfão; cancelamento antes do início não chama Popen;
EOF antes do término continua cancelável; exit code 0 sem saída é falha; duas
instâncias no mesmo destino não sobrescrevem arquivos. Sucesso/erro é emitido uma
única vez e uma segunda operação começa somente após limpeza da anterior.

**Riscos e recuperação:** interrupção forçada pode impedir finalizar MKV; preservar
diagnóstico e testar com processo controlado e mídia real. Validar rename, locks e
permissões em NTFS; caminhos UNC precisam de teste separado e não de promessa implícita.

### Etapa 4 — Separar build de produção, beta e publicação

**Prioridade:** P0 para identidade/licenças/publicação; P1 para ergonomia.
**Depende de:** etapas 1–3 para gerar um candidato confiável.

Adotar duas entradas finas com um núcleo compartilhado. Produção e beta usam o mesmo
perfil de conversão e as mesmas verificações de integridade.

| Operação proposta | Entrada | Versão e destino | Efeito externo |
| --- | --- | --- | --- |
| Teste local | `scripts/compilar_beta.py` | ID local único em `prototypes/testes/<id>/` | Nenhum |
| Candidato à beta pública | `scripts/compilar_beta.py --versao 0.3 --candidata` | `prototypes/beta 0.3/`, sem sobrescrever | Nenhum |
| Distribuição estável | `scripts/compilar.py --versao X.Y.Z` | `dist/producao/X.Y.Z/`, sem sobrescrever | Nenhum |
| Conferência de release | `scripts/release.py --artefato <pasta> --verificar` | Lê manifesto e prepara relatório | Somente leitura remota, se solicitada |
| Publicação | `scripts/release.py --artefato <pasta> --publicar` | Tag derivada e validada contra manifesto | Cria/retoma release com autorização específica |

Essas interfaces ainda não existem. `X.Y.Z` e `<pasta>` são campos ilustrativos,
não comandos prontos. A primeira versão estável será decidida separadamente.

1. Compartilhar validação, montagem do comando PyInstaller, staging, bloqueio,
   mensagens, diagnóstico de falha, empacotamento e manifesto em `scripts/distribuicao/`.
   Preservar `--onedir`, `--windowed`, `--noupx` e diagnóstico das últimas 30 linhas.
2. Exigir Windows e Python suportado; registrar ferramentas e ambiente. Tratar
   variáveis Qt/Python conflitantes com política explícita e testada, sem mutilar PATH.
3. Adicionar ao pacote `LICENSE`, instruções curtas, avisos/licenças necessários e
   inventário das dependências incluídas. Não incluir NVEncC/ffprobe nesta beta.
4. Registrar no manifesto versionado por esquema: produto, versão, canal, commit,
   estado do Git, data com fuso, Python/Qt/PyQt6/PyInstaller/hooks, dependências,
   parâmetros de empacotamento, tamanho e hashes do conteúdo. O manifesto não inclui
   seu próprio hash; checksum do ZIP é gerado depois em arquivo separado.
5. Preservar histórico e reconciliação. Isolar testes locais do histórico de versões
   públicas e suportar leitura dos manifests antigos sem reescrevê-los automaticamente.
6. Reservar destinos e publicar a pasta local sem substituição. Conflito de pasta,
   ZIP ou checksum deve falhar de modo claro, sem apagar entregas existentes.
7. Substituir seleção automática da maior pasta por seleção explícita. Para beta 0.3,
   exigir correspondência entre `0.3`, `beta 0.3` e `beta-0.3`, além do SHA aprovado.
8. Criar e conferir a release como rascunho/pré-release no fluxo apropriado, com notas
   reais e referência ao commit validado. Retomar a mesma tag após falha parcial;
   conferir tamanho/hash dos assets e recusar conflito em vez de aceitar só o nome.
9. Testar CLI, ZIP, metadados inválidos, concorrência, timeout, falha de upload e
   recuperação com dublês. Build real e smoke test entram no aceite da entrega.

**Migração:** `python scripts/compilar.py` hoje gera beta automaticamente. Ao transformar
essa entrada em produção, uma chamada sem versão deve informar o novo comando e
encerrar sem gerar nem publicar nada. Documentar a mudança. Preservar o histórico
antigo como referência; não renumerar versões existentes para adequar o novo fluxo.

**Aceite:** teste local não consome número público; nenhuma compilação publica no
GitHub; versão divergente é rejeitada; pacote exige o executável certo e recursos;
queda entre rename e histórico é reconciliada; repetição de publicação não cria
outra versão nem substitui asset de conteúdo diferente.

**Riscos:** retentativas de rede têm resultados ambíguos; sempre consultar o estado
antes de agir novamente. A disponibilidade de `beta-0.3` só será conhecida ao consultar
o remoto; se ocupada, interromper a preparação e decidir a versão sem sobrescrever tag.

### Etapa 5 — Otimizar com referência e experimentos isolados

**Prioridade:** P1 para I/O/log/sondagem; P2 para remoções arriscadas do runtime.
**Depende de:** etapas 2–4 e build comparável.

| Proposta | Base/benefício esperado | Validação e decisão |
| --- | --- | --- |
| Reutilizar a sondagem | Hoje a duração é solicitada no controlador e no serviço. Reduz chamadas e espera; não há ganho de tempo medido. | Contar chamadas por operação e medir início da conversão com ffprobe presente/ausente. |
| Ler saída por blocos e limitar memória | Hoje há item na fila por byte e logs acumulados até o fim. Benefício de CPU/RSS é hipótese fundamentada na implementação. | Replay de saída com CR/LF, Unicode e alto volume; medir CPU, pico de RSS, progresso e cancelamento. |
| Selecionar traduções Qt necessárias | 99 arquivos, 7.022.569 bytes no artefato atual. Esse total é teto bruto de oportunidade, não economia prometida. | Definir idioma dos diálogos Qt, manter recursos necessários e testar seletores/mensagens no Windows. Medir diferença real no ZIP. |
| Auditar plugins não usados | Plugins somam 4.011.080 bytes; parte é obrigatória ou carregada dinamicamente. | Rastrear uso e testar plataforma Windows, diálogos, links, formatos, DPI e fallback. Preservar plugins de teste no ambiente de teste. |
| Investigar OpenGL por software | `opengl32sw.dll` tem 20.639.888 bytes. Não há prova de que possa ser removida com segurança. | Experimento separado com diferentes GPUs/sessões remotas; manter no candidato padrão até demonstrar compatibilidade. |
| Investigar ICU e bibliotecas nativas | ICU de dados representa 33.126.192 bytes; tamanho não comprova inutilidade. | Verificar dependências nativas/dinâmicas. Não remover por filtro de nome nem trocar runtime Qt nesta beta sem validação própria. |
| Comparar compressão ZIP | ZIP atual tem 50.565.552 bytes. Alterar nível pode trocar tempo de build por tamanho. | Usar o mesmo conteúdo e medir tempo/bytes; manter extração padrão do Windows e integridade. |

Protocolo: build de referência e variante no mesmo Windows, arquitetura e ambiente
de dependências; medir bytes extraídos e compactados, duração de build/inicialização,
CPU/RSS do processamento de logs e funções críticas. Somar apenas economias
incrementais não sobrepostas. Registrar método e arquivos alterados no relatório.

**Aceite:** nenhuma otimização entra no candidato sem smoke test e teste real das
funções afetadas. Não há meta percentual de redução fixada: ganhos precisam ser
medidos. Reverter filtros de empacotamento se houver regressão; não usar UPX nem
remover verificações, licenças ou diagnósticos para reduzir o pacote.

### Etapa 6 — Entregar melhorias visíveis com escopo controlado

**Prioridade:** P1. **Depende de:** etapas 2–3; não bloqueia correções P0.

| Feature proposta | Necessidade | Critério de aceite |
| --- | --- | --- |
| Estados de preparação, validação e cancelamento | O usuário precisa entender esperas sem progresso do encoder. | Textos distintos e responsivos; não aceitar segunda entrada enquanto houver recursos ativos. |
| Resultado com caminho de saída/log e avisos | Hoje a conclusão mostra somente mensagem genérica e divergências ficam no log. | Distinguir sucesso com avisos, sondagem indisponível e falha; permitir localizar o resultado por ação injetada, sem expor detalhes internos desnecessários. |
| Diagnóstico das ferramentas | A descoberta atual aceita existência/nome, sem demonstrar capacidade de codificação. | Relatório com caminho/versão detectados, ffprobe disponível e orientação útil; verificação lenta em worker, sem prometer compatibilidade da GPU apenas pela presença do `.exe`. |
| Aviso sobre o perfil de entrada | A aplicação aplica TFF/bob a qualquer `.ts`. | Explicar o perfil e, quando houver metadados suficientes, avisar incompatibilidade provável; nunca selecionar outro perfil silenciosamente. |

Botão de cancelar sem fechar a janela e seleção de pasta de saída são candidatos
opcionais, sujeitos a uma decisão de interface e revisão das regras de tamanho da
janela. Não condicionam a beta 0.3. Fila/lote, presets de qualidade, novos codecs,
atualização automática e inclusão de binários externos ficam para outra versão.

Validar interface clara, teclado, foco, nomes longos, escala 100/125/150/200%, mensagens
e links no Windows. Não aproveitar a beta para um redesenho amplo sem evidência de necessidade.

### Etapa 7 — Implantar integração contínua e entrega rastreável

**Prioridade:** P1; validações obrigatórias para aprovar o candidato.
**Depende de:** etapa 1 para CI; etapa 4 para artefatos.

1. Criar `.github/workflows/ci.yml` para push/PR com runner Windows e Python 3.13:
   instalação coerente com o lock, auditoria arquitetural, lint, suíte offscreen,
   testes de build/release simulados e relatório de resultados. Separar logs por job.
2. Tornar o auditor capaz de descobrir novos módulos e verificar dependências por
   camada. Como `.agents/` é área protegida no workspace atual, planejar essa edição
   com o mecanismo de permissão aplicável ou criar uma verificação complementar em
   `scripts/` sem enfraquecer a auditoria existente.
3. Criar workflow de build manual/candidato com Windows e versão explícita. Gerar
   pacote, manifesto, checksums, inventário/licenças e relatório de tamanho. Anexar
   artefatos ao job; produzir build não significa publicar release.
4. Acrescentar smoke test do executável em processo isolado, com prazo máximo e
   encerramento controlado. Considerar `--smoke-test` dedicado que exercite imports,
   inicialização Qt e recursos sem iniciar conversão nem alterar o Registro.
5. Separar workflow de publicação, com referência exata ao artefato/commit aprovado.
   A publicação deve promover o mesmo pacote validado, sem recompilação invisível.
6. Usar permissões mínimas: jobs de PR/teste sem escrita e sem segredos de publicação;
   credencial de escrita apenas no job autorizado. Fixar ações por revisão aprovada,
   definir timeouts, cache por lock e concorrência por canal/versão.
7. Manter validação GPU manual como requisito documentado. Runner hospedado sem o
   hardware necessário não pode atestar qualidade, sincronia ou velocidade do NVEncC.
   Runner próprio, caso desejado depois, exige desenho operacional separado.

**Aceite:** clone limpo executa CI sem estado de `prototypes/`; falha de teste bloqueia
aprovação do candidato; duas execuções não publicam a mesma versão; PR não publica;
checksums conferem após baixar os artefatos; o SHA e as notas correspondem ao pacote.

**Riscos:** regras de proteção e disponibilidade dos runners dependem da configuração
remota ainda não inspecionada. Consultar documentação oficial atual de GitHub Actions,
GitHub CLI, PyInstaller e ferramentas de dependências ao implementar os workflows.

### Etapa 8 — Reconciliar documentação e fechar a beta

**Prioridade:** P1, obrigatória para entrega. **Depende de:** resultados das demais etapas.

| Documento | Atualização proposta |
| --- | --- |
| `README.md` | Requisitos/instalação coerentes, comportamento realmente entregue, comandos novos de build, diferenças entre teste/candidato/produção, logs, colisões e limitações. |
| `AGENTS.md` | Orientações duráveis, arquitetura e verificações atuais; sem autorização permanente para publicação. |
| `MEMORY.md` | Decisões e contratos persistentes verificados, remetendo ao código; evitar registrar cada execução de teste como fato durável. |
| `PROMPT.md` | Identificar como documento histórico ou reconciliar instruções antigas que conflitam com o fluxo atual, evitando duas especificações normativas. |
| `docs/arquitetura.md` | Fluxo de estados, direção das dependências, cancelamento e pontos de extensão reais. |
| `docs/distribuicao.md` | Build limpo, metadados, destinos, recuperação, licenças, verificação e publicação explícita. |
| `docs/testes.md` | Camadas de validação, corpus manual, comandos e limites dos dublês/offscreen. |
| `changelog/beta 0.3.md` | Somente mudanças concluídas, medidas verificadas e problemas conhecidos confirmados no candidato. |

Não há convenção de changelog versionada para preservar. Recomenda-se o formato da
skill solicitada: `## Notas da versão beta 0.3 do MPEG-TS Converter`, itens `* ` com
efeitos para o usuário e, quando necessário, `## Problemas conhecidos:`. Este plano
não é uma nota de versão e não deve ser publicado como lista de melhorias concluídas.

**Aceite:** links/caminhos locais válidos, comandos copiados de um clone limpo,
nenhuma funcionalidade planejada descrita como disponível e nenhuma porcentagem de
otimização sem medição. Licença MIT e nomes/caminhos legados devem permanecer coerentes.

## 6. Matriz mínima de casos de borda e validação

| Cenário / pré-condição | Resultado esperado e consequência evitada | Evidência exigida |
| --- | --- | --- |
| NVEncC ausente, removido após detecção ou executável inválido | Erro recuperável, sem sucesso falso e sem perder a possibilidade de configurar ferramenta. | Serviço com dublês + Windows real para seleção/persistência. |
| ffprobe ausente, timeout, saída vazia/JSON inválido, duração zero/NaN | Conversão usa fallback; UI informa o que não foi verificado. | Testes parametrizados e execução real sem ffprobe no PATH. |
| `.TS`, múltiplos arquivos, diretório `.ts`, arquivo vazio, removido após seleção | Entrada válida segue; inválidas são recusadas ou falham com diagnóstico, sem estado travado. | Regras/serviço + eventos reais de arraste na GUI. |
| Origem sem leitura, destino sem escrita, disco cheio | Falha clara, log/fallback quando possível e arquivos anteriores preservados. | Falhas injetadas; teste real em diretório isolado com permissões controladas. |
| Destino existente ou duas instâncias para a mesma origem | Nenhuma substituição silenciosa; exclusão mútua e diagnóstico de colisão. | Dois processos isolados e conferência de hash do arquivo original. |
| Espaços, acentos, nomes longos e caminho UNC | Argumentos íntegros; erro explicativo quando o ambiente não suportar o caminho. | Testes de argumentos + Windows/NTFS; UNC apenas se houver ambiente disponível. |
| Sem áudio, várias faixas, layout ausente, PTS negativo e faixa inválida | Cópia conforme contrato, validação por faixa; indisponibilidade distinguida de equivalência. | Dados sintéticos + TS reais de referência com inspeção antes/depois. |
| Fonte progressiva/BFF ou TS multiprograma | Aviso coerente e nenhum ajuste silencioso do perfil; documentar limites encontrados. | Sondagem e corpus real, sem alegar suporte universal. |
| stdout/stderr com CR, LF, EOF sem newline e volume alto | Parser estável, log útil, memória controlada e cancelamento responsivo. | Processo auxiliar controlado e replay com métricas. |
| Processo silencioso, pipes fechados com processo vivo, erro de leitura | Cancelamento continua funcionando; término e limpeza têm limite verificável. | Processo auxiliar real, sem GPU, executado com timeout externo de proteção. |
| Fechar/cancelar em cada fase e repetir rapidamente | Um desfecho por operação, sem órfãos, sem sinal antigo afetar a nova operação. | Event loop Qt real em subprocesso de teste; smoke manual do `.exe`. |
| PyInstaller falha, retorna sem `.exe`, interrupção antes/depois do rename | Não consumir versão incompleta; reconciliar entrega concluída; preservar histórico inválido. | Dublês e testes do filesystem/bloqueio, incluindo interrupção isolada. |
| Build de teste repetido e candidato existente | Teste não consome versão pública; candidato não é sobrescrito. | Testes das duas entradas e manifesto. |
| Release/tag já existente, upload parcial, timeout, asset diferente com mesmo nome | Retomar a identidade correta ou falhar; nenhuma nova versão ou substituição implícita. | GitHub CLI simulado; conferência remota só na operação autorizada. |
| Windows sem Python/Qt/NVEncC globais, tela com DPI alto | Executável inicia; ausência da ferramenta externa é tratada; controles legíveis. | Máquina/VM limpa e smoke do ZIP extraído. |

A cobertura será orientada pelo risco dessas mudanças. Não é necessário criar testes
que apenas repitam a implementação ou exigir GPU de testes unitários. Testes reais
com processos controlados cobrem I/O e ciclo de vida; ainda não substituem mídia/GPU.

## 7. Dependências, decisões e ordem de entrega

Ordem recomendada: **1 → 2 → 3 → 4 → 5/6/7 → 8 → candidato → validação real**.
A parte inicial de CI da etapa 7 pode começar após a etapa 1. Otimização arriscada
não deve atrasar correção de dados, cancelamento ou identidade do pacote.

Dividir a implementação em mudanças revisáveis: referência de testes/dependências;
sondagem/áudio; processo/saída; distribuição; CI; melhorias de interface; documentação.
Cada uma deve registrar teste, risco e mudança de comportamento. Uma extração
arquitetural deve acompanhar o problema que resolve, sem misturar uma reformatação
global com correções de concorrência.

| Decisão | Recomendação inicial | Quando resolver |
| --- | --- | --- |
| Versão pública e versão de máquina | Público `beta 0.3`, tag `beta-0.3`; mapear explicitamente para versão de máquina, por exemplo `0.3.0b1`, e atualizar os metadados coerentemente. | Antes da etapa 4; validar formato aceito pelas ferramentas escolhidas. |
| Compatibilidade do executável | Preservar `p_broadcast.exe` nesta beta e exibir nome/versão do produto na interface e manifesto. Planejar renomeação separada. | Etapa 4. |
| Política de colisão | Recusar destino existente e preservar resultado; eventual substituição deve ser uma ação explícita futura. | Etapa 3. |
| Tratamento de parciais | Manter identificados em falha/cancelamento com caminho visível; remoção posterior explícita. | Etapa 3. |
| Diretório de log legado | Preservar `%LOCALAPPDATA%\Projeto Broadcast` até haver migração definida; evitar perder diagnósticos ao mudar a identidade visual. | Etapa 6. |
| Features opcionais | Adiar botão de cancelar e seletor de saída se ampliarem o redesenho; corrigir fechamento/cancelamento independentemente. | Antes de congelar o candidato. |
| Licenças e assinatura | Incluir licenças/inventário como requisito; avaliar assinatura de código separadamente, sem declarar um artefato assinado antes de verificá-lo. | Inventário na etapa 4; assinatura pode ser P2. |

Essas recomendações tornam o plano executável, mas continuam propostas. Não há
estimativa de prazo nem promessa de economia de tamanho: faltam implementação,
medição comparável e validação em hardware representativo.

## 8. Critérios para aprovar o candidato beta 0.3

* [ ] B01, B02, B03 e todos os itens P0 corrigidos e cobertos no nível adequado.
* [ ] Hipóteses P0 investigadas; falhas encontradas corrigidas, sem tratá-las como
  descartadas apenas porque testes com dublês passaram.
* [ ] Auditoria, lint e suíte completos aprovados, com dependências reproduzíveis.
* [ ] Build beta/teste e produção compartilham núcleo e mantêm destinos/metadados isolados.
* [ ] Artefato identificado por versão/canal/commit; licença, inventário e hashes presentes.
* [ ] ZIP extraído inicia em Windows limpo; seleção, falha e cancelamento funcionam.
* [ ] Conversões reais com mídia 60i/TFF, múltiplas faixas e caso sem áudio; verificar
  HEVC Main10, comportamento bob, faixas/canais e sincronia em trechos no início,
  meio e fim. Registrar GPU, driver, NVEncC, ffprobe e identificação das amostras.
* [ ] Teste real sem ffprobe confirma o comportamento degradado esperado.
* [ ] Saída anterior preservada em colisão; cancelamento não deixa processos órfãos.
* [ ] Métricas de tamanho/startup/memória comparadas pelo mesmo método; somente
  otimizações validadas presentes no pacote.
* [ ] README, memória e notas da versão descrevem o candidato efetivamente testado.
* [ ] Correspondência local/remota de `beta 0.3`/`beta-0.3` conferida no momento apropriado.
* [ ] Publicação executada somente após solicitação/autorização específica, com
  promoção do mesmo artefato validado e conferência dos assets remotos.

## 9. Limites da entrega original de planejamento

Somente este plano foi criado no conteúdo versionável. Não foram alterados código,
testes, versões, lockfiles, README, memória, regras de agente ou artefatos de beta.
A preparação local instalou pytest na `.venv` ignorada e gerou temporários/caches de teste.
Não houve commit, push, build real, publicação ou alteração remota.

As reproduções adicionais usaram entradas sintéticas e dublês. Não demonstram
incidência dos cenários com um NVEncC real. A auditoria aprovada cobre apenas os
15 arquivos explicitamente listados atualmente. A suíte permanece com nove falhas
documentadas, pois este pedido autoriza revisão e plano, sem implementar as correções.

## Atualização de implementação

O pedido posterior definiu input manual nos dois compiladores, beta sem restrição
X.Y.Z e convenção recomendada 0.0.3-beta1. Essa decisão substitui os exemplos de
numeração/destinos acima. Consultar docs/distribuicao.md para os comandos implementados.
A implementação não constitui aprovação do candidato: métricas de GPU, teste em
Windows limpo e otimizações condicionais do runtime continuam exigindo validação real.

### Estado após a implementação local

Implementados: correções B01–B06; metadados da GUI em worker; encerramento assíncrono
da conversão; reserva/saída parcial; logs e fila limitados; núcleo de build, input
manual nos dois compiladores, versões beta livres; manifesto/licenças; isolamento
PATH; verificação explícita e rascunho de release; dependências/lock reconciliados;
CI e build manual; documentação e notas locais. Testes adicionais cobrem I/O,
QThread, cancelamento, CLI e adulteração.

Pendências do plano: unificar a sondagem de duração ainda duplicada; relatório visual
de avisos A/V e diagnóstico de ferramentas; detecção de perfil de fonte; retomar
publicação remota existente com prova de identidade; regras remotas de proteção e
execução dos workflows; lint além da auditoria arquitetural; validação em Windows
limpo/GPU/corpus real. Remoções de plugins, traduções, ICU e OpenGL seguem condicionadas
a experimentos próprios. Nenhuma dessas pendências é declarada entregue.

O pacote local 0.0.3-beta1 foi compilado e passou em smoke test e integridade.
A última melhoria de apresentação do caminho no popup foi feita depois desse pacote;
o código-fonte é a referência para a próxima compilação, que deve usar outra versão
porque a política de imutabilidade preserva o pacote já gerado.
