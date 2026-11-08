# Orientações para agentes

Leia `README.md` e `MEMORY.md` antes de alterar o projeto. Confira o código e o estado do Git: a memória descreve o estado observado, não substitui a implementação. Preserve alterações preexistentes do usuário.

## Projeto e arquitetura

O MPEG-TS Converter é uma aplicação PyQt6 para Windows que converte um arquivo `.ts` por vez usando NVEncC. `main.py` é a raiz de composição. Mantenha MVC com responsabilidades isoladas:

- `config/`: constantes, sem dependências das demais camadas ou Qt.
- `utilitarios/`: formatação pura; sem I/O, Qt ou dependência de domínio.
- `modelos/`: dados e regras puras; sem I/O, Qt, serviços ou interface.
- `servicos/`: arquivos e subprocessos; não importa Qt. No Windows, subprocessos da aplicação usam `CREATE_NO_WINDOW`.
- `visoes/`: componentes Qt; não importa modelos ou controladores. Recebe validações e callbacks por injeção.
- `controladores/`: conectam a interface, serviços e trabalhadores em `QThread`; mantenha a interface responsiva e trate encerramento e cancelamento.

Use identificadores próprios em português sem acentos, nomes claros e dependências injetáveis. A orientação arquitetural do projeto estabelece módulos em torno de 250 linhas, funções de até 30 linhas de código e quatro parâmetros, e linhas de até 100 caracteres. Aplique esses limites com pragmatismo e consulte `.agents/skills/arquitetura-mvc-pyqt6/SKILL.md` para alterações Python.

## Conversão e infraestrutura

O perfil fixo usa TFF, BWDIF bob, HEVC Main10, QVBR 18 e cópia de áudio. A estimativa de 59,94 fps não é uma opção explícita de taxa no comando. Não altere parâmetros, escolha de faixas, sincronia ou leitura de progresso sem examinar `config/configuracoes.py`, `modelos/conversao.py`, os serviços e a skill `.agents/skills/conversao-nvencc-bwdif/SKILL.md`.

NVEncC é externo e obrigatório; ffprobe é externo e opcional. Preserve o funcionamento com sondagem indisponível e o tratamento de erros e cancelamento. A saída e o log de codificação ficam ao lado da origem; o log da aplicação compilada fica em `%LOCALAPPDATA%\Projeto Broadcast`.

## Desenvolvimento e verificação

Use Python 3.13 para o ambiente definido em `pyproject.toml`. Instale `requirements.txt` para execução e testes ou `requirements-build.txt` para compilação. Para alterações Python, execute a auditoria arquitetural e os testes adequados à mudança:

```powershell
python .agents/skills/arquitetura-mvc-pyqt6/scripts/validar_arquitetura.py
python -m pytest -v
```

Testes automatizados não substituem uma conversão real com GPU, driver, NVEncC e mídia adequados. Informe limitações de validação; não afirme resultados históricos como atuais. Consulte `.agents/skills/testes-internos/SKILL.md` ao executar ou modificar testes.

## Compilação e publicação

`scripts/compilar.py` compila produção com versão X.Y.Z em `dist/producao/`.
`scripts/compilar_beta.py` compila beta com nome Windows livre em `prototypes/beta/`;
ambos pedem a versão por input, aceitando `--versao` para CI. Convenção beta:
`0.0.3-beta1`. Compartilham bloqueio, histórico e recuperação em `scripts/distribuicao/`.
`scripts/release.py --artefato <pasta>` verifica o manifesto localmente. Publicação
exige `--publicar --notas <arquivo>` e cria rascunho; não executar sem autorização.
Execute também `python scripts/auditar_workspace.py` para descobrir novos módulos.
Instale `requirements-dev.txt` para testes e `requirements-build.txt` para build.

`prototypes/`, logs, caches e backups são ignorados pelo Git; não apague nem adicione artefatos locais inadvertidamente. Após mudanças relevantes, atualize README e memória quando necessário, mantendo licença e caminhos reais consistentes.
