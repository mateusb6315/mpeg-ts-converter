# Arquitetura atual

`main.py` compõe janela, controladores e serviços. Views recebem validações e emitem
sinais; modelos contêm regras puras; serviços de arquivos/processos não dependem Qt.
O worker coleta os metadados apresentados pela GUI, depois chama o conversor.
A duração ainda é consultada novamente no motor: sua unificação permanece pendente.

A conversão reserva o destino com bloqueio de sistema, cria parcial `.mkv` em pasta
única no mesmo volume e promove a saída sem substituir arquivos existentes. Falhas
preservam o parcial identificado no log. A reserva vazia persiste para evitar corridas
entre instâncias, mas o bloqueio ativo é liberado pelo sistema em caso de queda.

Leitores usam blocos e fila limitada. Diagnósticos têm buffer limitado, com escrita
incremental das linhas comuns. Cancelamento encerra o processo e coleta leitores.
A GUI aguarda sinais de término antes de liberar a operação ou efetivar fechamento.

Build e release ficam em scripts, com núcleo comum de compilação, nomes e manifesto.
Históricos de produção/beta são separados e o manifesto identifica estado do Git,
commit e dependências. Nenhuma etapa de build publica remotamente.
