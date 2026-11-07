"""Testes de unidade para as funções puras de formatação em utilitarios/formatacao.py."""

from utilitarios.formatacao import (
    citar_argumento_comando,
    formatar_duracao,
    formatar_percentual,
    formatar_tamanho,
    truncar_texto_meio,
)


def test_formatar_tamanho_em_bytes_retorna_unidade_correta() -> None:
    """Verifica a formatação de tamanhos pequenos abaixo de 1 KB."""
    assert formatar_tamanho(0) == "0 bytes"
    assert formatar_tamanho(512) == "512 bytes"


def test_formatar_tamanho_em_kb_mb_gb_usa_virgula_decimal_ptbr() -> None:
    """Garante que escalas maiores usem separador decimal com vírgula."""
    assert formatar_tamanho(1536) == "1,5 KB"
    assert formatar_tamanho(5 * 1024**2) == "5,0 MB"
    assert formatar_tamanho(int(1.2 * 1024**3)) == "1,2 GB"


def test_formatar_tamanho_negativo_retorna_traco() -> None:
    """Garante retorno seguro para tamanhos inválidos negativos."""
    assert formatar_tamanho(-10) == "—"


def test_formatar_duracao_valida_retorna_padrao_relogio() -> None:
    """Verifica a conversão de segundos para o formato hh:mm:ss."""
    assert formatar_duracao(0) == "00:00:00"
    assert formatar_duracao(95.8) == "00:01:35"
    assert formatar_duracao(3661) == "01:01:01"


def test_formatar_duracao_invalida_ou_nula_retorna_traco() -> None:
    """Garante retorno '—' quando a duração é None, negativa ou infinita."""
    assert formatar_duracao(None) == "—"
    assert formatar_duracao(-1.0) == "—"
    assert formatar_duracao(float("inf")) == "—"


def test_formatar_percentual_limita_entre_zero_e_cem_com_virgula() -> None:
    """Confere se o percentual é limitado ao intervalo [0, 100] em pt-BR."""
    assert formatar_percentual(-5.0) == "0,0%"
    assert formatar_percentual(42.35) == "42,4%"
    assert formatar_percentual(150.0) == "100,0%"
    assert formatar_percentual(float("nan")) == "0,0%"


def test_truncar_texto_meio_preserva_curtos_e_abrevia_longos() -> None:
    """Verifica o truncamento central com reticências em nomes longos."""
    assert truncar_texto_meio("curto.ts", limite=20) == "curto.ts"
    truncado = truncar_texto_meio("arquivo_muito_longo_de_teste_broadcast.ts", limite=15)
    assert len(truncado) == 15
    assert "…" in truncado
    assert truncado.startswith("arquivo")
    assert truncado.endswith(".ts")


def test_citar_argumento_comando_escapa_espacos_e_aspas() -> None:
    """Testa o envelopamento em aspas de argumentos com espaços."""
    assert citar_argumento_comando("--avhw") == "--avhw"
    assert citar_argumento_comando("C:\\Meus Videos\\a.ts") == '"C:\\Meus Videos\\a.ts"'
