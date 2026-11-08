## Notas da versão beta 0.3 do MPEG-TS Converter

Alterações locais ainda não publicadas. Convenção recomendada para o build: 0.0.3-beta1.

* Adicionados compiladores separados para produção e beta, com entrada manual da versão
* Adicionada conferência de integridade dos pacotes antes de preparar uma release
* Corrigida a perda dos dados de vídeo necessários para conferir o deslocamento A/V
* Corrigido o preenchimento prematuro da barra em 100%
* A leitura de metadados da interface passa a ocorrer em segundo plano
* Resultados existentes são preservados e conversões usam arquivos parciais isolados

## Problemas conhecidos:

* A validação com NVEncC, GPU e mídia reais ainda está pendente.
* A comparação de horários iniciais não comprova sincronia durante todo o vídeo.
