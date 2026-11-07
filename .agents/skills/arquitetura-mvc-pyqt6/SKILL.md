---
name: arquitetura-mvc-pyqt6
description: >-
  Use this skill when modifying, extending, or auditing the codebase of Projeto
  Broadcast to ensure strict compliance with the MVC + pragmatic SRP + Low
  Coupling PyQt6 architectural rules, Portuguese naming conventions, function
  size limits, and layer isolation.
---

# Arquitetura MVC + PyQt6 do Projeto Broadcast

Esta skill guia a manutenção e evolução da arquitetura modular do **Projeto Broadcast**, garantindo que qualquer alteração respeite o desacoplamento entre camadas e os limites de qualidade de código.

## Regras de Isolamento entre Camadas

1. **`config/`**: Apenas constantes imutáveis (`configuracoes.py` e `interface.py`). Não importa nenhuma outra camada do projeto nem `PyQt6`.
2. **`utilitarios/`**: Funções puras de formatação em pt-BR (`formatacao.py`). Não importa `modelos/`, `servicos/`, `visoes/`, `controladores/` nem `PyQt6`.
3. **`modelos/`**: Regras de negócio puras e `dataclass`/`Enum` (`conversao.py`). **Proibido** fazer I/O de disco/rede/subprocesso ou importar `PyQt6`, `visoes/`, `controladores/` ou `servicos/`.
4. **`servicos/`**: Infraestrutura (`ffprobe`, `NVEncC`, sistema de arquivos). Isola `subprocess` (sempre com `CREATE_NO_WINDOW` no Windows) e **nunca importa `PyQt6`**.
5. **`visoes/`**: Componentes visuais PyQt6 em modo claro fixo (`560×170`). **Nunca importa `modelos/` nem `controladores/`**; recebe validadores e callbacks por injeção.
6. **`controladores/`**: Orquestra os sinais entre `JanelaPrincipal`, `ConversaoTrabalhador` (`QObject` movido para `QThread`) e os serviços.
7. **`main.py`**: Única raiz de composição autorizada a conectar todas as camadas.

## Limites de Código Obrigatórios

- **Módulos:** máximo de ~250 linhas.
- **Funções/Métodos:** máximo de 30 linhas de código (descontando docstring e linhas em branco) e máximo de 4 parâmetros.
- **Largura de linha:** até 100 caracteres (PEP 8).
- **Nomenclatura:** todos os identificadores próprios em português, sem acentos e sem `ç`.

## Passo de Validação Automática

Sempre que criar ou editar arquivos Python do projeto, execute o script validador:

1. Execute [validar_arquitetura.py](./scripts/validar_arquitetura.py):
   `python .agents/skills/arquitetura-mvc-pyqt6/scripts/validar_arquitetura.py`
2. Corrija qualquer violação reportada antes de concluir a tarefa.
