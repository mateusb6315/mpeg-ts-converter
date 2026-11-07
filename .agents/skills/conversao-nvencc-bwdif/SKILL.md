---
name: conversao-nvencc-bwdif
description: >-
  Use this skill when inspecting, troubleshooting, or modifying the video
  conversion parameters, NVEncC command-line arguments, ffprobe media probing,
  progress parsing, or audio stream synchronization checks in Projeto Broadcast.
---

# Pipeline de Conversão NVEncC (MPEG-TS 60i → HEVC 60p BWDIF)

Esta skill documenta o funcionamento técnico do motor de conversão do **Projeto Broadcast** e os cuidados obrigatórios para não alterar o comportamento de codificação.

## Fluxo Técnico da Conversão

1. **Localização do `NVEncC`** (`servicos/arquivo_servico.py`):
   - Ordem de busca: variável de ambiente `nvenc64` → `PATH` do sistema → pasta raiz da aplicação → `C:\Program Files\NVEncC_9.31_x64`.
   - Verificação de versão (`servicos/conversao_servico.py`): versões anteriores à `9.18` geram alerta em log devido ao histórico de dessincronia em entradas com PTS negativo.
2. **Sondagem de Entrada com `ffprobe`**:
   - Duração do formato (`format=duration`) usada para estimar `total_quadros = floor(duracao * 59.94 + 0.5)`.
   - Inspeção das faixas de áudio (`codec_type == "audio"`) para construir `--audio-copy 1,2,...` (ou `--audio-copy` caso o `ffprobe` não esteja instalado).
3. **Codificação e Progresso** (`modelos/conversao.py` e `servicos/conversao_servico.py`):
   - Consulte [parametros_nvencc.md](./references/parametros_nvencc.md) para a lista exata de flags que devem ser preservadas.
   - A saída `stdout`/`stderr` é lida byte a byte (tratando `\r` e `\n`) e analisada por `parsear_segmento_progresso`.
   - O arquivo `<saida>_encode_<YYYYMMDD_HHMMSS>.log` é sempre gravado em `utf-8-sig`.
4. **Validação Pós-Conversão**:
   - `validar_fluxos_audio` compara quantidade de faixas, `channels`, `channel_layout` e deslocamento de `start_time` A/V (tolerância de `0.100s`).
