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

`requirements.txt` declara PyQt6 >=6.5 e pytest >=8; `requirements-build.txt` acrescenta PyInstaller >=6.22,<7. `pyproject.toml` declara Python >=3.13 e PyQt6 >=6.12,<7, e `poetry.lock` registra a resolução do Poetry. Os metadados do pyproject ainda usam `projeto-broadcast` e autor de exemplo.

`scripts/compilar.py` gera `prototypes/beta 0.N/` com `p_broadcast.exe`, usa histórico JSON local, bloqueio e recuperação de publicação interrompida. `scripts/release.py` compacta o prototype local de maior número e escolhe a próxima tag remota `beta-0.N`; os dois números podem divergir. A pasta `prototypes/` inteira é ignorada pelo Git; seu histórico local não é compartilhado entre clones. O README referencia a release beta 0.2. A disponibilidade remota deve ser verificada novamente quando necessário.

A distribuição inclui Python e PyQt6, mas não NVEncC ou ffprobe. O log da aplicação executada pelo código fica no diretório de trabalho; no executável, em `%LOCALAPPDATA%\Projeto Broadcast\projeto_broadcast.log`. O log de codificação fica ao lado do vídeo, quando pode ser gravado. O projeto usa a licença MIT em `LICENSE`.

## Verificação e próximas iterações

A suíte é executada com `python -m pytest -v`; a auditoria com `python .agents/skills/arquitetura-mvc-pyqt6/scripts/validar_arquitetura.py`. Não foram executadas nesta atualização documental. Leia `AGENTS.md` para os limites de arquitetura e os cuidados de build e publicação; consulte as skills do workspace conforme a área alterada.
