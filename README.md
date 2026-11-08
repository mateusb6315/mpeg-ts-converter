# MPEG-TS Converter

Aplicativo desktop para Windows que converte **um vídeo MPEG-TS (`.ts`) por vez** em um arquivo Matroska (`.mkv`). Ele foi criado para material **60i com campo superior primeiro (TFF)**: o NVEncC aplica desentrelaçamento BWDIF em modo bob e codifica o vídeo em HEVC Main10 (10 bits). Para essa entrada, cada campo dá origem a um quadro progressivo, com resultado próximo de **59,94 quadros por segundo**. O áudio é copiado quando há faixas disponíveis.

A interface, em português, permite escolher ou arrastar o arquivo, acompanha o andamento e informa a conclusão. A conversão usa a GPU NVIDIA por meio do [NVEncC](https://github.com/rigaya/NVEnc). **O programa não examina se o vídeo realmente é 60i/TFF antes de aplicar esse perfil fixo**; confira a fonte para evitar um resultado inadequado.

## Comece pela distribuição pronta

A [página de releases](https://github.com/mateusb6315/mpeg-ts-converter/releases) contém as versões publicadas, incluindo a [beta 0.0.3](https://github.com/mateusb6315/mpeg-ts-converter/releases/tag/0.0.3-beta). Para usar uma distribuição:

1. Baixe o arquivo ZIP da versão desejada e **extraia todo o conteúdo** para uma pasta com permissão de escrita. Não execute o programa diretamente de dentro do ZIP.
2. Instale ou extraia o NVEncC conforme a seção seguinte. Tenha uma GPU e um driver NVIDIA compatíveis.
3. Abra `mpeg-ts-converter.exe` na pasta extraída, mantendo a subpasta `_internal` ao lado do executável.
4. Se o programa não localizar o NVEncC, selecione `NVEncC64.exe` ou `nvenc64.exe` quando solicitado.
5. Clique na área **“Selecione ou arraste um arquivo .ts aqui”** ou solte nela um único arquivo `.ts`. A conversão começa imediatamente.

A distribuição inclui o runtime Python e a interface PyQt6. **NVEncC e ffprobe não são incluídos.** Não é preciso instalar Python para executar o ZIP compilado.

## Requisitos e ferramentas externas

- **Sistema:** Windows 10 ou 11, GPU NVIDIA e driver compatíveis com o NVEncC e a codificação HEVC de 10 bits. A velocidade e a possibilidade de conversão dependem do hardware e dos recursos suportados pelo codificador.
- **NVEncC obrigatório:** baixe a versão Windows nas [versões oficiais do NVEncC](https://github.com/rigaya/NVEnc/releases), extraia o pacote e mantenha seus arquivos juntos. A aplicação registra um aviso quando detecta versão anterior à 9.18; use uma versão atual para evitar problemas conhecidos de sincronia.
- **ffprobe opcional:** é parte do FFmpeg. Coloque `ffprobe.exe` no `PATH` do Windows para mostrar a duração da entrada e permitir a sondagem e a conferência das faixas de áudio. Em um novo PowerShell, confirme com `ffprobe -version`. Sem ele, a conversão ainda pode ocorrer, mas duração, estimativa de progresso e validação de áudio ficam limitadas.
- **Arquivos:** a pasta do `.ts` precisa ter espaço livre e permitir escrita, pois o `.mkv` e o log da codificação são criados nela.

Na inicialização, a aplicação procura o NVEncC na variável `nvenc64` da sessão ou do Registro do Windows, depois no `PATH`, ao lado do programa e na pasta padrão `C:\Program Files\NVEncC_9.31_x64`. A variável pode apontar para o executável ou para a pasta que o contém. Se a busca falhar, a janela pergunta se você deseja selecionar o arquivo manualmente e oferece um link para download. O botão **“Selecionar nvenc64”** permanece disponível até uma seleção aceita. A escolha é aplicada à sessão atual e o programa tenta salvá-la na variável de ambiente do usuário para as próximas execuções. A seleção verifica nome e existência do arquivo; a compatibilidade real é verificada quando o NVEncC é usado.

## Executar pelo código-fonte

Use **Python 3.13** para seguir tanto os arquivos de dependências quanto o `pyproject.toml`. O código-fonte pode ser instalado com `pip`; o Poetry é opcional. Se ainda não tiver o projeto, obtenha-o com `git clone` e entre na pasta criada:

```powershell
git clone https://github.com/mateusb6315/mpeg-ts-converter.git
cd mpeg-ts-converter
```

No PowerShell, na raiz do repositório:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python main.py
```

`requirements.txt` fixa as bibliotecas de execução. `requirements-dev.txt` acrescenta
pytest; `requirements-build.txt` acrescenta PyInstaller e seus hooks. O pyproject e o
lockfile mantêm grupos equivalentes para Poetry:

```powershell
poetry install --with dev,build --no-root
poetry run python main.py
```

O uso de `--no-root` executa a aplicação diretamente a partir do repositório, sem precisar empacotar o projeto como biblioteca Python. Para abrir a interface sem console com o ambiente virtual do exemplo, use `.\.venv\Scripts\pythonw.exe main.py`.

## Como usar a interface

1. Abra o programa e aguarde a busca inicial pelo NVEncC. Se aparecer a pergunta de seleção manual, indique o executável extraído. Se preferir instalá-lo depois, use o botão que ficará visível na janela.
2. Escolha um arquivo local com extensão `.ts` pelo clique na área à esquerda ou arraste **exatamente um** arquivo para a janela. Outros formatos, múltiplos arquivos e caminhos inexistentes são recusados. A extensão é verificada sem diferenciar maiúsculas e minúsculas; o conteúdo do vídeo não é analisado para confirmar TFF/60i.
3. A janela mostra nome, tamanho, duração quando conhecida, status, tempo decorrido e tempo restante estimado. O nome longo aparece abreviado; passe o cursor sobre ele para ver o caminho completo. Durante a conversão, não é possível iniciar outro arquivo.
4. Aguarde o aviso de conclusão. Após fechar o aviso, a janela volta a aceitar outro `.ts`. Em caso de falha, ela mostra uma mensagem; consulte os logs descritos abaixo para obter mais detalhes.
5. Para cancelar uma conversão, feche a janela e confirme. O codificador recebe a solicitação de interrupção. Um arquivo `.mkv` incompleto pode permanecer em uma subpasta `.conversao-*`; confira-o antes de usá-lo ou iniciar uma nova tentativa.

O resultado é salvo **na mesma pasta da entrada** como `<nome-original>_60fps_bwdif.mkv`. Exemplo: `programa.ts` gera `programa_60fps_bwdif.mkv`. Não há seleção de pasta de saída nem fila de arquivos. Uma nova conversão recusa saída existente. Preserve ou renomeie o resultado anterior antes de repetir a operação.

## O que acontece durante a conversão

O programa lê o tamanho do arquivo e tenta consultar a duração e as faixas com o ffprobe. Em seguida, chama o NVEncC fora da thread da interface. O perfil usa entrada TFF, `--vpp-bwdif mode=bob,order=tff`, `--avsync forcecfr`, HEVC Main10, preset `p7`, QVBR 18 e recursos de AQ. Os argumentos ficam em `config/configuracoes.py`; não há controles de qualidade ou filtro na janela. A taxa de 59,94 fps é usada pelo programa para **estimar** o total de quadros e o progresso, não é passada como opção explícita de taxa de saída ao NVEncC.

Quando o ffprobe identifica faixas de áudio, o programa solicita a cópia de todas elas. Se a sondagem não estiver disponível, solicita `--audio-copy` sem selecionar faixas específicas; se a sondagem indicar que não há áudio, não acrescenta essa opção. Após uma conversão concluída, compara a quantidade de faixas, os canais e o deslocamento inicial áudio/vídeo, quando há dados para isso. Diferenças superiores à tolerância de 100 ms são registradas como avisos no log da aplicação e **não bloqueiam a conclusão**. Confira o arquivo resultante com um reprodutor antes de descartá-lo ou distribuí-lo como versão final.

O progresso depende da saída do NVEncC e, quando disponível, da duração obtida pelo ffprobe. O tempo restante é uma estimativa e pode variar; a barra chega a 100% somente após a conclusão reportada pelo processo.

## Logs e solução de problemas

| Situação | Onde procurar |
| --- | --- |
| Aplicação iniciada pelo código-fonte | `projeto_broadcast.log` no diretório de trabalho usado para iniciá-la |
| Aplicação compilada | `%LOCALAPPDATA%\Projeto Broadcast\projeto_broadcast.log` |
| Codificação | `<nome-original>_60fps_bwdif_encode_<AAAAMMDD>_<HHMMSS>.log` na pasta do `.ts` |

O log da codificação registra o comando, o código de saída e mensagens do NVEncC. Ele é gravado quando o codificador retorna, inclusive com código de erro; um cancelamento ou uma falha antes dessa etapa pode impedir a sua criação. Se a pasta de origem não permitir escrita, o próprio log também pode faltar.

Se o programa disser que o NVEncC não foi encontrado, confira o caminho selecionado, a variável `nvenc64` e a extração completa do pacote. Se a conversão falhar, verifique a versão do NVEncC, o driver, a compatibilidade da GPU, o espaço em disco e as mensagens dos logs. Se a duração aparecer indisponível, verifique `ffprobe -version` em um novo PowerShell e confirme que a pasta de `ffprobe.exe` está no `PATH`. Alguns caminhos de log ainda usam “Projeto Broadcast”; isso não afeta os nomes dos arquivos de saída.

## Estrutura do projeto

| Caminho | Responsabilidade |
| --- | --- |
| `main.py` | Inicia o Qt, configura o log e conecta as camadas. |
| `config/` | Parâmetros de conversão, caminhos, textos e aparência. |
| `modelos/` | Estados, dados e regras de conversão sem acesso a arquivos ou interface. |
| `servicos/` | Busca de executáveis, sondagem com ffprobe, execução do NVEncC e persistência da configuração. |
| `controladores/` | Coordena seleção, estados, progresso e trabalhadores em `QThread`. |
| `visoes/` | Janela, componentes, diálogos e estilos PyQt6. |
| `utilitarios/` | Formatação de números, duração e texto. |
| `scripts/compilar.py`, `scripts/compilar_beta.py` | Geram distribuições Windows para produção e beta. |
| `scripts/release.py` | Verifica um artefato informado e pode preparar uma release em rascunho. |
| `tests/` | Testes automatizados. |
| `requirements*.txt`, `pyproject.toml`, `poetry.lock` | Definições de dependências para `pip`, build e Poetry. |
| `LICENSE` | Texto integral da licença MIT. |

A interface e os subprocessos ficam separados: a janela emite eventos, os controladores coordenam o fluxo e os serviços executam as operações externas. Essa divisão permite manter a interface responsiva durante a conversão.

## Compilar e preparar uma versão

Instale `requirements-build.txt`. Execute `python scripts/compilar.py` para produção
ou `python scripts/compilar_beta.py` para beta. Ambos pedem a versão manualmente.
Ambos aceitam versão livre válida como nome de pasta no Windows. Para CI use
`--versao` explicitamente.

Produção fica em `dist/producao/mpeg-ts-converter <versao>`; beta em
`prototypes/beta/mpeg-ts-converter <versao>`.
Se a pasta já existir, uma nova pasta numerada é criada. Em caso de acesso negado
ao mover a pasta, o script repete a operação e tenta copiá-la. Se a cópia também
falhar, confira permissões e processos que possam estar bloqueando os arquivos.
Nenhum compilador
publica no GitHub. Consulte [distribuição](docs/distribuicao.md) para manifesto,
verificação e preparação explícita de rascunho de release.

## Desenvolvimento e verificações

Para executar a suíte de testes e a auditoria de arquitetura, com o ambiente de desenvolvimento instalado:

```powershell
python -m pytest -v
python .agents/skills/arquitetura-mvc-pyqt6/scripts/validar_arquitetura.py
```

Essas verificações cobrem regras e integração interna. Uma conversão real também depende de um arquivo de entrada adequado, do NVEncC e do hardware compatível.

## Licença

O MPEG-TS Converter é distribuído sob a **licença MIT**. Ela permite usar, modificar e distribuir o projeto, inclusive comercialmente, desde que o aviso de direitos autorais e o texto da licença acompanhem as cópias ou partes substanciais. O software é fornecido sem garantias. Consulte o texto completo em [`LICENSE`](LICENSE). NVEncC, FFmpeg/ffprobe e demais dependências seguem suas próprias licenças.
