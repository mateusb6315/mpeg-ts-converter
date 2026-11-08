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

`scripts/compilar.py` gera `prototypes/beta 0.N/` com `p_broadcast.exe`, histórico local, bloqueio e recuperação de builds interrompidos. `scripts/release.py` publica no GitHub e escolhe o maior prototype local e a próxima tag remota `beta-0.N` independentemente: verifique a correspondência antes de publicar. Use a skill `.agents/skills/compilacao-distribuicao-executavel/SKILL.md` ao alterar o pipeline. Não execute publicação, push ou release sem solicitação ou autorização aplicável.

`prototypes/`, logs, caches e backups são ignorados pelo Git; não apague nem adicione artefatos locais inadvertidamente. Após mudanças relevantes, atualize README e memória quando necessário, mantendo licença e caminhos reais consistentes.
