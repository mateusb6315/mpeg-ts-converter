# Projeto Broadcast

O Projeto Broadcast é um conversor desktop para Windows que prepara vídeos MPEG-TS entrelaçados para exibição progressiva. A interface em português recebe um arquivo `.ts` por vez e usa o **NVIDIA NVEncC** para gerar um `.mkv` com vídeo HEVC Main10 e desentrelaçamento BWDIF em modo bob. O perfil foi pensado para material 60i com campo superior primeiro (TFF), produzindo aproximadamente 59,94 quadros por segundo para esse tipo de entrada.

A aplicação mostra informações do arquivo, progresso e tempo estimado, enquanto a codificação acontece em segundo plano. Sua arquitetura separa interface, regras de negócio e acesso às ferramentas externas.

## Requisitos e implantação

- **Windows 10 ou 11**, com GPU NVIDIA e driver compatíveis com os recursos de decodificação, codificação HEVC de 10 bits e filtros utilizados pelo NVEncC.
- **NVEncC**: baixe uma versão para Windows nas [versões oficiais](https://github.com/rigaya/NVEnc/releases), extraia o pacote e mantenha seus arquivos juntos. Recomenda-se a versão 9.18 ou posterior; versões anteriores geram um aviso no log por causa da sincronia. O programa não instala o NVEncC automaticamente.
- **Python 3.10 ou superior** e `pip` para executar o código-fonte ou compilar. O executável já compilado dispensa a instalação do Python na máquina de destino.
- **ffprobe**, componente do FFmpeg, é opcional. Para habilitar a leitura de duração e a verificação de áudio, instale-o e inclua a pasta que contém `ffprobe.exe` no `PATH` do Windows; confirme em um novo PowerShell com `ffprobe -version`.
- Espaço livre e permissão de escrita na pasta do arquivo de entrada, onde serão gravados o vídeo e o log da codificação.

O NVEncC pode ser localizado pela variável de ambiente `nvenc64`, pelo `PATH`, ao lado da aplicação ou em `C:\Program Files\NVEncC_9.31_x64`. Na inicialização, a aplicação também consulta a variável no Registro do Windows. Se não encontrar o executável, oferece um seletor para `NVEncC64.exe` ou `nvenc64.exe`. A escolha vale para a sessão atual e o programa tenta persistir o caminho na variável de usuário `nvenc64` no Registro.

## Dependências

| Dependência | Finalidade | Instalação |
| --- | --- | --- |
| PyQt6 `>=6.5.0` | Interface gráfica e comunicação entre threads | `requirements.txt` |
| pytest `>=8.0.0` | Execução dos testes automatizados | `requirements.txt` |
| PyInstaller `>=6.22,<7` | Geração da distribuição Windows | `requirements-build.txt`, que também inclui `requirements.txt` |
| NVEncC | Decodificação, desentrelaçamento e codificação | Download e extração separados |
| ffprobe | Sondagem e verificação de mídia, opcionais | Instalação separada no `PATH` |

Além dessas dependências, o código usa a biblioteca padrão do Python. A distribuição compilada inclui Python e PyQt6, mas não inclui NVEncC nem ffprobe.

## Quick start

No PowerShell, a partir da raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Para iniciar sem uma janela de console, use `pythonw main.py` no ambiente configurado. Se o NVEncC ainda não for encontrado, siga as instruções da janela e selecione o executável extraído. Depois clique na área de seleção ou arraste um único arquivo `.ts` para a janela: a conversão começa automaticamente.

Se já tiver uma distribuição compilada, execute `Projeto Broadcast.exe` dentro da pasta da distribuição, mantendo seus arquivos juntos. As ferramentas externas e os requisitos de GPU continuam necessários.

## Fluxo de operação

1. Ao iniciar, `main.py` configura o log e o tema, cria a janela e conecta os controladores. A busca pelo NVEncC ocorre em segundo plano. Se ele não for encontrado, a interface oferece seleção manual e um link para download.
2. Escolha um arquivo local `.ts` clicando na área indicada ou arrastando-o para a janela. A aplicação verifica a existência e a extensão; não verifica se o conteúdo realmente é 60i ou TFF. O perfil é fixo, portanto use uma fonte adequada.
3. O painel mostra nome, tamanho e, quando disponível, duração. O serviço consulta o ffprobe para descobrir as faixas e estimar o total de quadros; se a sondagem falhar ou estiver indisponível, a conversão ainda pode prosseguir e a cópia de áudio é solicitada sem seleção explícita de faixas.
4. O NVEncC é executado em uma thread de trabalho. A interface acompanha o progresso e os tempos decorrido e estimado. Apenas um arquivo é processado por vez. A estimativa depende dos dados fornecidos pelo codificador e pela sondagem.
5. O resultado é gravado na mesma pasta, com o nome `<nome>_60fps_bwdif.mkv`. Um log de codificação com data e hora também é criado nessa pasta após o processo retornar. Ao concluir, a janela informa o sucesso e volta ao estado inicial; em caso de erro, mostra uma mensagem.
6. Para interromper uma conversão, feche a janela e confirme a saída. O processo do codificador é encerrado; pode restar um arquivo de saída incompleto, e o log da codificação pode não ser gravado nesse caso.

## Estrutura de módulos

```text
main.py                         Composição e inicialização da aplicação
config/
  configuracoes.py              Caminhos, ferramentas e parâmetros de conversão
  interface.py                  Textos, dimensões, cores e configuração de log
modelos/
  conversao.py                  Estados, dados e regras puras da conversão
servicos/
  arquivo_servico.py            Validação, sondagem e busca de executáveis
  conversao_servico.py          Execução do NVEncC, progresso e logs
  nvenc_config_servico.py       Detecção e configuração da variável nvenc64
controladores/
  conversao_controlador.py      Fluxo da janela, estados e progresso
  conversao_trabalhador.py      Conversão em QThread e sinais de resultado
  verificador_nvenc_trabalhador.py  Busca do NVEncC e seleção manual
visoes/
  janela_principal.py           Janela, seleção, arraste e diálogos
  componentes_visao.py          Componentes e caixas de mensagem
  estilos_visao.py              Estilos QSS
  tema_visao.py                 Tema claro da aplicação
utilitarios/formatacao.py       Formatação de valores e argumentos
scripts/compilar.py             Compilação e versionamento da distribuição
tests/                          Testes automatizados
```

O projeto segue uma organização MVC: os modelos concentram regras e dados, os serviços isolam operações externas, as visões apresentam a interface e os controladores coordenam os sinais e o trabalho em segundo plano. `main.py` cria e conecta essas partes.

## Informações importantes

### Perfil de conversão e áudio

O perfil usa entrada TFF, `--vpp-bwdif mode=bob,order=tff`, sincronização de taxa constante (`--avsync forcecfr`), HEVC Main10, preset `p7`, QVBR 18 e AQ espacial e temporal. Os parâmetros ficam em `config/configuracoes.py`; a interface não oferece escolha de perfil. A taxa de 59,94 fps também é usada para estimar o progresso, não como opção explícita de taxa de saída no comando.

Quando o ffprobe identifica as faixas de áudio, o programa solicita ao NVEncC a cópia de todas elas; se não houver áudio, não adiciona essa opção. Após uma conversão bem-sucedida, tenta comparar quantidade de faixas, canais e deslocamento inicial entre áudio e vídeo, com tolerância de 100 ms. Divergências são registradas no log da aplicação como avisos e não impedem a conclusão. A verificação depende dos dados disponíveis no ffprobe e não substitui a conferência do vídeo e áudio resultantes.

O nome de saída é determinístico: uma nova conversão da mesma origem aponta para o mesmo caminho. Verifique ou renomeie uma saída anterior antes de converter novamente. Não há fila de arquivos nem seleção de destino na interface.

### Logs e diagnóstico

- **Aplicação executada pelo código-fonte:** `projeto_broadcast.log` no diretório de trabalho a partir do qual foi iniciada.
- **Aplicação compilada:** `%LOCALAPPDATA%\Projeto Broadcast\projeto_broadcast.log`.
- **Codificação:** `<nome>_60fps_bwdif_encode_<data>_<hora>.log`, na pasta de origem, com comando, código de saída e mensagens do NVEncC. A gravação pode falhar se a pasta não permitir escrita.

Se houver falha, confira a compatibilidade da GPU e do driver, o caminho do NVEncC, o espaço em disco e os logs. Sem ffprobe no `PATH`, a duração e a validação de áudio podem ficar indisponíveis. A seleção manual do NVEncC verifica o nome e a existência do arquivo, mas não garante que ele seja executável ou compatível.

### Compilação para distribuição

Em um ambiente Python no Windows, execute na raiz:

```powershell
python -m pip install -r requirements-build.txt
python scripts/compilar.py
```

O script usa o PyInstaller em modo de pasta e cria `prototypes/beta 0.1/`, `beta 0.2/` e assim por diante. Distribua a pasta inteira. Ele registra as versões em `prototypes/historico.json`, preserva versões anteriores e recupera registros interrompidos a partir dos arquivos `build.json`. Um histórico inválido deve ser corrigido antes de uma nova compilação. Compilações simultâneas são bloqueadas; a presença de `.compilacao.lock` após a execução não significa que o bloqueio ainda esteja ativo. Em falha de compilação, são exibidas as últimas linhas da saída do PyInstaller.

### Testes

Com as dependências instaladas, execute:

```powershell
python -m pytest -v
python .agents/skills/arquitetura-mvc-pyqt6/scripts/validar_arquitetura.py
```

Os testes automatizados e a auditoria de arquitetura ajudam a verificar o código; a execução real da conversão depende também das ferramentas externas e do hardware compatível.

## Licença MIT

O projeto é disponibilizado sob a licença MIT, que permite usar, copiar, modificar e distribuir o software, inclusive para fins comerciais, desde que o aviso de direitos autorais e a licença sejam mantidos nas cópias ou partes substanciais. O software é fornecido sem garantias. As ferramentas e dependências de terceiros possuem suas próprias licenças.

Este repositório ainda não contém um arquivo `LICENSE` com o texto integral da licença e a identificação do titular dos direitos autorais.
