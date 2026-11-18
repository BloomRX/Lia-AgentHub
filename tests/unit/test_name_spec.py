"""M3 — validador estrutural com os casos que o critério de aceite nomeia.

O doc do MVP exige: "Skill com `name` de 65 chars ou hífen duplo → erro com a
regra citada". Estes testes cobrem exatamente isso, mais os casos de borda que
a execução revelou — em especial campo presente e VAZIO, que passava como
válido enquanto a ausência da chave era erro.
"""
from __future__ import annotations

import pytest

from lia_agenthub.domain.skills import validate_skill


def _fm(**campos) -> str:
    linhas = "\n".join(f"{k}: {v}" for k, v in campos.items())
    return f"---\n{linhas}\n---\n\nCorpo.\n"


def erros(texto: str) -> list[str]:
    return [i.code for i in validate_skill(texto) if i.severity.value == "error"]


class TestNome:
    def test_65_caracteres_e_erro(self):
        assert "NAME_TOO_LONG" in erros(_fm(name="a" * 65, description="d"))

    def test_64_caracteres_e_aceito(self):
        """O limite é 64 e precisa valer para o 64º caractere também."""
        assert erros(_fm(name="a" * 64, description="d")) == []

    def test_hifen_duplo_e_erro(self):
        assert "NAME_FORMAT" in erros(_fm(name="a--b", description="d"))

    def test_hifen_final_e_erro(self):
        assert "NAME_FORMAT" in erros(_fm(name="ab-", description="d"))

    def test_maiuscula_e_erro(self):
        assert "NAME_FORMAT" in erros(_fm(name="Ab", description="d"))

    def test_underscore_e_erro(self):
        assert "NAME_FORMAT" in erros(_fm(name="a_b", description="d"))

    def test_kebab_case_valido(self):
        assert erros(_fm(name="minha-skill-valida", description="d")) == []

    def test_nome_de_um_caractere(self):
        assert erros(_fm(name="a", description="d")) == []


class TestCampoVazio:
    """Presença da chave ≠ valor utilizável."""

    def test_nome_vazio_e_erro(self):
        assert "FIELD_EMPTY" in erros(_fm(name='""', description="d"))

    def test_descricao_vazia_e_erro(self):
        assert "FIELD_EMPTY" in erros(_fm(name="ok", description='""'))

    def test_ambos_vazios_geram_dois_erros(self):
        assert erros(_fm(name='""', description='""')).count("FIELD_EMPTY") == 2

    def test_so_espacos_conta_como_vazio(self):
        assert "FIELD_EMPTY" in erros(_fm(name='"   "', description="d"))

    def test_campo_ausente_continua_sendo_erro_diferente(self):
        """Ausente e vazio são problemas distintos e o relatório distingue."""
        ausente = erros(_fm(description="d"))
        vazio = erros(_fm(name='""', description="d"))
        assert "MISSING_FIELD" in ausente
        assert "FIELD_EMPTY" in vazio
        assert "MISSING_FIELD" not in vazio


class TestDescricao:
    def test_descricao_longa_e_aviso_nao_erro(self):
        """500+ caracteres é recomendação, não bloqueio."""
        issues = validate_skill(_fm(name="ok", description="d" * 600))
        assert not [i for i in issues if i.severity.value == "error"]

    def test_descricao_em_bloco_yaml_e_lida_inteira(self):
        texto = ("---\nname: bloco\ndescription: >-\n  Linha um.\n  Linha dois.\n"
                 "---\n\nCorpo.\n")
        from lia_agenthub.domain.skills import parse_frontmatter
        fm = parse_frontmatter(texto)
        assert "Linha um." in fm.frontmatter["description"]
        assert ">" not in fm.frontmatter["description"]
        assert erros(texto) == []
