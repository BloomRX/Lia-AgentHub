"""IDX-3 — o contrato do índice é consumível SEM o Hub.

Este é o teste que impede M8 de ser uma afirmação não verificada: o doc do MVP
diz que, sem um leitor de referência, publicar um contrato que ninguém jamais
leu não prova nada. Aqui o leitor roda em subprocesso, com `PYTHONPATH`
apontado para um diretório vazio, e prova que não tem acesso ao Hub.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
LEITOR = RAIZ / "docs/examples/independent-reader/read_index.py"


def _skill(base: Path, nome: str, *, versao="1.0.0", licenca=None, extra=""):
    d = base / nome
    d.mkdir(parents=True)
    linhas = ["---", f"name: {nome}", f"description: Skill de teste {nome}",
              f"version: {versao}"]
    if licenca:
        linhas.append(f"license: {licenca}")
    linhas.append("---")
    (d / "SKILL.md").write_text("\n".join(linhas) + "\n\nCorpo.\n" + extra,
                                encoding="utf-8")
    return d


def _ambiente_isolado() -> dict:
    """Ambiente em que `import lia_agenthub` tem de falhar."""
    vazio = Path(__file__).parent / "_vazio_para_idx3"
    vazio.mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k not in
           ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "PYTHONSTARTUP")}
    env["PYTHONPATH"] = str(vazio)
    env["PYTHONNOUSERSITE"] = "1"
    return env


def _rodar(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-S", str(LEITOR), *args],
        capture_output=True, text=True, env=_ambiente_isolado(), timeout=60)


class TestLeitorIndependente:
    def test_o_leitor_roda_sem_o_hub_instalado(self, hub, tmp_path):
        """`-S` desliga site-packages: o Hub não pode ser importado."""
        r = _skill(tmp_path / "a", "isolada", licenca="MIT")
        imp = hub.import_path(str(r))
        hub.promote(imp.capability_id)
        caminho = hub.publish_index()["path"]

        resultado = _rodar(caminho)
        assert resultado.returncode == 0, resultado.stderr
        assert "isolada" in resultado.stdout
        assert "MIT" in resultado.stdout

    def test_o_leitor_nao_importa_lia_agenthub(self):
        """Prova textual: nenhum import do pacote no arquivo de referência."""
        fonte = LEITOR.read_text(encoding="utf-8")
        for linha in fonte.splitlines():
            sem_espaco = linha.strip()
            if sem_espaco.startswith(("import ", "from ")):
                assert "lia_agenthub" not in sem_espaco, linha

    def test_import_do_hub_falha_no_ambiente_do_teste(self):
        """Contraprova: o isolamento é real, não decorativo."""
        env = _ambiente_isolado()
        r = subprocess.run([sys.executable, "-S", "-c", "import lia_agenthub"],
                           capture_output=True, text=True, env=env, timeout=30)
        assert r.returncode != 0
        assert "ModuleNotFoundError" in r.stderr

    def test_imprime_trust_licenca_e_requisitos(self, tmp_path):
        """Os três campos que o critério de M8 exige explicitamente."""
        from lia_agenthub.adapters.paths_resolver import resolve_locations
        from lia_agenthub.app import AgentHub
        hub = AgentHub(resolve_locations(tmp_path / "h"))
        r = _skill(tmp_path / "s", "completa", licenca="Apache-2.0")
        imp = hub.import_path(str(r))
        hub.promote(imp.capability_id)
        caminho = hub.publish_index()["path"]

        saida = _rodar(caminho).stdout
        assert "CONFIANÇA" in saida.upper()
        assert "Apache-2.0" in saida
        # O leitor repete o que o índice NÃO avalia, em vez de confiar que o
        # consumidor leu o campo. Isso é requisito de honestidade, não ruído.
        assert "NÃO avalia" in saida

    def test_leitor_nao_escreve_nada(self, hub, tmp_path):
        r = _skill(tmp_path / "n", "sem-escrita", licenca="MIT")
        imp = hub.import_path(str(r))
        hub.promote(imp.capability_id)
        caminho = hub.publish_index()["path"]
        antes = Path(caminho).stat().st_mtime_ns
        conteudo_antes = Path(caminho).read_bytes()

        _rodar(caminho)

        assert Path(caminho).stat().st_mtime_ns == antes
        assert Path(caminho).read_bytes() == conteudo_antes


class TestCheckDoContrato:
    def test_indice_publicado_e_consistente(self, hub, tmp_path):
        r = _skill(tmp_path / "a", "valida", licenca="MIT")
        imp = hub.import_path(str(r))
        hub.promote(imp.capability_id)
        caminho = hub.publish_index()["path"]
        resultado = _rodar(caminho, "--check")
        assert resultado.returncode == 0, resultado.stdout
        assert "consistente" in resultado.stdout

    def test_check_recusa_id_duplicado(self, tmp_path):
        idx = {"schemaVersion": 1, "generatedAt": "2026-01-01T00:00:00Z",
               "capabilities": [
                   {"id": "x", "name": "a", "version": "1", "type": "agent-skill",
                    "trust": "unreviewed", "license": None, "licenseKnown": False,
                    "redistributable": False, "treeHash": "a" * 64},
                   {"id": "x", "name": "b", "version": "1", "type": "agent-skill",
                    "trust": "unreviewed", "license": None, "licenseKnown": False,
                    "redistributable": False, "treeHash": "b" * 64}]}
        arq = tmp_path / "dup.json"
        arq.write_text(json.dumps(idx), encoding="utf-8")
        r = _rodar(str(arq), "--check")
        assert r.returncode == 1
        assert "duplicado" in r.stdout

    def test_check_recusa_redistribuivel_sem_licenca(self, tmp_path):
        """Não se redistribui o que não se conhece. O leitor denuncia."""
        idx = {"schemaVersion": 1, "generatedAt": "2026-01-01T00:00:00Z",
               "capabilities": [
                   {"id": "y", "name": "a", "version": "1", "type": "agent-skill",
                    "trust": "unreviewed", "license": None, "licenseKnown": False,
                    "redistributable": True, "treeHash": "c" * 64}]}
        arq = tmp_path / "bad.json"
        arq.write_text(json.dumps(idx), encoding="utf-8")
        r = _rodar(str(arq), "--check")
        assert r.returncode == 1
        assert "redistribu" in r.stdout.lower()

    def test_check_recusa_schema_version_desconhecida(self, tmp_path):
        idx = {"schemaVersion": 99, "generatedAt": "x", "capabilities": []}
        arq = tmp_path / "v99.json"
        arq.write_text(json.dumps(idx), encoding="utf-8")
        r = _rodar(str(arq), "--check")
        assert r.returncode == 1
        assert "99" in r.stdout

    def test_arquivo_ausente_sai_com_2(self):
        r = _rodar("/caminho/que/nao/existe.json")
        assert r.returncode == 2
        assert "não encontrado" in r.stdout + r.stderr

    def test_json_malformado_sai_com_2(self, tmp_path):
        arq = tmp_path / "quebrado.json"
        arq.write_text("{nao é json", encoding="utf-8")
        r = _rodar(str(arq))
        assert r.returncode == 2
        assert "malformado" in r.stdout + r.stderr


class TestNullNuncaViraZero:
    """O índice declara ignorância como `null`. O leitor não pode inventar."""

    def test_licenca_desconhecida_aparece_como_desconhecida(self, hub, tmp_path):
        r = _skill(tmp_path / "d", "sem-licenca")
        imp = hub.import_path(str(r))
        hub.promote(imp.capability_id)
        saida = _rodar(hub.publish_index()["path"]).stdout
        assert "desconhecida" in saida
        assert " | n/a" not in saida

    def test_campo_nulo_nao_vira_texto_none(self, hub, tmp_path):
        r = _skill(tmp_path / "n", "nula", licenca="MIT")
        imp = hub.import_path(str(r))
        hub.promote(imp.capability_id)
        saida = _rodar(hub.publish_index()["path"]).stdout
        assert "None" not in saida
        assert "null" not in saida
