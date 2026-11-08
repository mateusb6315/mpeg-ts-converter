# Distribuição Windows

Use Python 3.13 e `python -m pip install -r requirements-build.txt`.

```powershell
python scripts/compilar.py
python scripts/compilar_beta.py
```

Ambos solicitam a versão por input e aceitam nome livre válido de pasta Windows.
Também aceitam `--versao`; no CI esse argumento é obrigatório.
Produção fica em `dist/producao/mpeg-ts-converter <versao>`; beta em
`prototypes/beta/mpeg-ts-converter <versao>`.
Versões podem ser reutilizadas; se a pasta já existir, uma nova pasta numerada é criada.
O build não consulta nem registra histórico de versões.

Após o PyInstaller, o script tenta mover a pasta gerada para o destino. Em caso
de acesso negado, tenta novamente e, se necessário, tenta copiar os arquivos.
Se a cópia falhar, confira as permissões de leitura e escrita e se outro processo
está bloqueando os arquivos. Bloqueios transitórios foram simulados em testes;
a causa de um erro específico precisa ser investigada no ambiente afetado.

Cada pacote contém executável, runtime, README, licença, licenças coletadas das
bibliotecas instaladas e build.json com commit, ambiente e hashes. A coleta não
substitui uma revisão do inventário de licenças antes de distribuição pública.
O build local pode registrar Git sujo; publicação exige Git limpo no manifesto.

```powershell
python scripts/release.py --artefato "prototypes/beta/mpeg-ts-converter 0.0.3-beta"
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
