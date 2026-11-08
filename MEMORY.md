# Memória do MPEG-TS Converter

Estado analisado em 2026-11-08. Consulte o código para confirmar detalhes antes de uma alteração; resultados antigos de testes não são evidência da execução atual.

## Objetivo e fluxo

Aplicação desktop Windows em Python/PyQt6, anteriormente chamada Projeto Broadcast. Converte um `.ts` local por vez para `<nome>_60fps_bwdif.mkv` na pasta de origem, usando NVEncC externo. O perfil pressupõe entrada 60i TFF e usa BWDIF bob, HEVC Main10, preset p7, QVBR 18 e cópia de áudio. A aplicação não confirma se a fonte é 60i/TFF; 59,94 fps é usado para estimar progresso, sem argumento explícito de taxa de saída.

A janela oferece clique ou arraste, mostra progresso e tempos e executa o codificador em segundo plano. Ao fechar durante uma conversão, pede confirmação e sinaliza cancelamento; um arquivo parcial pode permanecer. A seleção manual do NVEncC aceita `NVEncC64.exe` e `nvenc64.exe` e tenta persistir a variável `nvenc64` no ambiente do usuário. A busca também considera Registro, PATH, diretório da aplicação e caminho padrão configurado.

ffprobe no PATH é opcional: obtém duração e fluxos e permite comparar faixas, canais e deslocamento inicial A/V após a conversão. Sem sondagem, a conversão pode continuar com `--audio-copy` sem seleção explícita; divergências de áudio são avisos no log, não falhas de conversão.

## Organização

- `main.py`: logging, QApplication e composição.
- `config/`: parâmetros técnicos e constantes da interface.
- `modelos/conversao.py`: estados, dados, caminhos, progresso, áudio e comando.
- `servicos/`: sondagem e arquivos, subprocesso NVEncC, localização e persistência da ferramenta.
- `controladores/`: coordenação da janela, worker de conversão e verificação do NVEncC em QThread.
- `visoes/`: janela, componentes, estilos e tema claro.
- `utilitarios/formatacao.py`: formatação pura em pt-BR.
- `tests/`: testes de modelo, formatação, integração interna e compilação.

## Ambiente e distribuição

`requirements.txt` fixa execução; `requirements-dev.txt` adiciona pytest e
`requirements-build.txt` adiciona PyInstaller/hooks. Pyproject e poetry.lock incluem
grupos dev/build. Ambiente suportado de desenvolvimento: Python 3.13.

Compiladores de produção/beta solicitam versão manual ou recebem --versao para CI.
Ambos os compiladores aceitam versão livre válida para pasta no Windows. Distribuição e
verificação estão descritas em docs/distribuicao.md. Os artefatos beta 0.2 existentes
permanecem como referência, sem associação garantida com o HEAD.

Logs compilados continuam em %LOCALAPPDATA%\Projeto Broadcast. NVEncC e ffprobe
não são incluídos. O projeto conserva sua licença MIT.

## Verificação e próximas iterações

A suíte é executada com `python -m pytest -v`; a auditoria com `python .agents/skills/arquitetura-mvc-pyqt6/scripts/validar_arquitetura.py`. Não foram executadas nesta atualização documental. Leia `AGENTS.md` para os limites de arquitetura e os cuidados de build e publicação; consulte as skills do workspace conforme a área alterada.

## Implementação local da beta 0.3

Compiladores separados com input manual e --versao para CI. Beta aceita nomes livres
Windows. Destinos isolados; pastas existentes geram uma nova pasta numerada.
Release verifica manifesto explícito; publicação cria rascunho, exige origem limpa e
recusa tag existente. Consultar docs/distribuicao.md; nenhuma publicação foi executada.
Conversão preserva fluxos de vídeo na validação A/V, usa parcial isolado e recusa
colisão. Metadados da interface são coletados no worker. Plano original permanece
como referência histórica, com pendências de validação real e otimização do runtime.
