---
name: testes-internos
description: >-
  Use this skill when running internal tests, verifying unit test coverage,
  testing the PyQt6 interface headlessly, or validating architectural compliance
  before delivering changes in Projeto Broadcast.
---

# Execução de Testes Internos do Projeto Broadcast

Esta skill define o procedimento padrão para validar qualquer alteração no **Projeto Broadcast** sem depender de hardware GPU, `NVEncC`, `ffprobe` ou servidor gráfico interativo.

## Etapas de Verificação

1. **Auditoria Estática da Arquitetura (AST)**:
   Execute o validador da skill `arquitetura-mvc-pyqt6`:
   ```powershell
   python .agents/skills/arquitetura-mvc-pyqt6/scripts/validar_arquitetura.py
   ```
2. **Testes de Unidade (`pytest`)**:
   Execute toda a suíte em `tests/`:
   ```powershell
   python -m pytest -v
   ```
3. **Teste de Integração Headless (Camadas + GUI Offscreen)**:
   A suíte `tests/test_integracao_interna.py` exercita `JanelaPrincipal`, `ConversaoControlador`, `ConversaoTrabalhador` e `converter_arquivo` com dublês em modo `QT_QPA_PLATFORM=offscreen`. Certifique-se de que todos os testes passem com 100% de sucesso.
