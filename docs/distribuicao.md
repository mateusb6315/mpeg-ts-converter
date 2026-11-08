# Distribuição Windows

Use Python 3.13 e `python -m pip install -r requirements-build.txt`.

```powershell
python scripts/compilar.py
python scripts/compilar_beta.py
```

Ambos solicitam a versão por input. Produção exige X.Y.Z; beta aceita nome livre
válido de pasta Windows. Convenção recomendada: `0.0.3-beta1`.
Também aceitam `--versao`; no CI esse argumento é obrigatório.
Produção fica em `dist/producao/<versao>`; beta em `prototypes/beta/<versao>`.
Históricos são separados; uma versão registrada nunca é sobrescrita/reutilizada.
O histórico antigo na raiz de prototypes permanece intacto.

Cada pacote contém executável, runtime, README, licença, licenças coletadas das
bibliotecas instaladas e build.json com commit, ambiente e hashes. A coleta não
substitui uma revisão do inventário de licenças antes de distribuição pública.
O build local pode registrar Git sujo; publicação exige Git limpo no manifesto.

```powershell
python scripts/release.py --artefato "prototypes/beta/0.0.3-beta1"
```

Esse comando verifica arquivos e hashes localmente. Publicação exige `--publicar`
e `--notas` com caminho de notas revisadas. Cria rascunho e marca beta como
pré-release, vinculado ao commit do pacote. Recusa tag existente: falhas parciais
exigem conferir o GitHub antes de retomar. Não há retentativa automática destrutiva.
Nomes beta com espaços são válidos localmente, mas não são tags Git válidas.

A validação final exige Windows limpo e mídia/GPU reais. Não remover ICU, OpenGL
ou plugins Qt só pelo tamanho: as otimizações de empacotamento ficam condicionadas
à comprovação de compatibilidade em hardware representativo.

Para diagnóstico, `--console` mantém o console no executável. O build isola PATH e
variáveis de Qt/Python para evitar coleta de DLLs de outros aplicativos.
