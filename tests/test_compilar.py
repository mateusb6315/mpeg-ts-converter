"""Testes do versionamento e da publicação das compilações."""

import json
import subprocess

import pytest

from scripts.compilar import compilar, proxima_versao


@pytest.fixture(autouse=True)
def _versao_pyinstaller_falsa(monkeypatch):
    """Os testes simulados não exigem a instalação do PyInstaller."""
    monkeypatch.setattr("scripts.distribuicao.compilador.importlib.metadata.version", lambda nome: "teste")
    monkeypatch.setattr("scripts.distribuicao.manifesto.preparar_pacote",
                        lambda pasta, versao, canal: {})


def _compilador_falso(comando, **kwargs):
    """Cria uma distribuição de teste no local solicitado ao PyInstaller."""
    destino = comando[comando.index("--distpath") + 1]
    from pathlib import Path
    pasta = Path(destino) / comando[comando.index("--name") + 1]
    pasta.mkdir(parents=True)
    (pasta / "mpeg-ts-converter.exe").write_bytes(b"teste")


def _historico(diretorio):
    return json.loads((diretorio / "historico.json").read_text(encoding="utf-8"))


def test_proxima_versao_considera_pastas_existentes(tmp_path):
    """A numeração é inteira, não decimal, e considera a maior pasta existente."""
    (tmp_path / "beta 0.9").mkdir()
    (tmp_path / "beta 0.2").mkdir()
    assert proxima_versao(tmp_path, []) == 10


def test_compilacao_desabilita_upx(tmp_path):
    """Evita compressão UPX automática e possíveis problemas com binários Qt."""
    def verificar(comando, **kwargs):
        assert "--noupx" in comando
        _compilador_falso(comando, **kwargs)
    compilar(tmp_path, executar=verificar)


def test_saida_do_pyinstaller_e_suprimida_no_sucesso(tmp_path, capsys):
    """A saída do PyInstaller é capturada e substituída por uma mensagem única."""
    def compilar_silencioso(comando, **kwargs):
        assert kwargs.get("capture_output") is True
        _compilador_falso(comando, **kwargs)
        return subprocess.CompletedProcess(comando, 0, stdout="LINHA DO PYINSTALLER")
    compilar(tmp_path, executar=compilar_silencioso)
    saida = capsys.readouterr().out
    assert "Fazendo a compilação..." in saida
    assert "LINHA DO PYINSTALLER" not in saida


def test_falha_do_pyinstaller_exibe_ultimas_linhas(tmp_path, capsys):
    """Em caso de falha, a saída do PyInstaller é mostrada para diagnóstico."""
    def falhar(comando, **kwargs):
        raise subprocess.CalledProcessError(1, comando, output="ERRO DE IMPORTAÇÃO")
    with pytest.raises(subprocess.CalledProcessError):
        compilar(tmp_path, executar=falhar)
    assert "ERRO DE IMPORTAÇÃO" in capsys.readouterr().out


def test_compila_sequencialmente_e_emite_status(tmp_path, capsys):
    """Publicações consecutivas registram e anunciam cada versão."""
    compilar(tmp_path, executar=_compilador_falso)
    compilar(tmp_path, executar=_compilador_falso)
    assert (tmp_path / "mpeg-ts-converter beta 0.1" / "mpeg-ts-converter.exe").is_file()
    assert (tmp_path / "mpeg-ts-converter beta 0.2" / "mpeg-ts-converter.exe").is_file()
    assert [item["versao"] for item in _historico(tmp_path)] == ["beta 0.1", "beta 0.2"]
    assert _historico(tmp_path)[0]["caminho"] == "mpeg-ts-converter beta 0.1"
    saida = capsys.readouterr().out
    assert "beta 0.1" in saida and "Fazendo a compilação..." in saida
    assert "concluída" in saida


def test_json_vazio_gera_primeira_versao(tmp_path):
    """Um historico.json vazio equivale a nenhuma versão registrada."""
    (tmp_path / "historico.json").write_text("", encoding="utf-8")
    compilar(tmp_path, executar=_compilador_falso)
    assert (tmp_path / "mpeg-ts-converter beta 0.1" / "mpeg-ts-converter.exe").is_file()
    assert [item["versao"] for item in _historico(tmp_path)] == ["beta 0.1"]


