"""Correções exigidas pela revisão independente (bd4bfbb).

O Bloco 1 tinha defeitos reais, inclusive um que quebrava o uso normal do
produto: a validação de referências recusava 16 de 53 Skills reais do acervo.
Cada classe aqui trava um desses defeitos para não voltar.

Os números citados nos docstrings foram MEDIDOS contra os SKILL.md reais dos
quatro repositórios Lia, não estimados. O harness que faz a medição está em
`docs/operations/evidence/corpus_probe.py`.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from lia_agenthub.adapters.paths_resolver import resolve_locations
from lia_agenthub.app import AgentHub
from lia_agenthub.domain.model import License, Severity, Source
from lia_agenthub.domain.skills import (
    check_references, cross_skill_reference, escaping_references,
    folder_name_do_recurso, referenced_files, rotas_citadas,
)


@pytest.fixture
def hub(tmp_path):
    return AgentHub(resolve_locations(tmp_path / "hub"))


def _skill(pasta: Path, *, frontmatter: str = "name: s\ndescription: d\n",
           corpo: str = "Corpo.\n", arquivos: dict[str, str] | None = None) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "SKILL.md").write_text(
        f"---\n{frontmatter}---\n\n{corpo}", encoding="utf-8")
    for nome, texto in (arquivos or {}).items():
        alvo = pasta / nome
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text(texto, encoding="utf-8")
    return pasta


# --------------------------------------------------------------------------
# R-4.1 — o defeito mais grave: C4 recusava 33% do acervo real
# --------------------------------------------------------------------------
class TestR41ReferenciaNaoRecusaRecurso:
    """Antes: 16 de 48 Skills reais eram RECUSADAS na importação.

    Causa: um endpoint CDP citado em prosa (`/json/list`) virava
    `REFERENCE_INVALID` com severidade ERROR, e ERROR bloqueia a importação.
    Uma Skill de operação de navegador não podia ser importada por descrever
    o endpoint que ela mesma usa.
    """

    @pytest.mark.parametrize("endpoint", [
        "/json/list", "/json/version", "/", "/api/v1/health", "/devtools/page/1",
    ])
    def test_endpoint_cdp_citado_em_prosa_nao_gera_issue(self, endpoint):
        texto = f"4. Para Electron, enumere `{endpoint}` no endpoint CDP."
        assert check_references(texto, {"SKILL.md"}) == []

    def test_endpoint_nao_e_confundido_com_caminho_absoluto(self):
        assert escaping_references("`/json/list`") == []
        assert referenced_files("`/json/list`") == []
        assert rotas_citadas("`/json/list`") == ["/json/list"]

    def test_importacao_de_skill_que_cita_endpoint_funciona(self, hub, tmp_path):
        """A regressão que o usuário sentia: a Skill não importava."""
        src = _skill(tmp_path / "lia-browser-automation",
                     corpo="Enumerar `/json/list` e escolher o alvo por URL.\n")
        r = hub.import_path(str(src))
        assert r.ok is True, f"recusada: {r.blocked_reason}"
        assert not [i for i in r.issues if i["severity"] == "error"]

    def test_travessia_em_prosa_e_aviso_de_portabilidade(self):
        """`../../../docs/...` em monorepo é intencional, não ataque.

        Continua sendo REPORTADO (o autor quis dizer algo), mas como aviso:
        quem importar só esta Skill não terá o arquivo. Nunca como bloqueio.
        """
        texto = "Ver `../../../docs/02-LIA-CAPABILITY-MATRIX.md`."
        iss = check_references(texto, {"SKILL.md"})
        assert [i.code for i in iss] == ["REFERENCE_ESCAPE"]
        assert iss[0].severity is Severity.WARNING

    def test_skill_de_monorepo_que_cita_docs_importa(self, hub, tmp_path):
        src = _skill(tmp_path / "capability-mapping",
                     corpo="Ver `../../../docs/02-LIA-CAPABILITY-MATRIX.md`.\n")
        r = hub.import_path(str(src))
        assert r.ok is True, f"recusada: {r.blocked_reason}"

    def test_escaping_references_ainda_detecta_fuga_de_verdade(self):
        """A relaxação não pode ter aberto buraco na detecção."""
        for alvo in ("../../etc/passwd", "C:/Windows/win.ini",
                     "\\\\servidor\\share\\x.md"):
            assert escaping_references(f"`{alvo}`"), alvo

    def test_blocked_reason_cita_o_codigo_real(self, hub, tmp_path):
        """Antes dizia sempre 'estruturalmente inválido', mesmo quando era
        outra coisa — e mandava o usuário caçar erro no frontmatter."""
        src = _skill(tmp_path / "semdesc", frontmatter="name: semdesc\n")
        r = hub.import_path(str(src))
        assert not r.ok
        assert "MISSING_FIELD" in (r.blocked_reason or "")
        assert "estruturalmente inválido" not in (r.blocked_reason or "")

    def test_skill_md_vazio_e_recusado(self, hub, tmp_path):
        """Armadilha do `or`: `b""` é falso, então a validação era PULADA e
        um SKILL.md sem uma linha sequer era estagiado com zero issues."""
        src = tmp_path / "vazio"
        src.mkdir()
        (src / "SKILL.md").write_text("", encoding="utf-8")
        r = hub.import_path(str(src))
        assert not r.ok
        assert "NO_FRONTMATTER" in [i["code"] for i in r.issues]


# --------------------------------------------------------------------------
# R-4.2 — cross-skill era inalcançável no caso real
# --------------------------------------------------------------------------
class TestR42CrossSkill:
    """Antes: `pastas_de_skill` só derivava de `available`, então uma Skill
    citando OUTRA (que por definição não está neste payload) nunca casava, e
    o código `REFERENCE_CROSS_SKILL` era inalcançável. Zero testes cobriam.
    """

    def test_convencao_real_do_acervo_e_reconhecida(self):
        assert cross_skill_reference(
            ".agents/skills/outra-skill/SKILL.md") == "outra-skill"

    @pytest.mark.parametrize("alvo,esperado", [
        (".agents/skills/x/SKILL.md", "x"),
        ("../skills/y/SKILL.md", "y"),
        ("z/SKILL.md", "z"),
        ("docs/guia.md", None),
        ("SKILL.md", None),
    ])
    def test_extracao_do_nome(self, alvo, esperado):
        assert cross_skill_reference(alvo) == esperado

    def test_citar_outra_skill_e_info_nao_erro(self):
        """O caso dominante do monorepo: uma Skill cita outra."""
        iss = check_references("Ver `.agents/skills/lia-game-qa-plan/SKILL.md`.",
                              {"SKILL.md"}, folder_name="lia-game-design")
        assert [i.code for i in iss] == ["REFERENCE_CROSS_SKILL"]
        assert iss[0].severity is Severity.INFO

    def test_citar_a_propria_skill_nao_e_cross(self):
        """Auto-referência com prefixo de pasta resolve para dentro."""
        iss = check_references("Ver `minha-skill/docs/guia.md`.",
                              {"docs/guia.md"}, folder_name="minha-skill")
        assert iss == []

    def test_folder_name_e_passado_na_importacao(self, hub, tmp_path):
        """Antes `folder_name` nunca era passado nos dois pontos de produção,
        apesar de calculado uma linha antes."""
        src = _skill(tmp_path / "sk", corpo="Ver `docs/interno.md`.\n",
                     arquivos={"docs/interno.md": "# interno\n"})
        r = hub.import_path(str(src))
        assert r.ok
        assert "REFERENCE_MISSING" not in [i["code"] for i in r.issues]


# --------------------------------------------------------------------------
# P-E1 — description do frontmatter
# --------------------------------------------------------------------------
class TestPE1DescriptionFallback:
    """Antes: catálogo inteiro sem descrição, mesmo com o texto no SKILL.md.
    Medido: todas as Skills reais saíam com `description` vazio."""

    def test_descricao_vem_do_frontmatter(self, hub, tmp_path):
        src = _skill(tmp_path / "d",
                     frontmatter="name: d\ndescription: Plano de QA por Task.\n")
        r = hub.import_path(str(src))
        assert hub.detail(r.capability_id)["description"] == "Plano de QA por Task."

    def test_manifesto_tem_prioridade_sobre_frontmatter(self, hub, tmp_path):
        src = _skill(tmp_path / "m", frontmatter="name: m\ndescription: do frontmatter\n")
        r = hub.import_path(str(src))
        # o frontmatter preenche porque não há manifesto; aditivo, não invasivo
        assert hub.detail(r.capability_id)["description"] == "do frontmatter"

    def test_sem_descricao_em_lugar_nenhum_continua_vazio(self, hub, tmp_path):
        """Fallback não pode INVENTAR descrição.

        Não se chega ao registro porque `description` é campo obrigatório —
        a recusa é estrutural e nomeia o campo. Este teste trava as duas
        metades: nada é inventado e o motivo é dito.
        """
        src = _skill(tmp_path / "v", frontmatter="name: v\n")
        r = hub.import_path(str(src))
        assert not r.ok
        assert "MISSING_FIELD" in [i["code"] for i in r.issues]


# --------------------------------------------------------------------------
# P-E2 — licença do frontmatter como declaração
# --------------------------------------------------------------------------
class TestPE2LicencaDeclarada:
    """Antes o campo `license` do frontmatter era ignorado: recurso com
    licença declarada no texto saía como "sem licença".

    Regra que os testes travam: declaração NÃO é permissão.
    """

    def test_declaracao_no_frontmatter_e_registrada(self, hub, tmp_path):
        src = _skill(tmp_path / "f", frontmatter="name: f\ndescription: d\nlicense: Apache-2.0\n")
        r = hub.import_path(str(src))
        lic = hub.detail(r.capability_id)["license"]
        assert lic["code"] == "Apache-2.0"
        assert lic["status"] == "declared"

    def test_declaracao_nunca_autoriza_redistribuicao(self, hub, tmp_path):
        src = _skill(tmp_path / "a", frontmatter="name: a\ndescription: d\nlicense: MIT\n")
        r = hub.import_path(str(src))
        lic = hub.detail(r.capability_id)["license"]
        assert lic["redistributable"] is False

    def test_base_aponta_que_a_evidencia_e_textual(self, hub, tmp_path):
        src = _skill(tmp_path / "b", frontmatter="name: b\ndescription: d\nlicense: MIT\n")
        r = hub.import_path(str(src))
        base = hub.detail(r.capability_id)["license"]["redistribution_basis"]
        assert base and "frontmatter" in base
        assert "não verificação" in base

    def test_arquivo_de_licenca_vence_frontmatter(self, hub, tmp_path):
        """Evidência física > afirmação textual. Divergir é informação."""
        src = _skill(tmp_path / "c",
                     frontmatter="name: c\ndescription: d\nlicense: Apache-2.0\n",
                     arquivos={"LICENSE": "MIT License\n\nCopyright (c) 2026 X\n"})
        r = hub.import_path(str(src))
        lic = hub.detail(r.capability_id)["license"]
        assert lic["code"] == "MIT"
        assert "arquivo" in lic["redistribution_basis"]

    def test_ausencia_total_nao_inventa_licenca(self, hub, tmp_path):
        src = _skill(tmp_path / "n")
        r = hub.import_path(str(src))
        lic = hub.detail(r.capability_id)["license"]
        assert lic["code"] is None and lic["status"] == "unknown"


# --------------------------------------------------------------------------
# R-2.1 — NOTICE não cobria licença por Skill
# --------------------------------------------------------------------------
class TestR21NoticePorSkill:
    """Antes: `_texto_da_licenca` só olhava a RAIZ do payload. No acervo real
    a licença fica em `skills/<nome>/LICENSE.md`, então o pacote saía sem o
    texto que a licença obriga a acompanhar, e o THIRD_PARTY_NOTICES dizia
    "NÃO DECLARADA" para um recurso que TEM licença."""

    def test_licenca_em_subpasta_vai_para_o_notice(self, hub, tmp_path):
        src = _skill(tmp_path / "sub",
                     frontmatter="name: sub\ndescription: d\nlicense: MIT\n",
                     arquivos={"LICENSE.md": "MIT License\n\nCopyright (c) 2025 Fulano\n"})
        r = hub.import_path(str(src))
        hub.promote(r.capability_id)
        e = hub.export(r.capability_id, target="private",
                       destination=str(tmp_path / "out"))
        zf = zipfile.ZipFile(e["path"])
        assert "NOTICE" in zf.namelist()
        notice = zf.read("NOTICE").decode()
        # conteúdo REAL, não só o nome da licença
        assert "Copyright (c) 2025 Fulano" in notice
        assert "LICENSE.md" in notice

    def test_third_party_notices_nao_diz_nao_declarada(self, hub, tmp_path):
        src = _skill(tmp_path / "t",
                     frontmatter="name: t\ndescription: d\nlicense: MIT\n",
                     arquivos={"LICENSE.txt": "MIT License\n\nCopyright (c) 2025 Y\n"})
        r = hub.import_path(str(src))
        hub.promote(r.capability_id)
        e = hub.export(r.capability_id, target="private",
                       destination=str(tmp_path / "out"))
        tn = zipfile.ZipFile(e["path"]).read("THIRD_PARTY_NOTICES.md").decode()
        assert "NÃO DECLARADA" not in tn

    def test_sem_licenca_no_pacote_o_notice_admite(self, hub, tmp_path):
        """Não finge que o texto está lá quando não está."""
        src = _skill(tmp_path / "s", frontmatter="name: s\ndescription: d\nlicense: MIT\n")
        r = hub.import_path(str(src))
        hub.promote(r.capability_id)
        e = hub.export(r.capability_id, target="private",
                       destination=str(tmp_path / "out"))
        notice = zipfile.ZipFile(e["path"]).read("NOTICE").decode()
        assert "nenhum arquivo de licença" in notice.lower()


# --------------------------------------------------------------------------
# Achados menores da revisão
# --------------------------------------------------------------------------
class TestAchadosMenores:
    def test_r1_1_extra_nao_sobrescreve_campo_conhecido(self):
        s = Source.from_dict({"method": "local", "extra": {"method": "HACK"}})
        assert s.as_dict()["method"] == "local"

    def test_r1_2_license_preserva_campo_desconhecido(self):
        lic = License.from_dict({"code": "MIT", "campoFuturo": "x"})
        assert lic.extra == {"campoFuturo": "x"}
        assert lic.as_dict()["campoFuturo"] == "x"

    def test_r1_2_license_campo_desconhecido_nao_sobrescreve(self):
        lic = License.from_dict({"code": "MIT", "extra": {"code": "HACK"}})
        assert lic.code == "MIT"

    def test_r1_3_erros_de_leitura_nao_acumulam(self, hub, tmp_path):
        """Antes: erro de uma varredura contaminava a seguinte."""
        ruim = hub.repo.locations.library / "quebrado" / ".lia"
        ruim.mkdir(parents=True)
        (ruim / "capability.json").write_text("{ invalido", encoding="utf-8")
        hub.repo.list_all()
        assert len(hub.repo.erros_de_leitura) == 1
        hub.repo.list_all()
        assert len(hub.repo.erros_de_leitura) == 1, "não pode acumular"
        # Pasta sem registro nenhum é ELA MESMA um sinal (payload sem
        # metadata = dado perdido) e continua sendo reportada. Para provar
        # que a lista zera, removemos o registro quebrado por completo.
        import shutil
        shutil.rmtree(hub.repo.locations.library / "quebrado")
        hub.repo.list_all()
        assert hub.repo.erros_de_leitura == [], "varredura limpa zera"

    def test_r2_2_helper_morto_removido(self):
        import lia_agenthub.domain.model as m
        assert not hasattr(m, "exige_notice_conhecido")

    @pytest.mark.parametrize("entrada,esperado", [
        ("/home/u/minha-skill", "minha-skill"),
        ("C:\\Users\\u\\minha-skill", "minha-skill"),
        ("/home/u/pacote.zip", None),
        ("/home/u/arquivo.md", None),
        ("rotulo-simples", None),
        ("", None),
        (None, None),
    ])
    def test_r5_1_folder_name_sem_ramo_morto(self, entrada, esperado):
        assert folder_name_do_recurso(entrada) == esperado

    def test_r8_2_indice_emitido_esta_no_schema(self):
        """Antes: 6 chaves emitidas e ausentes do schema publicado — um
        consumidor que validasse o índice contra o schema o rejeitaria."""
        from lia_agenthub.adapters.index_builder import SCHEMA
        props = set(SCHEMA["properties"]["capabilities"]["items"]["properties"])
        emitidas = {"id", "name", "version", "type", "trust", "license",
                    "package", "lifecycle", "description", "domain", "tags",
                    "author", "redistributable"}
        assert emitidas <= props, f"fora do schema: {sorted(emitidas - props)}"


# --------------------------------------------------------------------------
# Débito herdado que a revisão apontou como pré-existente
# --------------------------------------------------------------------------
class TestReimportacao:
    """`alreadyPresent` era declarado, serializado e NUNCA atribuído: sempre
    False. Reimportar sobrescrevia a quarentena em silêncio, inclusive
    trocando a procedência quando o `upstream` era outro."""

    def test_reimportacao_reporta_que_ja_existia(self, hub, tmp_path):
        src = _skill(tmp_path / "idem")
        r1 = hub.import_path(str(src))
        r2 = hub.import_path(str(src))
        assert r1.already_present is False
        assert r2.already_present is True
        assert r1.capability_id == r2.capability_id

    def test_importacao_nao_promove_sozinha(self, hub, tmp_path):
        """Estar em quarentena E não estar na biblioteca são coisas distintas;
        `exists()` responde só sobre a biblioteca."""
        src = _skill(tmp_path / "q")
        r = hub.import_path(str(src))
        assert hub.repo.exists(r.capability_id) is False
        assert hub.repo.exists_anywhere(r.capability_id) is True


class TestCapabilityTolerante:
    """Mesma classe de defeito da R-1.2, um nível acima.

    `License.from_dict` descartava campo desconhecido (corrigido). Mas
    `Capability.from_dict` fazia o mesmo no nível de cima, e ninguém tinha
    olhado: um registro gravado por um Hub mais novo perdia o campo ao ser
    LIDO por um Hub mais antigo. Perda silenciosa no roundtrip.
    """

    def test_campo_futuro_sobrevive_ao_roundtrip(self):
        from lia_agenthub.domain.model import Capability
        c = Capability.from_dict({"id": "x", "name": "x", "version": "1",
                                  "campoDeVersaoFutura": {"a": 1}})
        assert c.extra == {"campoDeVersaoFutura": {"a": 1}}
        assert c.as_dict()["campoDeVersaoFutura"] == {"a": 1}

    def test_campo_futuro_nao_sobrescreve_campo_conhecido(self):
        from lia_agenthub.domain.model import Capability
        c = Capability.from_dict({"id": "x", "name": "x", "version": "1",
                                  "extra": {"id": "HACK"}})
        assert c.as_dict()["id"] == "x"

    def test_regstro_que_nao_e_objeto_da_erro_claro(self):
        from lia_agenthub.domain.model import Capability
        from lia_agenthub.domain.errors import LiaError
        with pytest.raises(LiaError):
            Capability.from_dict(["nao", "e", "objeto"])


class TestUnicodeNome:
    """O nome do arquivo é conteúdo não confiável tanto quanto o corpo."""

    def test_nome_com_bidi_e_sinalizado(self, hub, tmp_path):
        src = tmp_path / "bidi"
        src.mkdir()
        (src / "SKILL.md").write_text(
            "---\nname: bidi\ndescription: d\n---\n\nCorpo.\n", encoding="utf-8")
        (src / "a\u202egnp.exe").write_bytes(b"x")
        r = hub.import_path(str(src))
        assert "UNICODE_FILENAME" in [i["code"] for i in r.issues]
        assert r.requires_review is True

    def test_nome_normal_nao_gera_ruido(self, hub, tmp_path):
        src = tmp_path / "ok"
        src.mkdir()
        (src / "SKILL.md").write_text(
            "---\nname: ok\ndescription: d\n---\n\nCorpo.\n", encoding="utf-8")
        (src / "guia.md").write_text("texto\n", encoding="utf-8")
        r = hub.import_path(str(src))
        assert "UNICODE_FILENAME" not in [i["code"] for i in r.issues]
