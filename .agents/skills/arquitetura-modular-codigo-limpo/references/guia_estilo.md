# Guia de estilo – exemplos

## Árvore de referência
```
projeto/
├── main.py                 # composição
├── config/                 # configuracoes.py, interface.py
├── utilitarios/            # formatacao.py
├── modelos/                # dataclasses, enums, regras puras
├── servicos/               # infraestrutura (sem UI)
├── visoes/                 # janela_*, componentes_*, estilos_*, tema_*
├── controladores/          # controlador_*, trabalhador_*
├── tests/                  # espelha as camadas
└── .agents/skills/         # skills do projeto
```

## Cabeçalho de módulo
```python
"""Resumo de uma linha do propósito do módulo."""

import logging
from pathlib import Path

from PyQt6.QtCore import QObject

from config.interface import TEXTO_X

REGISTRADOR = logging.getLogger(__name__)

# --- API pública ---
...
# --- Funções auxiliares privadas ---
```

## Função boa
```python
def calcular_percentual_progresso(feitos: int, total: int | None, anterior: float = 0.0) -> float:
    """Calcula percentual monotônico limitado ao intervalo permitido."""
    if not total or total <= 0:
        return anterior          # guarda: retorno antecipado, sem aninhar
    return max(anterior, min(MAXIMO, feitos / total * 100.0))
```

## Injeção com padrão
```python
class Controlador(QObject):
    def __init__(self, janela, verificar=verificar_ambiente, salvar=salvar_manual): ...
```

## Fronteira de thread
```python
try:
    resultado = self._executar()
except ErroDominio as erro:
    self.falhou.emit(str(erro))
except Exception as erro:  # noqa: BLE001 - nada pode morrer calado na thread
    REGISTRADOR.exception("Erro inesperado")
    self.falhou.emit(f"Erro inesperado: {erro}")
else:
    self.concluida.emit(str(resultado))
finally:
    self.finalizado.emit()
```

## Dividir módulo grande
Sintoma: >250 linhas. Divida por responsabilidade:
`janela.py` (eventos/layout) | `componentes.py` (widgets + diálogos genéricos) |
`estilos.py` (QSS). Reexporte via imports explícitos, sem `import *`.

## Marcador de extensão
```python
# EXTENSÃO: para exibir nova propriedade, adicione um rótulo na grade.
```