def test_json_somente_espacos_gera_primeira_versao(tmp_path):
    """Espaços e quebras de linha são tratados como arquivo vazio."""
    (tmp_path / "historico.json").write_text(" \n\t\n", encoding="utf-8")
    compilar(tmp_path, executar=_compilador_falso)
    assert [item["versao"] for item in _historico(tmp_path)] == ["beta 0.1"]


def test_json_inexistente_gera_primeira_versao(tmp_path):
    """Sem historico.json, a primeira compilação é beta 0.1."""
    compilar(tmp_path, executar=_compilador_falso)
    assert (tmp_path / "mpeg-ts-converter beta 0.1" / "mpeg-ts-converter.exe").is_file()


def test_versao_removida_nao_e_reutilizada(tmp_path):
    """O histórico preserva versões cujas pastas foram apagadas."""
    (tmp_path / "historico.json").write_text(
        json.dumps([{"versao": "beta 0.12"}]), encoding="utf-8"
    )
    compilar(tmp_path, executar=_compilador_falso)
    assert (tmp_path / "mpeg-ts-converter beta 0.13" / "mpeg-ts-converter.exe").is_file()


def test_compilacao_falha_sem_publicar_nem_consumir_versao(tmp_path):
    """Uma falha do PyInstaller não produz uma versão concluída."""
    def falhar(comando, **kwargs):
        raise subprocess.CalledProcessError(1, comando)
    with pytest.raises(subprocess.CalledProcessError):
        compilar(tmp_path, executar=falhar)
    assert not (tmp_path / "mpeg-ts-converter beta 0.1").exists()
    assert not (tmp_path / "historico.json").exists()
    compilar(tmp_path, executar=_compilador_falso)
    assert (tmp_path / "mpeg-ts-converter beta 0.1").exists()


def test_historico_invalido_interrompe_sem_sobrescrever(tmp_path):
    """Um histórico inválido requer correção manual antes de prosseguir."""
    arquivo = tmp_path / "historico.json"
    arquivo.write_text("conteúdo inválido", encoding="utf-8")
    with pytest.raises(ValueError, match="histórico"):
        compilar(tmp_path, executar=_compilador_falso)
    assert arquivo.read_text(encoding="utf-8") == "conteúdo inválido"


def test_recupera_publicacao_interrompida_antes_do_registro(tmp_path):
    """Uma pasta publicada e ausente do histórico é registrada na próxima execução."""
    pasta = tmp_path / "beta 0.4"
    pasta.mkdir()
    (pasta / "p_broadcast.exe").write_bytes(b"teste")
    (pasta / "build.json").write_text(
        json.dumps({"versao": "beta 0.4", "data": "2026-01-01"}), encoding="utf-8"
    )
    compilar(tmp_path, executar=_compilador_falso)
    assert [item["versao"] for item in _historico(tmp_path)] == ["beta 0.4", "beta 0.5"]
    assert (tmp_path / "mpeg-ts-converter beta 0.5").is_dir()


def test_executavel_ausente_nao_publica_versao(tmp_path):
    """Uma saída incompleta do PyInstaller não é publicada."""
    with pytest.raises(RuntimeError, match="executável"):
        compilar(tmp_path, executar=lambda *args, **kwargs: None)
    assert not (tmp_path / "mpeg-ts-converter beta 0.1").exists()


def test_bloqueio_recusa_outra_compilacao(tmp_path):
    """O bloqueio impede outra execução e é liberado ao terminar."""
    from scripts.compilar import bloqueio
    with bloqueio(tmp_path):
        with pytest.raises(RuntimeError, match="andamento"):
            with bloqueio(tmp_path):
                pass
    with bloqueio(tmp_path):
        pass


def test_log_executavel_usa_pasta_do_usuario(tmp_path, monkeypatch):
    """O executável não depende da permissão de escrita no diretório atual."""
    import sys
    from main import _obter_caminho_log
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    caminho = _obter_caminho_log()
    assert caminho == tmp_path / "Projeto Broadcast" / "projeto_broadcast.log"
    assert caminho.parent.is_dir()
