# Referência de Parâmetros do NVEncC no Projeto Broadcast

Os argumentos abaixo são montados por `construir_argumentos_nvenc` em `modelos/conversao.py` a partir das constantes de `config/configuracoes.py` e **não devem ser alterados** para preservar fidelidade com o script original:

| Parâmetro | Valor | Finalidade |
|---|---|---|
| `--log-level` | `error,core_progress=info,core_result=info` | Suprime ruído mantendo linhas de progresso e resultado final |
| `--avhw` | *(flag)* | Decodificação acelerada por hardware |
| `--interlace` | `tff` | Sinaliza entrada entrelaçada Top Field First (1080i/60i broadcast) |
| `--vpp-bwdif` | `mode=bob,order=tff` | Desentrelaçamento BWDIF duplicando a taxa de campos para 59,94p |
| `--avsync` | `forcecfr` | Mantém taxa de quadros constante e sincronismo de áudio/vídeo |
| `--input-analyze` | `60` | Analisa até 60 segundos iniciais do fluxo MPEG-TS para detectar todas as faixas |
| `-c` | `hevc` | Codificação de vídeo em H.265 / HEVC |
| `-u` | `p7` | Preset de qualidade máxima do NVENC |
| `--qvbr` | `18` | Controle de taxa variável baseado em qualidade constante (QVBR 18) |
| `--output-depth` | `10` | Profundidade de cor de 10 bits (reduz banding) |
| `--profile` | `main10` | Perfil HEVC Main10 |
| `--aq` / `--aq-temporal` | *(flags)* | Quantização adaptativa espacial e temporal |
| `--colormatrix`, `--colorprim`, `--transfer`, `--chromaloc` | `auto` | Preserva metadados colorimétricos do fluxo original |
| `--video-metadata`, `--audio-metadata` | `copy` | Copia metadados das faixas de vídeo e áudio |
| `--audio-copy` | `1..N` (ou sem argumento) | Copia sem recodificar todas as faixas de áudio detectadas |
