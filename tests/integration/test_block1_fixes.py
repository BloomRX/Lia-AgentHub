"""Bloco 1 — regressões dos defeitos corrigidos em C1–C5 e C8.

Cada teste aqui reproduz o comportamento ERRADO observado antes da correção.
Não são testes de "a função devolve algo": são testes de que o defeito
específico não volta. Onde possível, o docstring diz qual era o sintoma.

Cada teste é independente e não depende de fixtures externas.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from lia_agenthub.adapters.atomic import atomic_write_json
from lia_agenthub.adapters.index_builder import (
    SCHEMA, build_index, check_consistency, validate_index,
)
from lia_agenthub.adapters.paths_resolver import resolve_locations
from lia_agenthub.adapters.repository import Repository
from lia_agenthub.app import AgentHub
from lia_agenthub.domain.model import (
    Capability, License, Lifecycle, Severity, Source, notice_obrigatorio,
)
from lia_agenthub.domain.paths import WINDOWS_RESERVED
from lia_agenthub.domain.skills import (
    check_references, escaping_references, folder_name_do_recurso,
    referenced_files,
)


# ---------------------------------------------------------------- utilidades
def _hub(tmp_path: Path) -> AgentHub:
    return AgentHub(resolve_locations(tmp_path / "home"))


def _skill(base: Path, nome: str = "x", corpo: str = "", extras=None) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    (base / "SKILL.md").write_text(
        f"---\nname: {nome}\ndescription: fixture de teste\n---\n\n{corpo}",
        encoding="utf-8")
    for rel, texto in (extras or {}).items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texto, encoding="utf-8")
    return base


def _registro_manual(loc, cap_id: str, *, lifecycle="active", source=None,
                     license_=None) -> Path:
    """Grava um capability.json à mão, como uma versão futura teria gravado."""
    root = loc.library / cap_id
    (root / ".lia").mkdir(parents=True, exist_ok=True)
    (root / "payload").mkdir(exist_ok=True)
    (root / "payload" / "SKILL.md").write_text(
        "---\nname: x\ndescription: d\n---\n", encoding="utf-8")
    meta = {
        "id": cap_id, "name": cap_id, "version": "1.0.0",
        "type": "agent-skill", "trust": "unreviewed", "lifecycle": lifecycle,
        "license": license_ or {"code": None, "status": "unknown"},
        "source": source if source is not None else {"method": "local"},
    }
    atomic_write_json(root / ".lia" / "capability.json", meta)
    return root


# ============================================================ C1 — Source
class TestC1ToleranciaDeSource:
    """Antes: `Source(**d)` com campo extra → TypeError → `list_all()`
    levantava e a biblioteca INTEIRA ficava inacessível."""

    def test_source_aceita_campo_desconhecido_sem_levantar(self):
        s = Source.from_dict({"method": "local", "campoFuturo": "x"})
        assert s.method == "local"
        assert s.extra == {"campoFuturo": "x"}

    def test_campo_desconhecido_e_preservado_na_regravacao(self):
        """Preservar, não descartar: perder procedência é perda de dado."""
        s = Source.from_dict({"method": "local", "assinaturaFutura": {"alg": "x"}})
        volta = s.as_dict()
        assert volta["assinaturaFutura"] == {"alg": "x"}
        assert volta["method"] == "local"

    def test_ida_e_volta_estavel(self):
        original = {"method": "local", "upstream": "/a/b", "novoCampo": [1, 2]}
        d1 = Source.from_dict(original).as_dict()
        d2 = Source.from_dict(d1).as_dict()
        assert d1 == d2

    def test_registro_antigo_sem_campos_novos_continua_legivel(self):
        s = Source.from_dict({"method": "local"})
        assert s.method == "local"
        assert s.extra == {}

    def test_source_ausente_e_none_nao_quebram(self):
        assert Source.from_dict(None).method == "local"
        assert Source.from_dict({}).method == "local"

    def test_source_com_tipo_invalido_nao_levanta(self):
        """Registro corrompido não pode derrubar a leitura."""
        s = Source.from_dict("isto-nao-e-dict")
        assert s.extra["_valorOriginal"] == "isto-nao-e-dict"

    def test_um_registro_ruim_nao_derruba_a_biblioteca(self, tmp_path):
        """O defeito original, exatamente."""
        loc = resolve_locations(tmp_path / "h")
        loc.ensure()
        _registro_manual(loc, "a-ok")
        _registro_manual(loc, "b-ruim", source={"method": "local", "campoFuturo": 1})
        _registro_manual(loc, "c-ok")

        lidos = Repository(loc).list_all()

        assert len(lidos) == 3, "um registro incompatível não pode esconder os outros"
        assert {s.capability.id for s in lidos} == {"a-ok", "b-ruim", "c-ok"}

    def test_erro_de_leitura_de_registro_e_registrado_nao_engolido(self, tmp_path):
        """Registro realmente ilegível: sai da lista, mas fica o motivo."""
        loc = resolve_locations(tmp_path / "h")
        loc.ensure()
        _registro_manual(loc, "bom")
        ruim = loc.library / "sem-meta"
        (ruim / "payload").mkdir(parents=True)
        (ruim / "payload" / "x.md").write_text("x", encoding="utf-8")

        repo = Repository(loc)
        lidos = repo.list_all()

        assert [s.capability.id for s in lidos] == ["bom"]
        assert any(e["id"] == "sem-meta" for e in repo.erros_de_leitura), \
            "registro ilegível precisa deixar rastro, não desaparecer"
        assert all(e["motivo"] for e in repo.erros_de_leitura)

    def test_extra_nao_influencia_confianca_nem_ciclo(self):
        """Tolerância não vira permissividade."""
        cap = Capability.from_dict({
            "id": "x", "name": "x", "version": "1.0.0", "type": "agent-skill",
            "source": {"method": "local", "trust": "first-party",
                       "lifecycle": "active"}})
        assert cap.trust.value == "unreviewed"
        assert cap.lifecycle is Lifecycle.QUARANTINED


# ==================================================== C2 — notice_required
class TestC2NoticeRequired:
    """Antes: `License(...)` era construído sem o campo, então um recurso MIT
    era exportado sem NOTICE — obrigação do texto MIT descumprida."""

    def test_licenca_mit_exige_notice(self):
        assert notice_obrigatorio("MIT") is True

    def test_unlicense_nao_exige_notice(self):
        assert notice_obrigatorio("Unlicense") is False

    def test_licenca_desconhecida_nao_presume_exigencia_nem_permissao(self):
        assert notice_obrigatorio("Licenca-Inventada-9.9") is False
        # e continua não sendo permissão de uso:
        assert License(code="Licenca-Inventada-9.9").redistributable is False

    def test_importacao_preserva_notice_required_verdadeiro(self, tmp_path):
        hub = _hub(tmp_path)
        src = _skill(tmp_path / "src", extras={
            "LICENSE": "MIT License\n\nCopyright (c) 2026 Fulano\n"})
        r = hub.import_path(str(src))
        assert r.ok
        cap = hub.repo._load_any(r.capability_id).capability
        assert cap.license.code == "MIT"
        assert cap.license.notice_required is True, \
            "MIT exige aviso; o campo não pode voltar False"

    def test_persistencia_do_campo_em_disco(self, tmp_path):
        hub = _hub(tmp_path)
        src = _skill(tmp_path / "src", extras={"LICENSE": "MIT License\nx\n"})
        r = hub.import_path(str(src))
        meta = json.loads(
            (hub.repo._load_any(r.capability_id).meta / "capability.json")
            .read_text(encoding="utf-8"))
        assert meta["license"]["notice_required"] is True

    def test_exportacao_inclui_notice_e_o_texto_da_licenca(self, tmp_path):
        hub = _hub(tmp_path)
        src = _skill(tmp_path / "src", extras={
            "LICENSE": "MIT License\n\nCopyright (c) 2026 Beltrano\n"})
        r = hub.import_path(str(src))
        hub.promote(r.capability_id)
        e = hub.export(r.capability_id, target="private",
                       destination=str(tmp_path / "out"))
        assert e["ok"]
        zf = zipfile.ZipFile(e["path"])
        assert "NOTICE" in zf.namelist()
        texto = zf.read("NOTICE").decode("utf-8")
        assert "Copyright (c) 2026 Beltrano" in texto, \
            "MIT exige o texto do aviso, não só o nome da licença"

    def test_registro_antigo_sem_o_campo_deriva_da_licenca(self):
        """Compatibilidade: campo ausente não vira False silencioso."""
        antigo = License.from_dict({"code": "MIT", "status": "declared"})
        assert antigo.notice_required is True

    def test_registro_antigo_de_licenca_sem_exigencia_continua_false(self):
        antigo = License.from_dict({"code": "Unlicense", "status": "declared"})
        assert antigo.notice_required is False

    def test_valor_explicito_prevalece_sobre_a_tabela(self):
        """Decisão humana registrada não é sobrescrita pela derivação."""
        explicito = License.from_dict(
            {"code": "MIT", "status": "declared", "notice_required": False})
        assert explicito.notice_required is False

    def test_sem_licenca_identificada_nao_inventa_notice(self, tmp_path):
        hub = _hub(tmp_path)
        src = _skill(tmp_path / "src")           # nenhum arquivo de licença
        r = hub.import_path(str(src))
        cap = hub.repo._load_any(r.capability_id).capability
        assert cap.license.code is None
        assert cap.license.notice_required is False

    def test_licenca_com_notice_mas_sem_texto_avisa_em_vez_de_fingir(self, tmp_path):
        hub = _hub(tmp_path)
        src = _skill(tmp_path / "src", extras={"LICENSE": "MIT License\n"})
        r = hub.import_path(str(src))
        hub.promote(r.capability_id)
        # Remove o texto do payload para simular registro incompleto
        payload = hub.repo._load_any(r.capability_id).payload
        (payload / "LICENSE").unlink()
        e = hub.export(r.capability_id, target="private",
                       destination=str(tmp_path / "out"))
        assert e["ok"]
        texto = zipfile.ZipFile(e["path"]).read("NOTICE").decode("utf-8")
        assert "nenhum arquivo de licença" in texto.lower()

    def test_exportacao_publica_continua_exigindo_base(self, tmp_path):
        """C2 não relaxa a política por destino: MIT ≠ direito de publicar."""
        hub = _hub(tmp_path)
        src = _skill(tmp_path / "src", extras={"LICENSE": "MIT License\nx\n"})
        r = hub.import_path(str(src))
        hub.promote(r.capability_id)
        e = hub.export(r.capability_id, target="public",
                       destination=str(tmp_path / "pub"))
        assert e["ok"] is False
        assert "redistribuí" in e["refusedReason"] or "redistribu" in e["refusedReason"]


# ========================================================= C3 — bloqueio .lia
class TestC3BloqueioDeMetadadosInternos:
    """Antes: `.lia/capability.json` forjado entrava no payload e saía no
    pacote exportado como `payload/.lia/capability.json`."""

    @pytest.mark.parametrize("rel", [
        ".lia/capability.json",
        ".lia/provenance.json",
        ".lia/history.json",
        "docs/.lia/provenance.json",          # aninhado
        ".LIA/capability.json",               # variação de caixa
        ".Lia/history.json",
        ".lia./capability.json",              # ponto final (Windows colapsa)
    ])
    def test_payload_com_lia_e_recusado(self, tmp_path, rel):
        hub = _hub(tmp_path)
        src = _skill(tmp_path / "src", extras={rel: '{"trust":"first-party"}'})
        r = hub.import_path(str(src))
        assert r.ok is False, f"`{rel}` deveria ser recusado"
        assert ".lia" in r.blocked_reason.lower() or "proibida" in r.blocked_reason.lower()

    def test_zip_com_lia_e_recusado(self, tmp_path):
        hub = _hub(tmp_path)
        z = tmp_path / "p.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("SKILL.md", "---\nname: x\ndescription: d\n---\n")
            zf.writestr(".lia/capability.json", '{"trust":"first-party"}')
        r = hub.import_path(str(z))
        assert r.ok is False

    def test_pacote_lia_capability_com_lia_e_recusado(self, tmp_path):
        """Reimportar um pacote adulterado também não passa."""
        hub = _hub(tmp_path)
        z = tmp_path / "p.lia-capability"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("payload/SKILL.md", "---\nname: x\ndescription: d\n---\n")
            zf.writestr("payload/.lia/capability.json", "{}")
        r = hub.import_path(str(z))
        assert r.ok is False

    def test_payload_limpo_continua_importando(self, tmp_path):
        hub = _hub(tmp_path)
        src = _skill(tmp_path / "src", extras={"docs/guia.md": "# ok"})
        assert hub.import_path(str(src)).ok is True

    def test_metadado_forjado_nao_eleva_confianca(self, tmp_path):
        """Mesmo se algo passar, o trust não vem do payload."""
        hub = _hub(tmp_path)
        src = _skill(tmp_path / "src")
        r = hub.import_path(str(src))
        cap = hub.repo._load_any(r.capability_id).capability
        assert cap.trust.value == "unreviewed"
        assert cap.lifecycle is Lifecycle.QUARANTINED

    def test_exportacao_remove_lia_de_registro_legado_e_avisa(self, tmp_path):
        """Registro importado ANTES da correção ainda pode estar contaminado."""
        loc = resolve_locations(tmp_path / "h")
        loc.ensure()
        root = _registro_manual(loc, "legado", license_={"code": "MIT",
                                                         "status": "declared"})
        (root / "payload" / ".lia").mkdir(parents=True)
        (root / "payload" / ".lia" / "capability.json").write_text(
            '{"trust":"first-party"}', encoding="utf-8")

        hub = AgentHub(loc)
        e = hub.export("legado", target="private", destination=str(tmp_path / "out"))

        assert e["ok"] is True
        nomes = zipfile.ZipFile(e["path"]).namelist()
        assert not [n for n in nomes if ".lia" in n], \
            "metadado interno não pode viajar para quem recebe o pacote"
        assert any(".lia" in w for w in e["warnings"]), \
            "excluir em silêncio esconderia que o registro está contaminado"

    def test_exportacao_recusa_payload_que_so_tem_lia(self, tmp_path):
        loc = resolve_locations(tmp_path / "h")
        loc.ensure()
        root = _registro_manual(loc, "so-meta")
        (root / "payload" / "SKILL.md").unlink()
        (root / "payload" / ".lia").mkdir(parents=True)
        (root / "payload" / ".lia" / "x.json").write_text("{}", encoding="utf-8")

        e = AgentHub(loc).export("so-meta", target="private",
                                 destination=str(tmp_path / "out2"))
        assert e["ok"] is False

    def test_nomes_reservados_do_windows_continuam_bloqueados(self):
        assert "CON" in WINDOWS_RESERVED and "AUX" in WINDOWS_RESERVED


# ============================================================ C4 — referências
class TestC4Referencias:
    """Antes: fugas (`..`, absoluto) eram descartadas em silêncio, e citar
    outra Skill ou arquivo ausente eram o mesmo código."""

    def test_referencia_local_existente_nao_gera_aviso(self):
        assert check_references("Veja `docs/guia.md`.",
                                {"SKILL.md", "docs/guia.md"}) == []

    def test_referencia_local_ausente_gera_missing(self):
        iss = check_references("Veja `docs/sumiu.md`.",
                               {"SKILL.md", "docs/guia.md"})
        assert [i.code for i in iss] == ["REFERENCE_MISSING"]

    def test_referencia_a_outra_skill_e_cross_skill(self):
        iss = check_references("Veja `outra-skill/SKILL.md`.",
                               {"SKILL.md", "outra-skill/SKILL.md"})
        assert [i.code for i in iss] == []

    def test_referencia_cross_skill_ausente_nao_e_erro(self):
        """Citar outra Skill é informativo, nunca bloqueio.

        Antes isto virava REFERENCE_MISSING (warning) porque o detector só
        reconhecia Skill quando ela estava DENTRO do payload — que é o caso
        raro. O caso real do acervo é `.agents/skills/<outra>/SKILL.md`.
        """
        iss = check_references("Veja `.agents/skills/outra-skill/SKILL.md`.",
                               {"SKILL.md"})
        assert [i.code for i in iss] == ["REFERENCE_CROSS_SKILL"]
        assert iss[0].severity is Severity.INFO

    @pytest.mark.parametrize("texto", [
        "[x](../fora.md)",
        "[x](../../etc/passwd)",
        "[x](C:/Windows/win.ini)",
        "`C:/Windows/x.md`",
        "[x](\\\\servidor\\share\\x.md)",
    ])
    def test_escape_e_reportado_como_aviso_nunca_como_bloqueio(self, texto):
        """Citar caminho fora do payload é aviso de portabilidade.

        A versão anterior promovia isto a ERROR e recusava a importação. Medido
        contra os 48 SKILL.md reais: 16 de 53 Skills (33%) que importavam
        passaram a ser recusadas — incluindo Skills de monorepo que citam
        `../../../docs/...` de propósito. Referência é TEXTO; a segurança de
        caminho real acontece em paths.py/safe_extract.py. Nenhuma Skill pode
        ser recusada por causa do que ela escreve.
        """
        iss = check_references(texto, {"SKILL.md"})
        assert any(i.code == "REFERENCE_ESCAPE" for i in iss), texto
        assert all(i.severity is not Severity.ERROR for i in iss), texto

    @pytest.mark.parametrize("rota", ["/json/list", "/json/version", "/", "/api/v1/x"])
    def test_rota_http_em_prosa_nao_e_referencia_de_arquivo(self, rota):
        """Endpoint CDP numa Skill de operação não é caminho de arquivo."""
        assert check_references(f"Enumere `{rota}` no endpoint.", {"SKILL.md"}) == []
        assert escaping_references(f"`{rota}`") == []

    def test_escaping_references_reporta_em_vez_de_silenciar(self):
        assert escaping_references("[x](../fora.md)") == ["../fora.md"]

    def test_referenced_files_nao_inclui_fuga(self):
        assert referenced_files("[x](../fora.md)") == []

    @pytest.mark.parametrize("texto", [
        "Rode `python -m pytest`.",
        "URL https://exemplo.com/x.md",
        "Âncora [a](#secao).",
        "Use `--flag=valor` na linha de comando.",
    ])
    def test_prosa_normal_nao_gera_falso_positivo(self, texto):
        """Comando, URL e âncora não são referência de arquivo."""
        assert escaping_references(texto) == []
        assert check_references(texto, {"SKILL.md"}) == []

    def test_caminho_de_exemplo_citado_e_avisado_como_ausente(self):
        """Citar `path/to/file.md` num recurso que não o tem É referência
        ausente — aviso de propósito. Bloquear seria recusar Skill legítima;
        silenciar esconderia arquivo de apoio faltando."""
        iss = check_references("Use `path/to/file.md` como exemplo.",
                               {"SKILL.md"})
        assert [i.code for i in iss] == ["REFERENCE_MISSING"]
        assert iss[0].severity.value == "warning", "aviso, nunca bloqueio"

    def test_url_nao_e_referencia_de_arquivo(self):
        assert referenced_files("Veja https://exemplo.com/doc.md") == []

    def test_importacao_de_skill_com_referencia_quebrada_ainda_passa(self, tmp_path):
        """Referência quebrada é aviso, não bloqueio — não recusar skill legítima."""
        hub = _hub(tmp_path)
        src = _skill(tmp_path / "src", corpo="Leia `nao-existe.md`.\n")
        r = hub.import_path(str(src))
        assert r.ok is True
        assert any(i["code"] == "REFERENCE_MISSING" for i in r.issues)

    def test_importacao_com_fuga_de_fronteira_importa_e_avisa(self, tmp_path):
        """O recurso importa; a fuga vira aviso. O alvo nunca é lido."""
        hub = _hub(tmp_path)
        src = _skill(tmp_path / "src", corpo="Veja [x](../../../docs/guia.md).\n")
        r = hub.import_path(str(src))
        assert r.ok is True, "referência em prosa não pode recusar o recurso"
        assert any(i["code"] == "REFERENCE_ESCAPE" for i in r.issues)


# =========================================================== C5 — folder_name
class TestC5FolderName:
    """Antes: a pasta vinha do primeiro segmento de um caminho INTERNO.
    Recurso flat com `docs/x.md` era comparado contra `docs`; sem subpasta,
    virava None e a checagem de coerência nem rodava."""

    @pytest.mark.parametrize("upstream,esperado", [
        ("/home/u/minha-skill", "minha-skill"),
        ("C:\\Users\\u\\minha-skill", "minha-skill"),
        ("/home/u/pacote.zip", None),
        ("/home/u/notas.md", None),
        (None, None),
        ("", None),
    ])
    def test_pasta_vem_da_origem(self, upstream, esperado):
        assert folder_name_do_recurso(upstream, ["SKILL.md"]) == esperado

    def test_subpasta_interna_nao_e_a_pasta_do_recurso(self):
        """O defeito original: `docs` é conteúdo, não a pasta."""
        assert folder_name_do_recurso("/home/u/minha-skill",
                                      ["SKILL.md", "docs/guia.md"]) == "minha-skill"

    def test_importador_usa_a_pasta_de_origem(self, tmp_path, monkeypatch):
        import lia_agenthub.adapters.importer as imp

        capturado = []
        original = imp.validate_skill

        def espiao(text, *, folder_name=None):
            capturado.append(folder_name)
            return original(text, folder_name=folder_name)

        monkeypatch.setattr(imp, "validate_skill", espiao)

        hub = _hub(tmp_path)
        src = _skill(tmp_path / "minha-skill", extras={"docs/guia.md": "# g"})
        hub.import_path(str(src))

        assert capturado == ["minha-skill"], \
            "a checagem deve comparar com a pasta apontada, não com `docs`"

    def test_validacao_usa_a_pasta_de_origem(self, tmp_path, monkeypatch):
        import lia_agenthub.app as app_mod

        hub = _hub(tmp_path)
        src = _skill(tmp_path / "minha-skill", extras={"docs/guia.md": "# g"})
        r = hub.import_path(str(src))
        hub.promote(r.capability_id)

        capturado = []
        original = app_mod.validate_skill

        def espiao(text, *, folder_name=None):
            capturado.append(folder_name)
            return original(text, folder_name=folder_name)

        monkeypatch.setattr(app_mod, "validate_skill", espiao)
        hub.validate(r.capability_id)
        assert capturado == ["minha-skill"]

    def test_nome_igual_a_pasta_nao_gera_aviso(self, tmp_path):
        hub = _hub(tmp_path)
        src = _skill(tmp_path / "coerente", nome="coerente")
        r = hub.import_path(str(src))
        assert not [i for i in r.issues if i["code"] == "NAME_FOLDER_MISMATCH"]

    def test_nome_diferente_da_pasta_gera_aviso(self, tmp_path):
        hub = _hub(tmp_path)
        src = _skill(tmp_path / "pasta-diferente", nome="outro-nome")
        r = hub.import_path(str(src))
        assert any(i["code"] == "NAME_FOLDER_MISMATCH" for i in r.issues)

    def test_zip_nao_inventa_pasta(self, tmp_path):
        hub = _hub(tmp_path)
        z = tmp_path / "p.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("SKILL.md", "---\nname: x\ndescription: d\n---\n")
        r = hub.import_path(str(z))
        assert r.ok is True
        assert not [i for i in r.issues if i["code"] == "NAME_FOLDER_MISMATCH"]


# ============================================================== C8 — índice
class TestC8SchemaDoIndice:
    """Antes: `check_consistency` acusava `superseded`/`archived` como
    problema, e o índice não declarava escopo nem estado."""

    def test_indice_declara_escopo(self, tmp_path):
        hub = _hub(tmp_path)
        r = hub.import_path(str(_skill(tmp_path / "src")))
        hub.promote(r.capability_id)
        idx = build_index(hub.repo)
        assert idx["scope"] == "active"
        assert idx["scopeNote"]

    def test_entrada_traz_lifecycle(self, tmp_path):
        hub = _hub(tmp_path)
        r = hub.import_path(str(_skill(tmp_path / "src")))
        hub.promote(r.capability_id)
        idx = build_index(hub.repo)
        assert idx["capabilities"][0]["lifecycle"] == "active"

    def test_superseded_fica_fora_do_indice_sem_virar_inconsistencia(self, tmp_path):
        loc = resolve_locations(tmp_path / "h")
        loc.ensure()
        _registro_manual(loc, "velha", lifecycle="superseded")
        _registro_manual(loc, "ativa", lifecycle="active")

        idx = build_index(Repository(loc))
        assert [c["id"] for c in idx["capabilities"]] == ["ativa"]

        cons = check_consistency(idx, loc.exports, loc.library)
        assert cons["ok"] is True, "estado fora do índice por desenho não é erro"
        assert cons["notIndexed"] == []
        assert cons["notIndexedByState"] == {"velha": "superseded"}

    def test_ativa_fora_do_indice_continua_sendo_inconsistencia(self, tmp_path):
        loc = resolve_locations(tmp_path / "h")
        loc.ensure()
        _registro_manual(loc, "ativa", lifecycle="active")
        idx = build_index(Repository(loc))
        idx["capabilities"] = []          # simula índice desatualizado
        cons = check_consistency(idx, loc.exports, loc.library)
        assert cons["ok"] is False
        assert cons["notIndexed"] == ["ativa"]

    def test_quarentena_nunca_entra_no_indice(self, tmp_path):
        loc = resolve_locations(tmp_path / "h")
        loc.ensure()
        _registro_manual(loc, "em-quarentena", lifecycle="quarantined")
        idx = build_index(Repository(loc))
        assert idx["capabilities"] == []

    def test_indice_com_quarentena_e_recusado_na_validacao(self):
        idx = {
            "schemaVersion": 1, "generatedAt": "x", "signed": False,
            "capabilities": [{
                "id": "q", "name": "q", "version": "1.0.0",
                "type": "agent-skill", "trust": "unreviewed",
                "license": None, "lifecycle": "quarantined"}],
        }
        problemas = validate_index(idx)
        assert any("quarentena" in p for p in problemas)

    def test_indice_antigo_sem_campos_novos_continua_valido(self):
        """Compatibilidade: exigir `scope`/`lifecycle` invalidaria todo índice
        já publicado. São aditivos."""
        antigo = {
            "schemaVersion": 1, "generatedAt": "2026-01-01T00:00:00+00:00",
            "signed": False,
            "capabilities": [{
                "id": "a", "name": "a", "version": "1.0.0",
                "type": "agent-skill", "trust": "unreviewed", "license": None}],
        }
        assert validate_index(antigo) == []

    def test_schema_declara_lifecycle_e_escopo(self):
        props = SCHEMA["properties"]["capabilities"]["items"]["properties"]
        assert "lifecycle" in props
        assert SCHEMA["properties"]["scope"]["const"] == "active"

    def test_lifecycle_invalido_no_indice_e_recusado(self):
        idx = {
            "schemaVersion": 1, "generatedAt": "x", "signed": False,
            "capabilities": [{
                "id": "a", "name": "a", "version": "1.0.0",
                "type": "agent-skill", "trust": "unreviewed", "license": None,
                "lifecycle": "inventado"}],
        }
        assert any("lifecycle" in p for p in validate_index(idx))

    def test_publicacao_grava_indice_valido(self, tmp_path):
        hub = _hub(tmp_path)
        r = hub.import_path(str(_skill(tmp_path / "src")))
        hub.promote(r.capability_id)
        res = hub.publish_index()
        assert res["ok"] and res["count"] == 1
        lido = hub.read_index()
        assert lido["scope"] == "active"
        assert validate_index(lido) == []
