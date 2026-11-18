"""O registro de decisões não pode ser promovido por engano.

`ADOPTED para implementação` significa "a Fase 1 estava autorizada a construir
a partir desta recomendação". Isso é diferente de `APPROVED`, que exige aceite
humano. Uma sessão que escreve código não ganha o direito de aprovar decisão.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
REGISTRO = RAIZ / "docs/DECISION-REGISTER.md"


def bloco(cap_id: str) -> str:
    """Texto da seção de uma decisão, do título até o próximo `### D-`."""
    texto = REGISTRO.read_text(encoding="utf-8")
    m = re.search(rf"### {re.escape(cap_id)} — .*?(?=\n### D-|\n---\n\n## |\Z)",
                  texto, re.S)
    assert m, f"decisão {cap_id} não encontrada"
    return m.group(0)


def estado(cap_id: str) -> str:
    m = re.search(r"\*\*Estado\*\*\s*\|\s*(.+)", bloco(cap_id))
    assert m, f"{cap_id} sem campo Estado"
    return m.group(1).strip()


class TestDecisoesAbertasContinuamAbertas:
    @pytest.mark.parametrize("cap_id", ["D-01", "D-05", "D-16", "D-18"])
    def test_continua_open(self, cap_id):
        assert "OPEN" in estado(cap_id), f"{cap_id} deixou de estar OPEN"

    @pytest.mark.parametrize("cap_id", ["D-01", "D-05", "D-16", "D-18"])
    def test_nao_foi_marcada_approved(self, cap_id):
        e = estado(cap_id)
        assert "APPROVED" not in e, f"{cap_id} foi promovida: {e}"


class TestNenhumaAprovacaoInventada:
    def test_registro_nao_tem_nenhum_approved(self):
        """O estado atual é: 0 decisões aprovadas. Se mudar, é decisão humana
        e precisa aparecer no diff como tal — não como efeito colateral."""
        texto = REGISTRO.read_text(encoding="utf-8")
        # O cabeçalho explica os estados possíveis; excluímos essa linha.
        linhas = [l for l in texto.splitlines()
                  if "`OPEN` · `RESEARCHING`" not in l]
        aprovacoes = [l for l in linhas if "| `APPROVED`" in l or "Estado** | `APPROVED`" in l]
        assert not aprovacoes, f"decisão marcada APPROVED: {aprovacoes}"

    def test_secao_de_implementacao_nao_promove(self):
        texto = REGISTRO.read_text(encoding="utf-8")
        # `index()` pegaria a menção no cabeçalho, não a seção. `rindex` pega a
        # seção real, que é a última ocorrência do título.
        inicio = texto.rindex("## Estado de implementação por decisão")
        fim = texto.find("\n## ", inicio + 10)
        assert fim > inicio, "seção de implementação não termina"
        trecho = texto[inicio:fim]
        assert "Nenhuma decisão foi promovida" in trecho
        for cap_id in ("D-05", "D-16", "D-18"):
            # A linha tem três colunas: ID | descrição | estado. Procurar só
            # `ID` seguido do estado casaria com a coluna errada.
            padrao = rf"\| `{cap_id}` \|[^|]*\| \*\*`OPEN`\*\* \|"
            assert re.search(padrao, trecho), f"{cap_id} não consta OPEN na tabela"


class TestLicencaNaoFoiEscolhida:
    def test_nao_existe_arquivo_LICENSE_na_raiz(self):
        """D-16 aberta: criar LICENSE seria decidir por conta própria."""
        assert not (RAIZ / "LICENSE").exists()
        assert not (RAIZ / "LICENSE.md").exists()

    def test_nao_existe_TRADEMARK(self):
        assert not (RAIZ / "TRADEMARK.md").exists()

    def test_pyproject_nao_declara_licenca_escolhida(self):
        texto = (RAIZ / "pyproject.toml").read_text(encoding="utf-8")
        assert "UNLICENSED" in texto or "D-16" in texto
