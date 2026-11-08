"""Transação de saída: reserva, parcial isolado, validação e promoção sem substituir."""
import datetime as dt
import os
from pathlib import Path
import tempfile
from contextlib import contextmanager

from modelos.conversao import construir_argumentos_nvenc, gerar_caminho_saida
from modelos.conversao import selecionar_argumentos_audio
from servicos.arquivo_servico import sondar_fluxos_midia
from servicos import conversao_servico as motor


def verificar_cancelamento(evento) -> None:
    """Interrompe antes de iniciar uma nova fase de I/O."""
    if evento is not None and evento.is_set():
        raise motor.ErroConversao("Conversão cancelada pelo usuário.")


@contextmanager
def reservar_destino(destino: Path):
    """Mantém bloqueio de sistema liberado inclusive em queda do processo."""
    from servicos.bloqueio_servico import bloqueio
    # Cada destino recebe seu próprio diretório de controle persistente.
    reserva = destino.parent / ("." + destino.name + ".reserva")
    reserva.mkdir(exist_ok=True)
    with bloqueio(reserva):
        if destino.exists():
            raise motor.ErroConversao(f"Saída já existe: {destino}")
        yield


def executar_conversao(origem: Path, callback, evento=None) -> Path:
    """Protege resultados anteriores e preserva parcial e log em caso de falha."""
    verificar_cancelamento(evento)
    if not origem.is_file() or origem.stat().st_size == 0:
        raise motor.ErroConversao("Arquivo de entrada ausente ou vazio.")
    destino = gerar_caminho_saida(origem)
    with reservar_destino(destino):
        return _converter_reservado(origem, destino, callback, evento)


def _converter_reservado(origem, destino, callback, evento):
    parcial = Path(tempfile.mkdtemp(prefix=".conversao-", dir=destino.parent)) / "video.mkv"
    carimbo = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log = destino.parent / f"{destino.stem}_encode_{carimbo}.log"
    contexto = motor._ContextoExecucao("Preparando", None, callback, evento)
    codigo = -1
    try:
        executavel = motor._obter_executavel_validado()
        motor._verificar_versao_nvenc(executavel)
        verificar_cancelamento(evento)
        fluxos = sondar_fluxos_midia(origem)
        audio, _ = selecionar_argumentos_audio(fluxos)
        argumentos = construir_argumentos_nvenc(origem, parcial, audio)
        contexto = motor._criar_contexto_execucao(executavel, argumentos, origem, callback)
        contexto.cancelamento = evento
        contexto.caminho_log = log
        verificar_cancelamento(evento)
        codigo = motor._executar_processo_nvenc(executavel, argumentos, contexto)
        verificar_cancelamento(evento)
        if codigo != 0 or not parcial.is_file() or parcial.stat().st_size == 0:
            raise motor.ErroConversao(f"Conversão sem saída válida; código {codigo}.")
        motor._registrar_validacao_audio(parcial, fluxos)
        verificar_cancelamento(evento)
        _promover_parcial(parcial, destino)
        return destino
    except Exception as erro:
        contexto.log_stderr.append(f"{erro}; parcial: {parcial}")
        raise
    finally:
        motor._gravar_arquivo_log_codificacao(log, codigo, contexto)


def _promover_parcial(parcial: Path, destino: Path) -> None:
    """Publica no mesmo volume sem substituir um arquivo existente."""
    if os.name == "nt":
        parcial.rename(destino)
    else:
        os.link(parcial, destino)
        parcial.unlink()
    parcial.parent.rmdir()
