"""Liberação de recursos de subprocessos e leitores."""
import threading


def liberar_processo(processo, fila, leitores) -> None:
    """Libera pipes e coleta leitores após término ou cancelamento."""
    getattr(fila, "parada", threading.Event()).set()
    if processo is not None:
        for fluxo in (processo.stdout, processo.stderr):
            if fluxo is not None:
                fluxo.close()
    for leitor in leitores:
        leitor.join(timeout=2)
