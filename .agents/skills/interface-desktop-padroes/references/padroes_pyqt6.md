# Trechos de referência (PyQt6)

## Widget clicável com sinal
```python
class ZonaClicavel(QFrame):
    clicada = pyqtSignal()

    def mousePressEvent(self, evento):
        if evento is not None and self._ativa and evento.button() == Qt.MouseButton.LeftButton:
            self.clicada.emit()
        super().mousePressEvent(evento)
```

## Pergunta Sim/Não com padrão seguro
```python
def exibir_pergunta_sim_nao(pai, texto) -> bool:
    caixa = QMessageBox(pai)
    caixa.setIcon(QMessageBox.Icon.Question)
    caixa.setText(texto)
    sim = caixa.addButton("Sim", QMessageBox.ButtonRole.YesRole)
    nao = caixa.addButton("Não", QMessageBox.ButtonRole.NoRole)
    caixa.setDefaultButton(nao)
    caixa.exec()
    return caixa.clickedButton() == sim
```

## Popup com link clicável
```python
caixa.setTextFormat(Qt.TextFormat.RichText)
caixa.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
caixa.setText('Baixe em <a href="https://exemplo.com">https://exemplo.com</a>')
```

## Seletor com filtro (cancelar = string vazia)
```python
caminho, _ = QFileDialog.getOpenFileName(self, TITULO, diretorio_inicial, "Vídeos (*.ts)")
return caminho
```

## Fluxo condicional (dependência externa ausente)
```
verificar (thread) ──encontrou──► segue (pass), botão oculto
        └─não achou─► pergunta "Sim/Não"
              ├─ Sim ─► seletor ─ válido ─► salva, oculta botão
              │              └─ cancelou/inválido ─┐
              └─ Não ─────────────────────────────┴► popup orientação + mostra botão
botão clicado ─► seletor ─ válido ─► salva, oculta botão
```

## Tema claro forçado
`app.setStyle("Fusion")` + `QPalette` explícita + `styleHints().setColorScheme(Light)`
protegido por `getattr` (versões antigas do Qt não têm).

## Layout compacto
Coluna esquerda (`QVBoxLayout`: zona + botão condicional) | painel (`stretch=1`);
barra de progresso embaixo. Tamanho fixo via `setFixedSize` e constantes de `config/`.
