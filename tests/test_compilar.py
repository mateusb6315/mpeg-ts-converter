"""Regressões da compilação com versão livre."""
import subprocess
import pytest
from scripts.distribuicao.compilador import compilar

def _compilador_falso(comando, **kwargs):
    """Cria uma distribuição de teste no local solicitado ao PyInstaller."""
    destino = comando[comando.index("--distpath") + 1]
    from pathlib import Path
    pasta = Path(destino) / comando[comando.index("--name") + 1]
    pasta.mkdir(parents=True)
    (pasta / "mpeg-ts-converter.exe").write_bytes(b"teste")


def test_reutiliza_versao_sem_ler_historico(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.distribuicao.manifesto.preparar_pacote",
                        lambda *args: {})
    (tmp_path / "historico.json").write_text("inválido", encoding="utf-8")
    primeira = compilar(tmp_path, executar=_compilador_falso, versao="ensaio livre")
    segunda = compilar(tmp_path, executar=_compilador_falso, versao="ensaio livre")
    assert primeira.name == "mpeg-ts-converter ensaio livre"
    assert segunda.name == "mpeg-ts-converter ensaio livre (2)"
    assert (primeira / "mpeg-ts-converter.exe").is_file()
    assert (segunda / "mpeg-ts-converter.exe").is_file()


def test_falha_nao_publica(tmp_path):
    def falhar(comando, **kwargs):
        raise subprocess.CalledProcessError(1, comando)
    with pytest.raises(subprocess.CalledProcessError):
        compilar(tmp_path, executar=falhar, versao="teste")
    assert not (tmp_path / "mpeg-ts-converter teste").exists()


def test_log_executavel_usa_pasta_do_usuario(tmp_path, monkeypatch):
    """O executável não depende da permissão de escrita no diretório atual."""
    import sys
    from main import _obter_caminho_log
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    caminho = _obter_caminho_log()
    assert caminho == tmp_path / "Projeto Broadcast" / "projeto_broadcast.log"
    assert caminho.parent.is_dir()
