"""Documentos com números precisam de números verdadeiros.

Um relatório que diz "644 passed" quando são 640 não é detalhe estético: é a
evidência que alguém vai citar.

MÉTODO — por que não há autoinspeção:
contar testes deste próprio arquivo exigiria rodar pytest dentro do pytest,
que recolhe a si mesmo e recorre indefinidamente (aconteceu duas vezes durante
o desenvolvimento, com timeouts de 5 e 10 minutos). A solução é a simples: o
relatório declara o total **de `tests/`**, e este arquivo soma 0 no baseline
porque roda fora de `tests/`. Ver `docs/operations/evidence/test-baseline.txt`.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
RELATORIO = RAIZ / "docs/operations/FUNCTIONAL-COMPLETION-REPORT.md"
BASELINE = RAIZ / "docs/operations/evidence/test-baseline.txt"


def _declarado() -> tuple[int, int, int, int]:
    texto = RELATORIO.read_text(encoding="utf-8")
    total = int(re.search(r"\*\*(\d+) testes\*\*", texto).group(1))
    m = re.search(r"— (\d+) unit, (\d+) integration,\s*\n?(\d+) security", texto)
    assert m, "distribuição por suíte não encontrada no relatório"
    unit, integ, sec = (int(x) for x in m.groups())
    return total, unit, integ, sec


def _baseline() -> dict[str, int]:
    assert BASELINE.is_file(), f"baseline ausente: {BASELINE}"
    dados: dict[str, int] = {}
    for linha in BASELINE.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        chave, _, valor = linha.partition("=")
        dados[chave.strip()] = int(valor.strip())
    return dados


class TestNumerosDoRelatorio:
    def test_relatorio_existe(self):
        assert RELATORIO.is_file()

    def test_declara_total_e_distribuicao(self):
        total, unit, integ, sec = _declarado()
        assert total > 0 and unit > 0 and integ > 0 and sec > 0

    def test_distribuicao_soma_o_total(self):
        total, unit, integ, sec = _declarado()
        assert unit + integ + sec == total, (
            f"{unit}+{integ}+{sec} = {unit+integ+sec}, mas o total é {total}")

    def test_relatorio_bate_com_o_baseline(self):
        """O baseline é a medição registrada. Divergência significa que a
        suíte cresceu ou o relatório ficou para trás — os dois exigem ação."""
        total, unit, integ, sec = _declarado()
        b = _baseline()
        assert (unit, integ, sec, total) == (
            b["unit"], b["integration"], b["security"], b["total"]), (
            f"relatório ({unit}/{integ}/{sec}={total}) diverge do baseline "
            f"({b['unit']}/{b['integration']}/{b['security']}={b['total']})")

    def test_baseline_declara_metodo(self):
        """Número sem método não é evidência. O arquivo diz como foi medido."""
        texto = BASELINE.read_text(encoding="utf-8")
        assert "pytest" in texto
        assert "medido em" in texto or "comando" in texto.lower()


class TestClassificacao:
    def test_todo_requisito_m1a_m8_aparece(self):
        texto = RELATORIO.read_text(encoding="utf-8")
        for n in range(1, 9):
            assert f"**M{n}**" in texto, f"M{n} ausente"

    def test_classes_usadas_sao_as_definidas(self):
        texto = RELATORIO.read_text(encoding="utf-8")
        validas = {"PASS", "PARTIAL", "BLOCKED", "NOT APPLICABLE"}
        usadas = set(re.findall(r"\*\*(PASS|PARTIAL|BLOCKED|NOT APPLICABLE)\*\*", texto))
        assert usadas <= validas

    def test_nao_declara_homologacao_windows(self):
        """A regra do kit: nunca AFIRMAR homologação em Windows.

        Menção à proibição é legítima ("nada aqui declara ..."). O que não
        pode existir é a afirmação em si — a busca exige negação antes.
        """
        texto = RELATORIO.read_text(encoding="utf-8").lower()
        for frase in ("validado no windows", "homologado no windows",
                      "funciona no windows"):
            for m in re.finditer(re.escape(frase), texto):
                antes = texto[max(0, m.start() - 60):m.start()]
                negado = any(n in antes for n in
                             ("nada aqui", "nunca", "não ", "nao ", "jamais"))
                assert negado, f"afirmação de homologação Windows: ...{antes}{frase}"

    def test_d09_permanece_bloqueado(self):
        assert "D-09 continua **BLOCKED**" in RELATORIO.read_text(encoding="utf-8")

    def test_registra_build_nao_executado(self):
        texto = RELATORIO.read_text(encoding="utf-8").lower()
        assert "não empacotei" in texto or "build falhou" in texto

    def test_nao_escolhe_licenca(self):
        assert "não escolhi licença" in RELATORIO.read_text(encoding="utf-8").lower()
