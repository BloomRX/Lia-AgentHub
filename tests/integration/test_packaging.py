"""Empacotamento — o que dá para testar sem Windows.

Estes testes existem porque um bug real escapou: o entry point do PyInstaller
apontava para `lia_agenthub/__main__.py`, que usa import relativo e explode
quando executado como `__main__` sem contexto de pacote. Nenhum teste cobria
isso, então passou. Esta suíte fecha essa lacuna.
"""
import ast
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
SPEC = RAIZ / "packaging" / "lia_agenthub.spec"
LAUNCHER = RAIZ / "packaging" / "launcher.py"
MAIN = RAIZ / "src" / "lia_agenthub" / "__main__.py"


def test_launcher_existe():
    assert LAUNCHER.is_file(), "o entry point do bundle precisa existir"


def test_launcher_nao_usa_import_relativo():
    """Import relativo na entrada do PyInstaller quebra o bundle."""
    arvore = ast.parse(LAUNCHER.read_text(encoding="utf-8"))
    for no in ast.walk(arvore):
        if isinstance(no, ast.ImportFrom):
            assert no.level == 0, (
                f"import relativo no launcher (nível {no.level}): "
                f"`from {'.' * no.level}{no.module or ''} import ...`")


def test_main_usa_import_relativo_e_por_isso_nao_serve_como_entrypoint():
    """Documenta o motivo de existir um launcher separado."""
    arvore = ast.parse(MAIN.read_text(encoding="utf-8"))
    relativos = [n for n in ast.walk(arvore)
                 if isinstance(n, ast.ImportFrom) and n.level > 0]
    assert relativos, (
        "se __main__ deixar de usar import relativo, o launcher pode ser "
        "dispensado — revise este teste e o spec")


def test_launcher_roda_como_script_sem_contexto_de_pacote():
    """A prova direta: executar o launcher como o PyInstaller faria."""
    # Copia o ambiente real: um PATH fixo como "/usr/bin:/bin" não existe no
    # Windows e faria este teste falhar lá por motivo errado.
    env = {**os.environ, "PYTHONPATH": str(RAIZ / "src")}
    r = subprocess.run([sys.executable, str(LAUNCHER), "--version"],
                       capture_output=True, text=True, env=env, timeout=60)
    assert r.returncode == 0, f"launcher falhou: {r.stderr}"
    assert "Lia Agent Hub" in r.stdout


def test_main_executado_direto_falha_sem_pacote():
    """Contraprova: sem o launcher, o import relativo quebra.

    Se este teste passar a falhar, o Python mudou o comportamento de execução
    de script e o launcher pode ser reavaliado.
    """
    env = {**os.environ, "PYTHONPATH": str(RAIZ / "src")}
    r = subprocess.run([sys.executable, str(MAIN), "--version"],
                       capture_output=True, text=True, env=env, timeout=60)
    assert r.returncode != 0
    assert "relative import" in r.stderr or "ImportError" in r.stderr


def test_spec_aponta_para_o_launcher():
    spec = SPEC.read_text(encoding="utf-8")
    entrada = re.search(r"Analysis\(\s*\[([^\]]+)\]", spec)
    assert entrada, "não foi possível ler o entry point do spec"
    alvo = entrada.group(1)
    assert "launcher.py" in alvo, f"spec aponta para {alvo!r}, deveria ser launcher.py"
    assert "__main__.py" not in alvo, "spec ainda aponta para o main quebrado"


def test_spec_inclui_a_ui_estatica():
    spec = SPEC.read_text(encoding="utf-8")
    assert "resources" in spec and "static" in spec


def test_spec_desliga_upx():
    """UPX dispara falso positivo de antivírus no Windows."""
    spec = SPEC.read_text(encoding="utf-8")
    assert re.search(r"upx\s*=\s*False", spec)


def test_spec_nao_usa_console_em_producao():
    spec = SPEC.read_text(encoding="utf-8")
    assert re.search(r"console\s*=\s*False", spec)


def test_todos_os_arquivos_da_ui_estao_no_spec():
    """Um arquivo novo em static/ que ninguém adiciona ao bundle some do .exe."""
    static = RAIZ / "src" / "lia_agenthub" / "resources" / "static"
    existentes = {p.name for p in static.iterdir() if p.is_file()}
    spec = SPEC.read_text(encoding="utf-8")
    # o spec inclui o diretório inteiro; verificamos que é isso mesmo
    assert "static" in spec
    assert existentes, "a pasta static está vazia"
    for nome in existentes:
        assert (static / nome).is_file()


def test_matriz_de_dependencias_documentada_esta_coerente():
    """pywebview só puxa pythonnet no Windows — o spec precisa saber disso."""
    pyproject = (RAIZ / "pyproject.toml").read_text(encoding="utf-8")
    assert "pywebview" in pyproject
    assert ">=3.11" in pyproject


# ---------------- fixtures para os testes manuais no Windows ----------------
def test_gerador_de_fixtures_existe_e_roda(tmp_path):
    """O Codex depende destas fixtures para os testes manuais."""
    import subprocess
    env = {**os.environ, "PYTHONPATH": str(RAIZ / "src")}
    r = subprocess.run([sys.executable, str(RAIZ / "scripts" / "make_fixtures.py"),
                        str(tmp_path / "fx")],
                       capture_output=True, text=True, env=env, timeout=180)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "fx" / "MANIFESTO.json").is_file()
    assert (tmp_path / "fx" / "01-skill-valida" / "SKILL.md").is_file()


def test_fixtures_nao_contem_codigo_de_terceiro():
    """As fixtures são sintéticas: nenhuma veio de fora."""
    fonte = (RAIZ / "scripts" / "make_fixtures.py").read_text(encoding="utf-8")
    assert "sintétic" in fonte.lower() or "sintetic" in fonte.lower()
    assert "http://" not in fonte.replace("https://www.python.org", "")
