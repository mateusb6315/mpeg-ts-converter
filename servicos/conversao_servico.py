"""Serviço de execução da conversão NVEncC com emissão de progresso e log."""

from dataclasses import dataclass, field
from collections import deque
import logging
from pathlib import Path
import queue
import re
import subprocess
import threading
from typing import BinaryIO, Callable

from config.configuracoes import (
    LIMITE_BUFFER_SEGMENTO_BYTES,
    TAXA_QUADROS_SAIDA,
    TIMEOUT_SONDAGEM_SEGUNDOS,
    VERSAO_MINIMA_NVENC_SINCRONIA,
)
from modelos.conversao import (
    LinhaLog,
    SegmentoProgresso,
    calcular_percentual_progresso,
    calcular_total_quadros,
    parsear_segmento_progresso,
    validar_fluxos_audio,
)
from servicos.arquivo_servico import (
    localizar_executavel_nvenc,
    sondar_duracao_arquivo,
    sondar_fluxos_midia,
)
from utilitarios.formatacao import citar_argumento_comando
from servicos.processo_recursos import liberar_processo

REGISTRADOR = logging.getLogger(__name__)
CallbackProgresso = Callable[[float], None]
FLAGS_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class ErroConversao(Exception):
    """Exceção levantada quando ocorre falha ou cancelamento na conversão."""


@dataclass
class _ContextoExecucao:
    """Agrupa o estado interno de uma execução do subprocesso NVEncC."""

    comando_texto: str
    total_quadros: int | None
    ao_progredir: CallbackProgresso
    cancelamento: threading.Event | None = None
    caminho_log: Path | None = None
    percentual_atual: float = 0.0
    log_stdout: deque[str] = field(default_factory=lambda: deque(maxlen=1000))
    log_stderr: deque[str] = field(default_factory=lambda: deque(maxlen=1000))

def converter_arquivo(
    origem: Path,
    ao_progredir: CallbackProgresso,
    evento_cancelamento: threading.Event | None = None,
) -> Path:
    """Executa a conversão completa do arquivo .ts para .mkv via NVEncC."""
    from servicos.pipeline_conversao import executar_conversao
    return executar_conversao(origem, ao_progredir, evento_cancelamento)

def _obter_executavel_validado() -> Path:
    """Localiza o binário do NVEncC ou levanta ErroConversao caso ausente."""
    executavel = localizar_executavel_nvenc()
    if not executavel or not executavel.is_file():
        raise ErroConversao(
            "Executável NVEncC não encontrado. Configure a variável 'nvenc64'."
        )
    return executavel

