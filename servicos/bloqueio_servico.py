"""Bloqueio de arquivo liberado pelo sistema ao encerrar o processo."""
import os
from pathlib import Path
from contextlib import contextmanager

@contextmanager
def bloqueio(diretorio: Path):
    """Impede compilações simultâneas e libera o bloqueio ao encerrar o processo."""
    with (diretorio / ".compilacao.lock").open("a+b") as arquivo:
        if arquivo.tell() == 0:
            arquivo.write(b"0")
            arquivo.flush()
        arquivo.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(arquivo.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(arquivo.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as erro:
            raise RuntimeError(
                "Outra compilação está em andamento; aguarde e tente novamente."
            ) from erro
        try:
            yield
        finally:
            if os.name == "nt":
                arquivo.seek(0)
                msvcrt.locking(arquivo.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(arquivo.fileno(), fcntl.LOCK_UN)

