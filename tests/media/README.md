# Mídia sintética de testes

`fluxo_progresso_sintetico.ts` tem 16 MiB e pacotes MPEG-TS de 188 bytes, com PAT,
PMT e preenchimento determinístico em PID nulo. Serve para exercitar leitura,
transferência de dados e interfaces que precisam mostrar progresso em entradas
maiores. Não contém quadros de vídeo nem áudio decodificável, não é uma mídia de
conversão e não comprova a saída de NVEncC. Testes de parser/progresso devem usar
saída controlada; conversão de verdade exige uma amostra decodificável e GPU.
