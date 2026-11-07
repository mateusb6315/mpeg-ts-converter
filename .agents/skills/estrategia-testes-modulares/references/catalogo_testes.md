# Catálogo de padrões de teste (pytest)

## Unitário puro
```python
def test_formatar_duracao_negativa_retorna_traco():
    assert formatar_duracao(-1.0) == "—"
```

## Parametrizado (limites)
```python
@pytest.mark.parametrize("entrada,esperado", [(0, "0 bytes"), (1536, "1,5 KB"), (-1, "—")])
def test_formatar_tamanho(entrada, esperado):
    assert formatar_tamanho(entrada) == esperado
```

## Arquivos temporários e variável de ambiente
```python
def test_salvar_atualiza_ambiente(tmp_path, monkeypatch):
    exe = tmp_path / "ferramenta.exe"; exe.write_bytes(b"MZ")
    chamadas = []
    monkeypatch.setattr("servicos.cfg._persistir", lambda n, v: chamadas.append((n, v)))
    assert salvar(exe) is True
    assert chamadas
```

## Controlador com dublês e diálogo substituído
```python
janela.perguntar_selecao_manual = lambda: False
janela.exibir_popup_download = lambda: popups.append(True)
ctrl = Controlador(janela, verificar=lambda: None, salvar=lambda p: p.is_file())
ctrl._ao_nao_identificar()
assert janela.esta_botao_visivel() is True and popups == [True]
```

## Evento de mouse sintético (GUI offscreen)
```python
evento = QMouseEvent(QMouseEvent.Type.MouseButtonPress, QPointF(5, 5),
                     Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier)
zona.mousePressEvent(evento)
```

## Trabalhador síncrono
Chame `trabalhador.executar()` direto e conecte sinais a listas (`lista.append`).

## Regressão
```python
def test_regressao_progresso_nao_regride_com_valor_menor():
    assert calcular(200, 1000, anterior=25.0) == 25.0
```

## Fuzz com seed
```python
def test_parser_nao_levanta_com_lixo():
    rng = random.Random(42)
    for _ in range(10_000):
        linha = "".join(chr(rng.randint(0, 0x2FF)) for _ in range(rng.randint(0, 200)))
        parsear_segmento_progresso(linha)   # contrato: não levanta
```

## Estresse / soak (marcado)
```python
@pytest.mark.slow
def test_soak_ciclos_da_janela():
    for _ in range(1000):
        janela.exibir_inicio_conversao("a.ts", "C:/a.ts")
        janela.exibir_estado_inicial()
    assert janela._ocupada is False
```

## Concorrência
```python
@pytest.mark.slow
def test_progresso_monotonico_com_threads():
    # N threads chamam callback com valores crescentes; o último valor visto deve ser o máximo
    ...
```

## Arquitetura como teste
```python
def test_arquitetura_sem_violacoes():
    assert auditar_projeto(Path(".")) == []
```

## `pytest.ini` sugerido
```ini
[pytest]
markers =
    slow: testes de estresse/carga/soak (excluir com -m "not slow")
```
