"""Fixtures — dados sintéticos apenas. Nada de rede, nada de execução."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lia_agenthub.adapters.paths_resolver import resolve_locations  # noqa: E402
from lia_agenthub.app import AgentHub                               # noqa: E402


@pytest.fixture
def locations(tmp_path):
    locs = resolve_locations(tmp_path / "home")
    locs.ensure()
    return locs


@pytest.fixture
def hub(locations) -> AgentHub:
    return AgentHub(locations)


@pytest.fixture
def skill_dir(tmp_path):
    """Uma Agent Skill bem formada, com licença MIT declarada."""
    d = tmp_path / "src" / "skill-exemplo"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        "---\n"
        "name: skill-exemplo\n"
        "description: Faz algo previsível em testes sintéticos.\n"
        "version: 1.0.0\n"
        "metadata: tags:teste,exemplo\n"
        "---\n\n"
        "# Exemplo\n\nEste corpo é sintético.\n",
        encoding="utf-8")
    (d / "LICENSE").write_text(
        "MIT License\n\nCopyright (c) 2026 Pessoa Sintética\n", encoding="utf-8")
    return d


@pytest.fixture
def bare_skill_dir(tmp_path):
    """Skill válida mas sem licença — caso comum, e o mais mal interpretado."""
    d = tmp_path / "src" / "sem-licenca"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        "---\nname: sem-licenca\ndescription: Sem arquivo de licença.\n---\n\nCorpo.\n",
        encoding="utf-8")
    return d


@pytest.fixture
def imported(hub, skill_dir):
    """Skill já importada E promovida — ponto de partida da maioria dos testes."""
    report = hub.import_path(str(skill_dir))
    assert report.ok, report.blocked_reason
    return hub.promote(report.capability_id)