def _verificar_versao_nvenc(executavel: Path) -> None:
    """Registra aviso caso a versão do NVEncC seja anterior à correção 9.18."""
    try:
        res = subprocess.run(
            [str(executavel), "--version"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=TIMEOUT_SONDAGEM_SEGUNDOS, check=False, creationflags=FLAGS_SEM_JANELA,
        )
        match = re.search(r"NVEncC[^\r\n]*?\b(\d+)\.(\d+)", f"{res.stdout}\n{res.stderr}", re.I)
        if match and (int(match[1]), int(match[2])) < VERSAO_MINIMA_NVENC_SINCRONIA:
            REGISTRADOR.warning("NVEncC %s.%s anterior à 9.18.", match[1], match[2])
    except (OSError, subprocess.SubprocessError):
        pass

def _criar_contexto_execucao(
    executavel: Path, argumentos: list[str], origem: Path, ao_progredir: CallbackProgresso
) -> _ContextoExecucao:
    """Monta o contexto inicial da conversão com o comando formatado e total de quadros."""
    args_citados = " ".join(citar_argumento_comando(arg) for arg in argumentos)
    total = calcular_total_quadros(sondar_duracao_arquivo(origem), TAXA_QUADROS_SAIDA)
    return _ContextoExecucao(f'"{executavel}" {args_citados}', total, ao_progredir)

def _executar_processo_nvenc(
    executavel: Path, argumentos: list[str], contexto: _ContextoExecucao
) -> int:
    """Inicia o subprocesso NVEncC, consome a saída em tempo real e retorna o exit code."""
    fila: queue.Queue[tuple[str, bytes | None]] = queue.Queue(maxsize=128)
    processo: subprocess.Popen[bytes] | None = None
    leitores = []
    try:
        processo = subprocess.Popen(
            [str(executavel), *argumentos],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=0, creationflags=FLAGS_SEM_JANELA,
        )
        leitores = _iniciar_leitores_fluxo(processo, fila)
        _consumir_fila_saida(fila, contexto, processo)
        codigo = processo.wait(timeout=5)
        for leitor in leitores:
            leitor.join(timeout=1.0)
        return codigo
    except BaseException:
        if processo is not None and processo.poll() is None:
            processo.kill()
            processo.wait(timeout=5)
        raise
    finally:
        liberar_processo(processo, fila, leitores)


def _iniciar_leitores_fluxo(
    processo: subprocess.Popen[bytes], fila: queue.Queue[tuple[str, bytes | None]]
) -> list[threading.Thread]:
    """Cria e inicia threads daemon para leitura byte a byte de stdout e stderr."""
    fila.parada = threading.Event()
    assert processo.stdout is not None and processo.stderr is not None
    leitores = [
        threading.Thread(target=_bombar_fluxo, args=("stdout", processo.stdout, fila), daemon=True),
        threading.Thread(target=_bombar_fluxo, args=("stderr", processo.stderr, fila), daemon=True),
    ]
    for leitor in leitores:
        leitor.start()
    return leitores

def _bombar_fluxo(
    canal: str, fluxo: BinaryIO, fila: queue.Queue[tuple[str, bytes | None]]
) -> None:
    """Lê bytes individuais de um stream do processo e os enfileira."""
    try:
        while bloco := fluxo.read(4096):
            if not _enfileirar(fila, (canal, bloco)):
                return
    finally:
        _enfileirar(fila, (canal, None))

def _consumir_fila_saida(
    fila: queue.Queue[tuple[str, bytes | None]],
    contexto: _ContextoExecucao,
    processo: subprocess.Popen[bytes],
) -> None:
    """Reconstrói linhas a partir dos bytes da fila e processa progresso e logs."""
    segmentos = {"stdout": bytearray(), "stderr": bytearray()}
    encerrados = 0
    while encerrados < 2 or processo.poll() is None:
        if contexto.cancelamento is not None and contexto.cancelamento.is_set():
            processo.kill()
            processo.wait(timeout=5)
            raise ErroConversao("Conversão cancelada pelo usuário.")
        try:
            canal, valor = fila.get(timeout=0.1)
        except queue.Empty:
            continue
        if valor is None:
            encerrados += 1
        else:
            for byte in valor:
                _acumular_ou_processar_byte(canal, byte, segmentos[canal], contexto)
    for canal, buffer in segmentos.items():
        if buffer:
            _processar_segmento(canal, buffer.decode("utf-8", errors="replace"), contexto)

def _acumular_ou_processar_byte(
    canal: str, valor: int, buffer: bytearray, contexto: _ContextoExecucao
) -> None:
    """Acumula byte no buffer ou dispara o processamento ao encontrar quebra de linha."""
    if valor in (10, 13):
        if buffer:
            _processar_segmento(canal, buffer.decode("utf-8", errors="replace"), contexto)
            buffer.clear()
        return
    buffer.append(valor)
    if len(buffer) > LIMITE_BUFFER_SEGMENTO_BYTES:
        destino = contexto.log_stdout if canal == "stdout" else contexto.log_stderr
        destino.append(buffer.decode("utf-8", errors="replace"))
        buffer.clear()

def _processar_segmento(canal: str, texto: str, contexto: _ContextoExecucao) -> None:
    """Classifica um segmento decodificado e atualiza o progresso ou o log."""
    analisado = parsear_segmento_progresso(texto)
    if isinstance(analisado, SegmentoProgresso):
        contexto.percentual_atual = calcular_percentual_progresso(
            analisado.quadros_codificados, contexto.total_quadros,
            contexto.percentual_atual, analisado.percentual_direto,
        )
        contexto.ao_progredir(contexto.percentual_atual)
    elif isinstance(analisado, LinhaLog):
        (contexto.log_stdout if canal == "stdout" else contexto.log_stderr).append(analisado.texto)
        if contexto.caminho_log is not None:
            try:
                with contexto.caminho_log.open("a", encoding="utf-8-sig") as fluxo:
                    fluxo.write(f"[{canal}] {analisado.texto}\n")
            except OSError:
                contexto.caminho_log = None

def _gravar_arquivo_log_codificacao(
    caminho_log: Path, codigo_saida: int, contexto: _ContextoExecucao
) -> None:
    """Salva o arquivo de log detalhado da conversão em UTF-8 com BOM."""
    estimado = contexto.total_quadros if contexto.total_quadros else "indeterminado"
    linhas = [
        f"CMD: {contexto.comando_texto}", f"ExitCode: {codigo_saida}",
        f"TotalFrames(estimado): {estimado}", "---- stdout ----",
        *contexto.log_stdout, "---- stderr (nao-progresso) ----", *contexto.log_stderr,
    ]
    try:
        with caminho_log.open("a", encoding="utf-8-sig") as fluxo:
            fluxo.write("\n".join(linhas) + "\n")
    except OSError as erro:
        REGISTRADOR.warning("Não foi possível gravar log da conversão: %s", erro)

def _registrar_validacao_audio(
    caminho_saida: Path, fluxos_origem: list[dict] | None
) -> None:
    """Valida as faixas de áudio do arquivo gerado e registra no log da aplicação."""
    fluxos_saida = sondar_fluxos_midia(caminho_saida)
    if fluxos_origem is None or fluxos_saida is None:
        REGISTRADOR.info("Validação de áudio indisponível (ffprobe ausente ou falhou).")
        return
    problemas = validar_fluxos_audio(fluxos_origem, fluxos_saida)
    if problemas:
        REGISTRADOR.warning("Diferenças de áudio detectadas: %s", "; ".join(problemas))
    else:
        REGISTRADOR.info("Validação de áudio concluída sem divergências.")

def _enfileirar(fila, item) -> bool:
    """Aplica contrapressão sem prender leitores após cancelamento."""
    while not fila.parada.is_set():
        try:
            fila.put(item, timeout=0.1)
            return True
        except queue.Full:
            continue
    return False
