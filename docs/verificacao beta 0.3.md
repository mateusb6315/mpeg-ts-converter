# Verificação local — 8 de novembro de 2026

Python 3.13.3, PyQt6/Qt 6.12.0, PyInstaller 6.22.3 e hooks 2026.9.
Auditoria original e descoberta automática aprovadas. Suíte: 65 testes aprovados,
incluindo QThread com metadados lentos e subprocesso Python cancelado.

Build real: prototypes/beta/0.0.3-beta1, windowed. Manifesto conferido e smoke test
`p_broadcast.exe --smoke-test` com Qt offscreen retornou zero. Git sujo registrado:
o pacote não é elegível para publicação pelo script. Não houve publicação.

* Extraído: 89.004.965 bytes (aproximadamente 84,9 MiB).
* ZIP local: 34.139.013 bytes (aproximadamente 32,6 MiB).
* Referência beta 0.2: 127.075.745 bytes extraídos e 50.565.552 bytes no ZIP.

A redução acompanha a correção de coleta de DLL ICU incompatível pelo PATH.
Não foram removidos manualmente plugins, ICU ou OpenGL. Builds de diagnóstico
anteriores permanecem separados no diretório ignorado; dois falharam no smoke test
antes do isolamento de ambiente. Não utilizá-los como candidatos.

O popup com caminho do resultado é ajuste de fonte posterior ao pacote testado.
O número de versão já compilado não deve ser sobrescrito para incorporar esse ajuste.
Ainda faltam validação GPU/NVEncC, corpus real e Windows limpo. Ver o estado de cada
etapa no plano: a implementação local não significa que todos os critérios de
aprovação da beta estejam atendidos.
