"""Testes de unidade para as regras de negócio puras em modelos/conversao.py."""

from pathlib import Path

from modelos.conversao import (
    LinhaLog,
    SegmentoProgresso,
    calcular_percentual_progresso,
    calcular_tempo_restante,
    calcular_total_quadros,
    construir_argumentos_nvenc,
    eh_arquivo_ts,
    gerar_caminho_saida,
    parsear_segmento_progresso,
    selecionar_argumentos_audio,
    validar_fluxos_audio,
)


def test_eh_arquivo_ts_aceita_minusculas_e_maiusculas() -> None:
    """Verifica que extensões .ts e .TS são reconhecidas sem distinção de caixa."""
    assert eh_arquivo_ts(Path("gravacao.ts")) is True
    assert eh_arquivo_ts(Path("C:/Videos/GRAVACAO_HD.TS")) is True
    assert eh_arquivo_ts(Path("captura.Ts")) is True


def test_eh_arquivo_ts_rejeita_outras_extensoes_e_vazio() -> None:
    """Garante rejeição de arquivos com outras extensões ou sem nome."""
    assert eh_arquivo_ts(Path("video.mp4")) is False
    assert eh_arquivo_ts(Path("video.mkv")) is False
    assert eh_arquivo_ts(Path("sem_extensao")) is False
    assert eh_arquivo_ts(Path("")) is False


def test_gerar_caminho_saida_mantem_pasta_e_adiciona_sufixo_bwdif() -> None:
    """Confere se o nome de saída segue exatamente o padrão '_60fps_bwdif.mkv'."""
    origem = Path("C:/Capturas/programa_ao_vivo.ts")
    esperado = Path("C:/Capturas/programa_ao_vivo_60fps_bwdif.mkv")
    assert gerar_caminho_saida(origem) == esperado


def test_calcular_total_quadros_estima_corretamente_em_59_94_fps() -> None:
    """Testa a estimativa de quadros totais após desentrelaçamento bob."""
    assert calcular_total_quadros(10.0, 59.94) == 599
    assert calcular_total_quadros(None) is None
    assert calcular_total_quadros(0.0) is None
    assert calcular_total_quadros(-5.0) is None


def test_calcular_percentual_progresso_limita_e_nunca_regride() -> None:
    """Garante que o percentual fica entre 0 e 99.9 durante a execução e não regride."""
    p1 = calcular_percentual_progresso(250, 1000, percentual_anterior=0.0)
    assert p1 == 25.0
    p2 = calcular_percentual_progresso(200, 1000, percentual_anterior=p1)
    assert p2 == 25.0
    p3 = calcular_percentual_progresso(1200, 1000, percentual_anterior=p2)
    assert p3 == 99.9


def test_calcular_percentual_progresso_usa_percentual_direto_sem_total_quadros() -> None:
    """Verifica fallback para percentual direto quando ffprobe não informou total."""
    pct = calcular_percentual_progresso(100, None, 10.0, percentual_direto=45.5)
    assert pct == 45.5


def test_calcular_tempo_restante_estima_segundos_ou_retorna_none() -> None:
    """Valida o cálculo do tempo restante estimado e os limites de segurança."""
    assert calcular_tempo_restante(0.1, 5.0) is None
    assert calcular_tempo_restante(50.0, 0.2) is None
    assert calcular_tempo_restante(100.0, 20.0) is None
    restante = calcular_tempo_restante(25.0, 10.0)
    assert restante is not None
    assert abs(restante - 30.0) < 1e-6


def test_parsear_segmento_progresso_extrai_quadros_fps_e_bitrate() -> None:
    """Testa o parser de linhas de progresso modernas e legadas do NVEncC."""
    linha = "[25.4%] 1520 frames: 142.5 fps, 12450 kbps, remain 0:00:30, encoded 1520"
    resultado = parsear_segmento_progresso(linha)
    assert isinstance(resultado, SegmentoProgresso)
    assert resultado.quadros_codificados == 1520
    assert resultado.quadros_por_segundo == 142.5
    assert resultado.taxa_bits == "12450 kbps"
    assert resultado.percentual_direto == 25.4


def test_parsear_segmento_progresso_formato_legado_e_linha_log() -> None:
    """Confere formato legado com '%', 'frames' e 'fps' e linhas comuns de log."""
    legado = parsear_segmento_progresso("[50.0%] 500 frames: 60.0 fps, 8000 kb/s")
    assert isinstance(legado, SegmentoProgresso)
    assert legado.quadros_codificados == 500
    comum = parsear_segmento_progresso("NVEncC (x64) 9.31 by rigaya")
    assert isinstance(comum, LinhaLog)
    assert parsear_segmento_progresso("   ") is None


def test_selecionar_argumentos_audio_mapeia_faixas_corretamente() -> None:
    """Verifica geração dos parâmetros --audio-copy conforme faixas detectadas."""
    args_indisp, faixas_indisp = selecionar_argumentos_audio(None)
    assert args_indisp == ["--audio-copy"]
    assert faixas_indisp is None

    fluxos = [
        {"codec_type": "video"},
        {"codec_type": "audio", "channels": 2},
        {"codec_type": "audio", "channels": 6},
    ]
    args, faixas = selecionar_argumentos_audio(fluxos)
    assert args == ["--audio-copy", "1,2"]
    assert faixas is not None and len(faixas) == 2


def test_construir_argumentos_nvenc_preserva_parametros_originais() -> None:
    """Confirma que todos os parâmetros de codificação HEVC BWDIF são mantidos."""
    entrada = Path("entrada.ts")
    saida = Path("saida.mkv")
    args = construir_argumentos_nvenc(entrada, saida, ["--audio-copy", "1"])
    assert "--vpp-bwdif" in args
    assert "mode=bob,order=tff" in args
    assert "-c" in args and "hevc" in args
    assert "--qvbr" in args and "18" in args
    assert args[-2:] == ["-o", "saida.mkv"]


def test_validar_fluxos_audio_detecta_divergencias_e_sincronia() -> None:
    """Verifica detecção de mudança em canais ou deslocamento A/V."""
    origem = [
        {"codec_type": "video", "start_time": "1.000"},
        {"codec_type": "audio", "channels": 2, "channel_layout": "stereo", "start_time": "1.000"},
    ]
    saida_ok = [
        {"codec_type": "video", "start_time": "0.000"},
        {"codec_type": "audio", "channels": 2, "channel_layout": "stereo", "start_time": "0.020"},
    ]
    assert validar_fluxos_audio(origem, saida_ok) == []

    saida_dessinc = [
        {"codec_type": "video", "start_time": "0.000"},
        {"codec_type": "audio", "channels": 6, "channel_layout": "5.1", "start_time": "0.500"},
    ]
    problemas = validar_fluxos_audio(origem, saida_dessinc)
    assert len(problemas) == 2
