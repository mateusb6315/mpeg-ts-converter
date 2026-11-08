"""Extração de um único caminho local dos eventos Qt de arraste."""
from pathlib import Path
from PyQt6.QtGui import QDragEnterEvent, QDropEvent


def extrair_caminho_unico(evento: QDragEnterEvent | QDropEvent) -> Path | None:
    """Extrai o Path se o evento de arraste contiver exatamente um arquivo local."""
    dados_mime = evento.mimeData()
    if dados_mime is None or not dados_mime.hasUrls():
        return None
    urls = dados_mime.urls()
    if len(urls) != 1 or not urls[0].isLocalFile():
        return None
    caminho_texto = urls[0].toLocalFile()
    return Path(caminho_texto) if caminho_texto else None
