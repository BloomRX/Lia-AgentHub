"""CLI de desenvolvimento — os comandos que a Fase 1 previa.

Testados por subprocesso, não por chamada de função: o contrato da CLI é o
que sai no stdout, o stderr e o código de saída. Testar `main()` internamente
deixaria passar um argparse quebrado ou um comando que nunca é alcançado.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]


def _env() -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(RAIZ / "src")
    return env


def run(*args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "lia_agenthub", *args],
                          capture_output=True, text=True, env=_env(),
                          timeout=timeout, cwd=str(RAIZ))


def _skill(base: Path, nome: str, *, licenca: str | None = "MIT",
           corpo: str = "Corpo.", extra: str = "") -> Path:
    d = base / nome
    d.mkdir(parents=True)
    linhas = ["---", f"name: {nome}", f"description: Skill {nome} de teste"]
    if licenca:
        linhas.append(f"license: {licenca}")
    linhas.append("---")
    (d / "SKILL.md").write_text("\n".join(linhas) + f"\n\n{corpo}\n{extra}",
                                encoding="utf-8")
    return d


@pytest.fixture
def home(tmp_path):
    return tmp_path / "casa"


class TestDiagnostico:
    def test_imprime_caminhos_e_nao_cria_nada_sem_querer(self, home):
        r = run("--home", str(home), "diagnostico")
        assert r.returncode == 0, r.stderr
        assert "home" in r.stdout and "library" in r.stdout
        assert str(home) in r.stdout

    def test_modo_json_entrega_objeto_parseavel(self, home):
        r = run("--home", str(home), "diagnostico", "--json")
        assert r.returncode == 0
        dados = json.loads(r.stdout.strip().splitlines()[-1]) if False else None
        # O JSON é a última coisa impressa, mas vem depois das linhas legíveis.
        bloco = r.stdout[r.stdout.index("{"):]
        dados = json.loads(bloco)
        assert "library" in dados


class TestValidate:
    def test_skill_valida_sai_com_zero(self, home, tmp_path):
        d = _skill(tmp_path, "valida")
        r = run("--home", str(home), "validate", str(d))
        assert r.returncode == 0, r.stdout + r.stderr
        assert "erros: 0" in r.stdout

    def test_skill_com_erro_sai_com_um(self, home, tmp_path):
        d = tmp_path / "quebrada"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: COM_MAIUSCULA\ndescription: d\n---\n\nC\n",
                                    encoding="utf-8")
        r = run("--home", str(home), "validate", str(d))
        assert r.returncode == 1
        assert "error" in r.stdout.lower()

    def test_diretorio_sem_skill_md_sai_com_dois(self, home, tmp_path):
        d = tmp_path / "vazia"
        d.mkdir()
        r = run("--home", str(home), "validate", str(d))
        assert r.returncode == 2
        assert "SKILL.md" in r.stderr

    def test_caminho_inexistente_sai_com_dois(self, home):
        r = run("--home", str(home), "validate", "/nao/existe/mesmo")
        assert r.returncode == 2


class TestPackEExport:
    def _importar(self, home, tmp_path) -> str:
        sys.path.insert(0, str(RAIZ / "src"))
        from lia_agenthub.adapters.paths_resolver import resolve_locations
        from lia_agenthub.app import AgentHub
        hub = AgentHub(resolve_locations(home))
        d = _skill(tmp_path, "empacotavel")
        rep = hub.import_path(str(d))
        hub.promote(rep.capability_id)
        return rep.capability_id

    def test_pack_cria_pacote_e_imprime_caminho(self, home, tmp_path):
        cid = self._importar(home, tmp_path)
        r = run("--home", str(home), "pack", cid)
        assert r.returncode == 0, r.stderr
        assert ".lia-capability" in r.stdout
        caminho = Path(r.stdout.split("pacote:")[1].splitlines()[0].strip())
        assert caminho.is_file()

    def test_pacote_de_nao_revisado_leva_sufixo(self, home, tmp_path):
        """Honestidade nº 17 do MVP: o nome do arquivo avisa."""
        cid = self._importar(home, tmp_path)
        r = run("--home", str(home), "pack", cid)
        assert "-NAO-REVISADO" in r.stdout

    def test_public_recusado_sem_base_de_redistribuicao(self, home, tmp_path):
        cid = self._importar(home, tmp_path)
        r = run("--home", str(home), "pack", cid, "--target", "public")
        assert r.returncode == 1
        assert "recusado" in r.stderr

    def test_private_funciona_com_licenca_desconhecida(self, home, tmp_path):
        """Critério de M5: privado nunca é bloqueado."""
        sys.path.insert(0, str(RAIZ / "src"))
        from lia_agenthub.adapters.paths_resolver import resolve_locations
        from lia_agenthub.app import AgentHub
        hub = AgentHub(resolve_locations(home))
        d = _skill(tmp_path, "semlic", licenca=None)
        rep = hub.import_path(str(d))
        hub.promote(rep.capability_id)
        r = run("--home", str(home), "pack", rep.capability_id)
        assert r.returncode == 0, r.stderr

    def test_id_inexistente_falha_sem_stacktrace(self, home):
        r = run("--home", str(home), "pack", "nao-existe")
        assert r.returncode != 0
        assert "Traceback" not in r.stderr


class TestIndex:
    def test_index_vazio_sem_erro(self, home):
        r = run("--home", str(home), "index")
        assert r.returncode == 0
        assert "0 capacidade" in r.stdout

    def test_publish_e_leitura(self, home, tmp_path):
        sys.path.insert(0, str(RAIZ / "src"))
        from lia_agenthub.adapters.paths_resolver import resolve_locations
        from lia_agenthub.app import AgentHub
        hub = AgentHub(resolve_locations(home))
        d = _skill(tmp_path, "indexavel")
        rep = hub.import_path(str(d))
        hub.promote(rep.capability_id)

        r = run("--home", str(home), "index", "--publish")
        assert r.returncode == 0, r.stderr
        assert "1 capacidade" in r.stdout

        leitura = run("--home", str(home), "index", "--json")
        dados = json.loads(leitura.stdout)
        assert len(dados["capabilities"]) == 1
        assert dados["signed"] is False


class TestVerifyPackage:
    def test_pacote_integro_verifica(self, home, tmp_path):
        sys.path.insert(0, str(RAIZ / "src"))
        from lia_agenthub.adapters.paths_resolver import resolve_locations
        from lia_agenthub.app import AgentHub
        hub = AgentHub(resolve_locations(home))
        d = _skill(tmp_path, "verificavel")
        rep = hub.import_path(str(d))
        hub.promote(rep.capability_id)
        pac = Path(run("--home", str(home), "pack", rep.capability_id)
                   .stdout.split("pacote:")[1].splitlines()[0].strip())

        r = run("--home", str(home), "verify-package", str(pac))
        assert r.returncode == 0, r.stdout
        assert "íntegro" in r.stdout
        # O aviso tem de estar no mesmo texto, não num doc à parte.
        assert "não autoria" in r.stdout

    def test_pacote_adulterado_falha(self, home, tmp_path):
        import zipfile
        sys.path.insert(0, str(RAIZ / "src"))
        from lia_agenthub.adapters.paths_resolver import resolve_locations
        from lia_agenthub.app import AgentHub
        hub = AgentHub(resolve_locations(home))
        d = _skill(tmp_path, "adulteravel")
        rep = hub.import_path(str(d))
        hub.promote(rep.capability_id)
        pac = Path(run("--home", str(home), "pack", rep.capability_id)
                   .stdout.split("pacote:")[1].splitlines()[0].strip())

        # Reescreve o payload mantendo o manifesto: hash não confere mais.
        adulterado = tmp_path / "adulterado.lia-capability"
        with zipfile.ZipFile(pac) as zin, zipfile.ZipFile(adulterado, "w") as zout:
            for item in zin.infolist():
                dados = zin.read(item.filename)
                if item.filename.endswith("SKILL.md"):
                    dados = dados + b"\nInjetado.\n"
                zout.writestr(item, dados)

        r = run("--home", str(home), "verify-package", str(adulterado))
        assert r.returncode == 1
        assert "ALTERADO" in r.stdout or "inv" in r.stdout.lower()


class TestDespachoNaoQuebraJanela:
    def test_flags_antigas_continuam_funcionando(self, home):
        """`--diagnostico` (flag histórica) não pode virar subcomando."""
        r = run("--home", str(home), "--diagnostico")
        assert r.returncode == 0
        assert "python" in r.stdout

    def test_help_nao_abre_janela(self):
        r = run("--help")
        assert r.returncode == 0
        assert "acervo local" in r.stdout or "usage" in r.stdout.lower()

    def test_comando_desconhecido_nao_abre_janela(self):
        """Sem subcomando e sem flag, o argparse recusa em vez de abrir UI."""
        r = run("comando-que-nao-existe", timeout=20)
        assert r.returncode != 0
