"""Contratos de integração: o Hub é utilizável pelos hosts Lia?

Cada classe corresponde a um projeto consumidor e verifica o que ELE precisa,
não o que a API por acaso oferece. Se um teste daqui quebrar, um host real
quebra — não é teste de unidade disfarçado.

Princípio que atravessa todos: o Hub entrega METADADO e PACOTE. Ele não
executa, não autoriza, não guarda segredo e não decide confiança. Os testes
negativos verificam que essa fronteira resiste.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from lia_agenthub.adapters.paths_resolver import resolve_locations
from lia_agenthub.app import AgentHub
from lia_agenthub.adapters.index_builder import INDEX_REQUIRED_KEYS


@pytest.fixture
def hub(tmp_path):
    return AgentHub(resolve_locations(tmp_path / "hub"))


def _skill(pasta: Path, nome: str = "sk", *, corpo: str = "Corpo.\n",
           frontmatter: str | None = None, arquivos: dict[str, str] | None = None) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    fm = frontmatter if frontmatter is not None else f"name: {nome}\ndescription: Descrição de {nome}.\n"
    (pasta / "SKILL.md").write_text(f"---\n{fm}---\n\n{corpo}", encoding="utf-8")
    for k, v in (arquivos or {}).items():
        alvo = pasta / k
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text(v, encoding="utf-8")
    return pasta


def _publicada(hub: AgentHub, tmp_path: Path, nome: str = "sk") -> str:
    r = hub.import_path(str(_skill(tmp_path / nome, nome)))
    hub.promote(r.capability_id)
    return r.capability_id


# ==========================================================================
# Lia Go — host de referência. Consome, não produz.
# ==========================================================================
class TestContratoLiaGo:
    """O que o Lia Go precisa para exibir e oferecer capacidades ao usuário.

    Lia Go é o primeiro host de referência (contrato §10). Ele lê o índice,
    apresenta, e depois o USUÁRIO decide. O Hub não pode decidir por ele.
    """

    def test_indice_publicado_tem_as_chaves_que_o_host_le(self, hub, tmp_path):
        """Host que lê o índice não pode quebrar porque uma chave sumiu."""
        _publicada(hub, tmp_path)
        hub.publish_index()
        idx = hub.read_index()
        assert idx is not None
        for chave in INDEX_REQUIRED_KEYS:
            assert chave in idx, f"chave `{chave}` ausente do índice"

    def test_indice_declara_que_nao_e_lista_completa(self, hub, tmp_path):
        """Sem isto o host mostra menos do que existe e não sabe por quê."""
        _publicada(hub, tmp_path)
        hub.publish_index()
        idx = hub.read_index()
        assert idx["scope"] == "active"
        assert idx["scopeNote"]

    def test_indice_nunca_publica_quarentena(self, hub, tmp_path):
        """Publicar quarentena converteria 'não revisado' em 'disponível'.

        Este é o teste de segurança mais importante do contrato: o índice é
        feito para circular, a quarentena não.
        """
        r = hub.import_path(str(_skill(tmp_path / "nq", "nq")))  # fica na quarentena
        hub.publish_index()
        idx = hub.read_index()
        ids = [c["id"] for c in idx["capabilities"]]
        assert r.capability_id not in ids

    def test_indice_nao_promete_assinatura(self, hub, tmp_path):
        """Hash não é assinatura. Se o host achar que é, confia em quem não devia."""
        _publicada(hub, tmp_path)
        hub.publish_index()
        idx = hub.read_index()
        assert idx["signed"] is False
        assert idx.get("signatureNote")

    def test_host_pode_consumir_pacote_por_arquivo(self, hub, tmp_path):
        """Lia Go pode não ter Python. O pacote tem que ser autodescritivo."""
        cid = _publicada(hub, tmp_path)
        e = hub.export(cid, target="private", destination=str(tmp_path / "out"))
        zf = zipfile.ZipFile(e["path"])
        assert "manifest.json" in zf.namelist()
        man = json.loads(zf.read("manifest.json"))
        assert man["hashes"]["contentHash"]


# ==========================================================================
# Lia Studio — ambiente de desenvolvimento. Autora e testa Skills.
# ==========================================================================
class TestContratoLiaStudio:
    """Studio escreve SKILL.md e quer saber ANTES de importar se está bom.

    A pergunta central: "meu arquivo tem problema?" — e a resposta não pode
    ser 'não' quando há problema, nem 'sim' quando só há prosa.
    """

    def test_dry_run_nao_escreve_nada(self, hub, tmp_path):
        """Autor roda validação o tempo todo. Não pode poluir a biblioteca."""
        src = _skill(tmp_path / "draft", "draft")
        r = hub.import_path(str(src), dry_run=True)
        assert r.ok
        assert hub.items() == []
        assert not hub.repo.exists_anywhere(r.capability_id)

    def test_dry_run_diz_o_que_seria_gravado(self, hub, tmp_path):
        src = _skill(tmp_path / "draft2", "draft2")
        r = hub.import_path(str(src), dry_run=True)
        assert r.name == "draft2"
        assert r.capability_id, "o autor precisa saber o id que teria"
        assert r.staged_at is None, "nada foi estagiado"

    def test_erro_estrutural_e_dito_com_codigo(self, hub, tmp_path):
        """Studio mostra a mensagem ao autor. Tem que ser acionável."""
        src = tmp_path / "ruim"
        src.mkdir()
        (src / "SKILL.md").write_text("sem frontmatter nenhum\n", encoding="utf-8")
        r = hub.import_path(str(src))
        assert not r.ok
        assert "NO_FRONTMATTER" in r.blocked_reason

    def test_prosa_estranha_nao_impede_o_autor_de_trabalhar(self, hub, tmp_path):
        """Skill que cita endpoint, rota de monorepo e outra Skill: importa.

        Foi exatamente aqui que a versão anterior recusava 30% do acervo.
        """
        corpo = ("Enumere `/json/list`. Ver `../../../docs/matriz.md`.\n"
                 "Combine com `.agents/skills/outra/SKILL.md`.\n")
        r = hub.import_path(str(_skill(tmp_path / "prosa", "prosa", corpo=corpo)))
        assert r.ok is True, r.blocked_reason

    def test_autor_ve_avisos_sem_que_sejam_bloqueio(self, hub, tmp_path):
        r = hub.import_path(str(_skill(tmp_path / "av", "av",
                                       corpo="Ver `nao-existe.md`.\n")))
        assert r.ok
        codigos = [i["code"] for i in r.issues]
        assert "REFERENCE_MISSING" in codigos
        assert not [i for i in r.issues if i["severity"] == "error"]


# ==========================================================================
# Lia-Project — infraestrutura. Distribui para os demais.
# ==========================================================================
class TestContratoLiaProject:
    """Project precisa publicar pacotes íntegros e provar que não mudaram."""

    def test_pacote_e_verificavel_por_quem_recebe(self, hub, tmp_path):
        """O receptor não tem a biblioteca do emissor; só o arquivo."""
        cid = _publicada(hub, tmp_path, "infra")
        e = hub.export(cid, target="private", destination=str(tmp_path / "dist"))
        v = hub.verify_package(e["path"])
        assert v["ok"] is True

    def test_pacote_adulterado_e_detectado(self, hub, tmp_path):
        """Trocar um byte no payload tem que invalidar o pacote."""
        cid = _publicada(hub, tmp_path, "infra2")
        e = hub.export(cid, target="private", destination=str(tmp_path / "dist"))
        original = Path(e["path"])
        adulterado = tmp_path / "adulterado.lia-capability"
        with zipfile.ZipFile(original) as zin, zipfile.ZipFile(adulterado, "w") as zout:
            for item in zin.infolist():
                dados = zin.read(item.filename)
                if item.filename.endswith("SKILL.md"):
                    dados = dados.replace(b"Corpo.", b"Adulterado.")
                zout.writestr(item, dados)
        v = hub.verify_package(str(adulterado))
        assert v["ok"] is False

    def test_exportacao_em_lote_nao_aborta_por_uma_falha(self, hub, tmp_path):
        """Distribuir 50 recursos: um problema não pode parar os outros 49."""
        ids = [_publicada(hub, tmp_path, f"lote{i}") for i in range(3)]
        r = hub.export_many(ids + ["inexistente-0000"], target="private",
                            destination=str(tmp_path / "lote"))
        resultados = r.get("results") or r.get("items") or []
        assert len(resultados) == 4
        assert sum(1 for x in resultados if x.get("ok")) == 3

    def test_exportacao_nao_leva_metadado_interno(self, hub, tmp_path):
        """.lia/ é do Hub. Não viaja no pacote."""
        cid = _publicada(hub, tmp_path, "semlia")
        e = hub.export(cid, target="private", destination=str(tmp_path / "out"))
        nomes = zipfile.ZipFile(e["path"]).namelist()
        assert not [n for n in nomes if n.startswith(".lia/") or "/.lia/" in n]


# ==========================================================================
# Lia Forge — consumidor criativo. Descobre e usa.
# ==========================================================================
class TestContratoLiaForge:
    """Forge busca capacidade por tema e precisa de metadado para escolher."""

    def test_descricao_e_buscavel(self, hub, tmp_path):
        """Sem descrição não há como descobrir. Era o defeito de P-E1."""
        src = _skill(tmp_path / "audio", "audio",
                     frontmatter="name: audio\ndescription: Planejar áudio de jogo.\n")
        hub.promote(hub.import_path(str(src)).capability_id)
        achados = hub.items()
        assert achados and achados[0]["description"] == "Planejar áudio de jogo."

    def test_tags_e_dominio_chegam_ao_consumidor(self, hub, tmp_path):
        src = _skill(tmp_path / "tag", "tag",
                     frontmatter=("name: tag\ndescription: d\n"
                                  "metadata: domain: audio, tags: vfx, ui\n"))
        hub.promote(hub.import_path(str(src)).capability_id)
        item = hub.items()[0]
        assert item["domain"] == "audio"
        assert "vfx" in item["tags"]

    def test_licenca_viaja_com_o_recurso(self, hub, tmp_path):
        """Forge redistribui conteúdo. Precisa saber a licença de cada um."""
        src = _skill(tmp_path / "lic", "lic",
                     frontmatter="name: lic\ndescription: d\nlicense: MIT\n",
                     arquivos={"LICENSE.md": "MIT License\n\nCopyright (c) 2026 Fulano\n"})
        r = hub.import_path(str(src))
        lic = hub.detail(r.capability_id)["license"]
        assert lic["code"] == "MIT"
        assert lic["redistributable"] is False, "declarado não é autorizado"

    def test_forge_nao_recebe_capacidade_em_quarentena(self, hub, tmp_path):
        """Descobrir != estar liberado. Quarentena não aparece na lista."""
        hub.import_path(str(_skill(tmp_path / "qq", "qq")))
        assert hub.items() == []


# ==========================================================================
# Lia Model Lab — catálogo e descoberta de modelos.
# ==========================================================================
class TestContratoModelLab:
    """Model Lab cataloga modelos; o Hub é referência de MECANISMO."""

    def test_registro_sobrevive_a_roundtrip(self, hub, tmp_path):
        """Catalogar exige poder reescrever o que foi lido, sem perder dado."""
        # `domain` vive dentro de `metadata:` no formato Agent Skills. As duas
        # grafias aparecem em acervo real: inline e em bloco. O Hub aceita as
        # duas — antes só a inline funcionava e a de bloco se perdia.
        src = _skill(tmp_path / "rt", "rt",
                     frontmatter="name: rt\ndescription: d\nmetadata:\n  domain: modelos\n")
        hub.promote(hub.import_path(str(src)).capability_id)
        item = hub.items()[0]
        assert item["description"] == "d"
        assert item["domain"] == "modelos"
        # O catálogo precisa poder REESCREVER o que leu sem perder dado.
        # `detail()` é a visão completa; `items()` é a de lista.
        assert hub.detail(item["id"])["description"] == "d"

    def test_campo_desconhecido_nao_derruba_a_leitura(self, hub, tmp_path):
        """Catálogo grande tem registro de versão futura. Não pode quebrar."""
        from lia_agenthub.domain.model import License
        lic = License.from_dict({"code": "MIT", "campoDeVersaoFutura": {"x": 1}})
        assert lic.as_dict()["campoDeVersaoFutura"] == {"x": 1}

    def test_hash_identifica_conteudo_nao_autoria(self, hub, tmp_path):
        """O hash prova integridade. NÃO diz quem escreveu.

        Dois recursos com conteúdo idêntico têm o mesmo `contentHash` mesmo
        vindo de origens diferentes — é o que permite detectar espelho e
        duplicata. Confundir isso com autoria é o erro que o modelo recusa.
        """
        # Mesmo conteúdo, pastas de origem diferentes: o hash TEM que bater.
        # É isso que permite detectar espelho/duplicata sem confiar em nome.
        a = _skill(tmp_path / "a", "igual")
        b = _skill(tmp_path / "b", "igual")
        ra = hub.import_path(str(a))
        rb = hub.import_path(str(b))
        assert ra.hashes["contentHash"] == rb.hashes["contentHash"]
        assert hub.detail(ra.capability_id)["treeHash"] == \
               hub.detail(rb.capability_id)["treeHash"]
        # ...e mesmo assim NÃO é uma decisão de autoria: hash igual não move
        # a confiança nem autoriza redistribuição.
        det = hub.detail(ra.capability_id)
        assert det["trust"] == "unreviewed"
        assert det["license"] is None or det["license"]["redistributable"] is False


# ==========================================================================
# Fronteiras — o que o Hub NÃO faz, em nenhuma circunstância
# ==========================================================================
class TestFronteirasQueNaoPodemCeder:
    """O Hub não é runtime. Estes testes falham se alguém tentar torná-lo."""

    def test_importar_nunca_executa(self, hub, tmp_path):
        """Skill com script: o script é ARMAZENADO, nunca rodado."""
        marcador = tmp_path / "EXECUTOU"
        src = _skill(tmp_path / "malicioso", "m",
                     arquivos={"run.sh": f"#!/bin/sh\ntouch {marcador}\n"})
        r = hub.import_path(str(src))
        assert r.ok
        assert r.contains_scripts is True
        assert not marcador.exists(), "conteúdo importado foi EXECUTADO"

    def test_importar_nao_grava_fora_do_hub(self, hub, tmp_path):
        antes = set(tmp_path.iterdir())
        hub.import_path(str(_skill(tmp_path / "normal", "n")))
        depois = set(tmp_path.iterdir())
        novos = {p.name for p in depois - antes} - {"normal"}
        assert novos <= {"hub"}, f"escreveu fora: {novos}"

    def test_nenhum_segredo_aparece_no_registro(self, hub, tmp_path):
        """O Hub guarda NOME de variável, nunca valor."""
        src = _skill(tmp_path / "sec", "sec",
                     frontmatter=("name: sec\ndescription: d\n"
                                  "metadata: requirements: OPENAI_API_KEY\n"))
        r = hub.import_path(str(src))
        d = hub.detail(r.capability_id)
        blob = json.dumps(d, ensure_ascii=False)
        # Nenhum valor de credencial aparece no registro.
        for forma in ("sk-", "Bearer ", "password=", "api_key="):
            assert forma not in blob, forma
        # `secrets` é uma ESTRUTURA de nomes, nunca de valores. Hoje o
        # extrator de `requirements` a partir do frontmatter não está
        # implementado (é P-E7, fora do escopo autorizado), então a lista
        # vem vazia — e vazia é honesto: nada foi declarado, nada foi lido.
        assert isinstance(d["secrets"], dict)
        assert d["secrets"]["envVars"] == []

    def test_trust_comeca_nao_revisado_e_exige_humano(self, hub, tmp_path):
        """Confiança não é inferida do conteúdo nem do hash."""
        r = hub.import_path(str(_skill(tmp_path / "cr", "cr")))
        assert hub.detail(r.capability_id)["trust"] == "unreviewed"
        # A escala não tem "trusted" binário: quem confia diferencia QUEM
        # revisou. "unreviewed" é o único ponto de partida honesto.
        assert "trusted" not in [t.value for t in __import__(
            "lia_agenthub.domain.model", fromlist=["Trust"]).Trust]
        hub.set_trust(r.capability_id, "reviewed-external", decided_by="humano")
        assert hub.detail(r.capability_id)["trust"] == "reviewed-external"


# ==========================================================================
# Auditoria adversarial — o que um atacante tentaria
# ==========================================================================
class TestAdversarial:
    """Vetores testados contra o Hub. Cada teste documenta um ataque real."""

    def test_zip_bomb_e_recusado(self, hub, tmp_path):
        """50 MB comprimido em 50 KB. Taxa de compressão é o sinal."""
        import io
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("SKILL.md", "---\nname: b\ndescription: d\n---\n")
            z.writestr("bomb.txt", "A" * (50 * 1024 * 1024))
        p = tmp_path / "bomb.zip"
        p.write_bytes(buf.getvalue())
        r = hub.import_path(str(p))
        assert not r.ok
        assert "compressão" in (r.blocked_reason or "").lower()

    def test_nome_de_arquivo_com_bidi_e_sinalizado(self, hub, tmp_path):
        """`a\\u202egnp.exe` — o bidi inverte o que o usuário VÊ.

        Antes disto, só o CORPO de .md/.txt/.json era varrido. O nome do
        arquivo passava limpo, então um script podia exibir um nome e ter
        outro.
        """
        src = _skill(tmp_path / "bidi", "bidi")
        (src / "a\u202egnp.exe").write_bytes(b"x")
        r = hub.import_path(str(src))
        codigos = [i["code"] for i in r.issues]
        assert "UNICODE_FILENAME" in codigos
        assert r.requires_review is True

    def test_payload_nao_pode_declarar_confianca(self, hub, tmp_path):
        """Falsificar `.lia/capability.json` com trust alto não passa."""
        src = _skill(tmp_path / "fake", "fake", arquivos={
            ".lia/capability.json": '{"trust": "first-party", "redistributable": true}'})
        r = hub.import_path(str(src))
        assert not r.ok
        assert ".lia" in (r.blocked_reason or "")

    def test_indice_editado_a_mao_listando_quarentena_e_detectado(self, hub, tmp_path):
        """Quem edita o índice para publicar quarentena é pego pela saúde.

        `validate_index` valida FORMA (e a forma é válida). Quem responde
        "este id não existe do lado ativo" é `index_health`. Sem esta
        separação, um índice adulterado pareceria só desatualizado.
        """
        r = hub.import_path(str(_skill(tmp_path / "q", "q")))  # quarentena
        pub = hub.publish_index()
        alvo = Path(pub["path"])
        idx = json.loads(alvo.read_text())
        idx["capabilities"].append({
            "id": r.capability_id, "name": "q", "version": "0.1.0",
            "type": "agent-skill", "trust": "first-party", "license": None,
            "package": "x.lia-capability", "lifecycle": "active"})
        alvo.write_text(json.dumps(idx), encoding="utf-8")
        saude = hub.index_health()
        assert saude["ok"] is False
        assert r.capability_id in saude["indexedButMissingOnDisk"]

    def test_publicacao_legitima_nunca_inclui_quarentena(self, hub, tmp_path):
        hub.import_path(str(_skill(tmp_path / "qq", "qq")))
        hub.publish_index()
        assert hub.read_index()["capabilities"] == []
