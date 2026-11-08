# Verificação da beta 0.3

```powershell
python -m pip install -r requirements-build.txt
python .agents/skills/arquitetura-mvc-pyqt6/scripts/validar_arquitetura.py
python scripts/auditar_workspace.py
python -m pytest -v
python main.py --smoke-test
```

A auditoria complementar descobre novos módulos das camadas. A suíte exercita regras,
CLI, saída isolada, integridade e cancelamento de processo Python controlado. Os
workers Qt têm testes offscreen; isso não comprova GPU/NVEncC ou Windows limpo.

Antes de aprovar o candidato, testar mídia TFF 60i, múltiplas faixas, áudio ausente,
ffprobe ausente, colisão e cancelamento em cada fase. Conferir HEVC Main10, bob,
faixas/canais e sincronia no início/meio/fim. Registrar GPU, driver e versões das
ferramentas. Não apagar a origem nem resultados anteriores durante a verificação.
