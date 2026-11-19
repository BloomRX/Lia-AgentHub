"""Leitura e classificação de inventário v1 — domínio puro, sem disco.

Cada teste aqui corresponde a uma regra do `CAPABILITY-INVENTORY-CONTRACT.md`
que não pode ser afrouxada. Quando um falhar, o contrato foi violado, não o teste.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from lia_agenthub.domain.inventory import (
    Classe,
    Conhecido,
    Severidade,
    classificar,
    ler,
)

EXEMPLO = Path(__file__).resolve().parents[2] / "docs" / "examples" / "central-capability-inventory.v1.json"


@pytest.fixture
def doc() -> dict:
    return json.loads(EXEMPLO.read_text(encoding="utf-8"))


def _bytes(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def _codigos(leitura) -> list[str]:
    return [a.code for a in leitura.achados]


def _erros(leitura) -> list[str]:
    return [a.code for a in leitura.erros]


# --------------------------------------------------------------------------
# Casos que DEVEM passar
# --------------------------------------------------------------------------
def test_exemplo_oficial_e_aceito_sem_achados(doc):
    """O exemplo do repositório é o caso de referência. Zero achado."""
    leitura = ler(_bytes(doc))
    assert leitura.ok is True
    assert leitura.achados == []
    assert leitura.envelope is not None
    assert leitura.envelope.inventory_version == 1
    assert leitura.envelope.issuer["project"] == "lia-forge"
    assert leitura.envelope.complete is False
    assert len(leitura.envelope.registros) == 1


def test_envelope_preserva_proveniencia_e_digest(doc):
    leitura = ler(_bytes(doc))
    env = leitura.envelope
    assert env.inventory_id == doc["inventoryId"]
    assert env.revision == doc["revision"]
    assert env.generated_at == doc["generatedAt"]
    assert env.file_digest == ler(_bytes(doc)).envelope.file_digest
    assert len(env.file_digest) == 64
    # digest do arquivo muda se um byte muda
    outro = ler(json.dumps(doc).encode("utf-8"))
    assert outro.envelope.file_digest != env.file_digest


def test_registro_preserva_conteudo_integral(doc):
    """Proveniência, licença, integridade e compatibilidade, campo a campo."""
    leitura = ler(_bytes(doc))
    reg = leitura.envelope.registros[0]
    original = doc["records"][0]

    assert reg.id == original["id"]
    assert reg.revision_id == original["revisionId"]
    assert reg.kind == original["kind"]
    assert reg.name == original["name"]
    # o conteúdo bruto é preservado inteiro, não resumido
    assert reg.bruto == original
    # e é cópia: mexer no original depois não corrompe o registro
    original["name"] = "mexido"
    assert reg.bruto["name"] != "mexido"


def test_records_vazio_e_valido(doc):
    """Lista vazia é diferente de ausente: omissão nunca apaga, vazio é vazio."""
    doc["records"] = []
    leitura = ler(_bytes(doc))
    assert leitura.ok is True
    assert leitura.envelope.registros == []


def test_model_lab_e_aceito_mas_marcado_inativo(doc):
    """Suspenso não é proibido: preservamos o histórico e avisamos."""
    doc["issuer"]["project"] = "lia-model-lab"
    leitura = ler(_bytes(doc))
    assert leitura.ok is True, "referência histórica precisa continuar legível"
    avisos = [a for a in leitura.achados if a.code == "ISSUER_INACTIVE_PROJECT"]
    assert len(avisos) == 1
    assert avisos[0].severity is Severidade.WARNING


def test_tipo_legado_e_mapeado_com_alias(doc):
    doc["records"][0]["kind"] = "cli-tool"
    leitura = ler(_bytes(doc))
    assert leitura.ok is True
    reg = leitura.envelope.registros[0]
    assert reg.kind == "cli"
    assert reg.tipo_legado == "cli-tool"
    assert "KIND_MAPPED_FROM_V1" in _codigos(leitura)


@pytest.mark.parametrize("tipo", ["api-service", "framework", "template", "reference", "unknown"])
def test_tipo_sem_kind_fica_pendente_e_fora_do_normalizado(doc, tipo):
    """O contrato manda manter esses tipos fora dos registros normalizados."""
    doc["records"][0]["kind"] = tipo
    leitura = ler(_bytes(doc))
    assert leitura.ok is True
    reg = leitura.envelope.registros[0]
    assert reg.kind is None, "não pode inventar `kind` para tipo sem correspondência"
    assert reg.tipo_legado == tipo
    assert "KIND_PENDING" in _codigos(leitura)


def test_campo_desconhecido_e_preservado_sem_efeito(doc):
    doc["records"][0]["customDoEmissor"] = {"nota": "valor qualquer"}
    doc["envelopeExtra"] = [1, 2, 3]
    leitura = ler(_bytes(doc))
    assert leitura.ok is True
    reg = leitura.envelope.registros[0]
    assert reg.desconhecidos == {"customDoEmissor": {"nota": "valor qualquer"}}
    assert leitura.envelope.desconhecidos == {"envelopeExtra": [1, 2, 3]}
    assert "ENVELOPE_UNKNOWN_FIELDS" in _codigos(leitura)


def test_null_e_lista_vazia_sao_diferentes(doc):
    """`null` é desconhecido; `[]` é vazio. O intake não pode confundir."""
    doc["records"][0]["description"] = None
    leitura = ler(_bytes(doc))
    assert leitura.envelope.registros[0].description is None
    assert leitura.envelope.registros[0].bruto["description"] is None


# --------------------------------------------------------------------------
# JSON malformado / schema incompatível
# --------------------------------------------------------------------------
def test_json_malformado_e_rejeitado_sem_gravar():
    leitura = ler(b'{"inventoryVersion": 1, "records": [}')
    assert leitura.ok is False
    assert leitura.envelope is None, "sem envelope não há o que gravar"
    assert "ENVELOPE_BAD_JSON" in _erros(leitura)


def test_nao_utf8_e_rejeitado():
    leitura = ler(b'{"inventoryVersion": 1, "name": "\xff\xfe"}')
    assert leitura.ok is False
    assert "ENVELOPE_NOT_UTF8" in _erros(leitura)


def test_raiz_precisa_ser_objeto():
    leitura = ler(b'[1, 2, 3]')
    assert leitura.ok is False
    assert "ENVELOPE_NOT_OBJECT" in _erros(leitura)


@pytest.mark.parametrize("versao", [2, 0, "1", 1.5, None])
def test_versao_incompativel_e_rejeitada_sem_gravacao(doc, versao):
    doc["inventoryVersion"] = versao
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert leitura.envelope is None
    assert any(c in _erros(leitura) for c in
               ("ENVELOPE_UNSUPPORTED_VERSION", "ENVELOPE_MISSING_VERSION"))


def test_chave_json_duplicada_e_rejeitada():
    """`json.loads` padrão manteria a última e descartaria a primeira."""
    texto = (b'{"inventoryVersion": 1, "revision": "a", "revision": "b", '
             b'"inventoryId": "x", "generatedAt": "2026-01-01T00:00:00Z", '
             b'"complete": true, "records": [], '
             b'"issuer": {"project": "lia-forge", "repository": null, "maintainer": null}}')
    leitura = ler(texto)
    assert leitura.ok is False
    assert "ENVELOPE_BAD_JSON" in _erros(leitura)
    assert "duplicada" in leitura.achados[0].message


@pytest.mark.parametrize("constante", [b"NaN", b"Infinity", b"-Infinity"])
def test_nan_e_infinity_nao_sao_json(constante):
    texto = b'{"inventoryVersion": 1, "x": ' + constante + b'}'
    leitura = ler(texto)
    assert leitura.ok is False
    assert "ENVELOPE_BAD_JSON" in _erros(leitura)


def test_documento_grande_demais_e_recusado_antes_de_processar(doc):
    from lia_agenthub.domain.inventory import MAX_BYTES
    leitura = ler(b" " * (MAX_BYTES + 1))
    assert leitura.ok is False
    assert "ENVELOPE_TOO_LARGE" in _erros(leitura)


# --------------------------------------------------------------------------
# Campos obrigatórios ausentes
# --------------------------------------------------------------------------
@pytest.mark.parametrize("campo", ["inventoryId", "revision", "complete", "records", "issuer"])
def test_campo_obrigatorio_ausente_no_envelope(doc, campo):
    doc.pop(campo)
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert leitura.envelope is None


def test_complete_precisa_ser_booleano(doc):
    doc["complete"] = "sim"
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "ENVELOPE_BAD_COMPLETE" in _erros(leitura)


@pytest.mark.parametrize("campo", ["project", "repository", "maintainer"])
def test_issuer_incompleto_e_rejeitado(doc, campo):
    doc["issuer"].pop(campo)
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "ISSUER_MISSING_FIELD" in _erros(leitura)


def test_generated_at_precisa_de_fuso(doc):
    """RFC 3339 sem fuso é ambíguo. O contrato exige fuso."""
    doc["generatedAt"] = "2026-11-18T00:00:00"
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "ENVELOPE_BAD_TIMESTAMP" in _erros(leitura)


def test_issuer_projeto_desconhecido_e_rejeitado(doc):
    doc["issuer"]["project"] = "projeto-inventado"
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "ISSUER_UNKNOWN_PROJECT" in _erros(leitura)


@pytest.mark.parametrize("campo", ["id", "revisionId", "kind", "name", "origins"])
def test_registro_sem_campo_obrigatorio_nao_e_identificavel(doc, campo):
    doc["records"][0].pop(campo)
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert leitura.envelope is None


def test_nome_vazio_e_rejeitado(doc):
    doc["records"][0]["name"] = "   "
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "RECORD_MISSING_NAME" in _erros(leitura)


# --------------------------------------------------------------------------
# Identidade
# --------------------------------------------------------------------------
@pytest.mark.parametrize("ident", [
    "revisao-de-asset",
    "urn:lia:cap:nao-e-uuid",
    "https://example.invalid/coisa",
    "",
])
def test_id_precisa_ser_urn_ou_ter_escopo(doc, ident):
    """ID derivado de nome, local, versão ou hash é proibido pelo contrato."""
    doc["records"][0]["id"] = ident
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert leitura.envelope is None


def test_par_id_revisao_repetido_no_envelope_e_erro(doc):
    doc["records"].append(copy.deepcopy(doc["records"][0]))
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "ENVELOPE_DUPLICATE_RECORD" in _erros(leitura)


def test_mesmo_id_com_revisoes_diferentes_no_mesmo_envelope_e_aceito(doc):
    segundo = copy.deepcopy(doc["records"][0])
    segundo["revisionId"] = "rev-002"
    segundo["name"] = "outra coisa"
    doc["records"].append(segundo)
    leitura = ler(_bytes(doc))
    assert leitura.ok is True
    assert len(leitura.envelope.registros) == 2


# --------------------------------------------------------------------------
# Proveniência e referências
# --------------------------------------------------------------------------
def test_origens_vazias_sao_rejeitadas(doc):
    doc["records"][0]["origins"] = []
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "RECORD_MISSING_ORIGINS" in _erros(leitura)


def test_caminho_absoluto_na_origem_e_rejeitado(doc):
    """Publicar caminho local vazaria a árvore de diretórios do emissor."""
    doc["records"][0]["origins"][0]["path"] = "C:/Users/alguem/segredo.md"
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "ORIGIN_ABSOLUTE_PATH" in _erros(leitura)


def test_caminho_absoluto_posix_na_origem_e_rejeitado(doc):
    doc["records"][0]["origins"][0]["path"] = "/etc/passwd"
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "ORIGIN_ABSOLUTE_PATH" in _erros(leitura)


def test_traversal_no_caminho_da_origem_e_rejeitado(doc):
    doc["records"][0]["origins"][0]["path"] = "../../fora.md"
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "ORIGIN_PATH_TRAVERSAL" in _erros(leitura)


def test_referencia_de_evidencia_inexistente_em_integrity_e_rejeitada(doc):
    """Referência que não resolve é proveniência quebrada, não detalhe."""
    # O exemplo tem `integrity: []` de propósito (desconhecido). Montamos o item.
    doc["records"][0]["integrity"] = [{"algorithm": "sha256", "scope": "payload",
                                       "digest": "a" * 64,
                                       "evidenceIds": ["ev-que-nao-existe"]}]
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "EVIDENCE_UNRESOLVED" in _erros(leitura)


def test_referencia_de_evidencia_inexistente_em_compatibility_e_rejeitada(doc):
    doc["records"][0]["compatibility"][0]["evidenceIds"] = ["ev-que-nao-existe"]
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "EVIDENCE_UNRESOLVED" in _erros(leitura)


def test_referencia_de_evidencia_em_origem_tambem_e_verificada(doc):
    """Regressão: `origins[].evidenceIds` ficou sem validação na primeira versão."""
    doc["records"][0]["origins"][0]["evidenceIds"] = ["ev-inexistente"]
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "EVIDENCE_UNRESOLVED" in _erros(leitura)


def test_evidencia_duplicada_e_rejeitada(doc):
    doc["evidence"] = [{"id": "ev-1"}, {"id": "ev-1"}]
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "EVIDENCE_DUPLICATE_ID" in _erros(leitura)


def test_evidencia_sem_campos_obrigatorios_e_rejeitada(doc):
    doc["evidence"] = [{"id": "ev-1"}]
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert any(a.code == "EVIDENCE_MISSING_FIELD" for a in leitura.erros)


def test_referencia_valida_resolve(doc):
    doc["evidence"] = [{
        "id": "ev-1", "kind": "commit", "locator": "https://example.invalid/c/abc",
        "recordedAt": "2026-11-01T00:00:00Z", "recordedBy": "maintainer",
        "subject": "record",
    }]
    doc["records"][0]["integrity"] = [{"algorithm": "sha256", "scope": "payload",
                                       "digest": "a" * 64, "evidenceIds": ["ev-1"]}]
    leitura = ler(_bytes(doc))
    assert leitura.ok is True


# --------------------------------------------------------------------------
# Hash e integridade
# --------------------------------------------------------------------------
@pytest.mark.parametrize("digest", [
    "abc",
    "g" * 64,
    "A" * 64,          # maiúsculas não são o formato do contrato
    "a" * 63,
    "a" * 65,
    None,
    12345,
])
def test_sha256_invalido_e_rejeitado(doc, digest):
    doc["records"][0]["integrity"] = [{"algorithm": "sha256", "scope": "payload",
                                       "digest": digest, "evidenceIds": []}]
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "INTEGRITY_BAD_SHA256" in _erros(leitura)


def test_sha256_valido_e_aceito(doc):
    doc["records"][0]["integrity"] = [{"algorithm": "sha256", "scope": "payload",
                                       "digest": "a" * 64, "evidenceIds": []}]
    leitura = ler(_bytes(doc))
    assert leitura.ok is True


# --------------------------------------------------------------------------
# Licença
# --------------------------------------------------------------------------
@pytest.mark.parametrize("status", ["gratis", "livre", "permitido", ""])
def test_status_de_redistribuicao_invalido_e_rejeitado(doc, status):
    doc["records"][0]["license"]["redistribution"]["status"] = status
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "LICENSE_BAD_REDISTRIBUTION" in _erros(leitura)


def test_allowed_sem_autorizacao_e_rejeitado(doc):
    """`allowed` sem autorização é exatamente a promoção automática proibida."""
    doc["records"][0]["license"]["redistribution"] = {
        "status": "allowed", "authorizationIds": []}
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "LICENSE_ALLOWED_WITHOUT_AUTHORIZATION" in _erros(leitura)


def test_allowed_com_autorizacao_que_nao_resolve_e_rejeitado(doc):
    doc["records"][0]["license"]["redistribution"] = {
        "status": "allowed", "authorizationIds": ["auth-fantasma"]}
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "LICENSE_UNRESOLVED_AUTHORIZATION" in _erros(leitura)


def test_licenca_desconhecida_nao_vira_permissao(doc):
    """`unknown` é aceito como declaração — e continua sendo desconhecido."""
    doc["records"][0]["license"] = {"declared": None, "components": [],
                                    "redistribution": {"status": "unknown",
                                                       "authorizationIds": []}}
    leitura = ler(_bytes(doc))
    assert leitura.ok is True
    reg = leitura.envelope.registros[0]
    assert reg.bruto["license"]["redistribution"]["status"] == "unknown"
    # Nada no intake promove licença desconhecida.
    assert "allowed" not in json.dumps(reg.bruto["license"])


# --------------------------------------------------------------------------
# Compatibilidade
# --------------------------------------------------------------------------
@pytest.mark.parametrize("status", ["verificado", "OK", "instalado"])
def test_resultado_de_compatibilidade_invalido_e_rejeitado(doc, status):
    doc["records"][0]["compatibility"][0]["result"] = status
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "COMPATIBILITY_BAD_RESULT" in _erros(leitura)


# --------------------------------------------------------------------------
# Segredos e conteúdo executável
# --------------------------------------------------------------------------
@pytest.mark.parametrize("segredo", [
    "AIzaSyA1234567890abcdefghijklmnopqrstu",
    "ghp_1234567890abcdefghijklmnopqrstuvwxyz",
    "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abc",
    "-----BEGIN PRIVATE KEY-----",
    "https://usuario:senha123@example.invalid/repo",
    "aws_secret_access_key=abcdefghijklmnop",
])
def test_segredo_em_qualquer_campo_recusa_o_documento(doc, segredo):
    """O intake recusa o documento inteiro — segredo não entra nem como metadado."""
    doc["records"][0]["description"] = segredo
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "SECRET_IN_INVENTORY" in _erros(leitura)


def test_segredo_aninhado_em_campo_desconhecido_tambem_e_pego(doc):
    doc["records"][0]["extra"] = {"deep": [{"token": "ghp_abcdefghijklmnopqrstuvwxyz0123456789"}]}
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "SECRET_IN_INVENTORY" in _erros(leitura)


def test_conteudo_executavel_como_campo_nao_e_executado(doc, tmp_path):
    """Comando no campo desconhecido vira dado preservado, jamais execução."""
    marcador = tmp_path / "EXECUTOU"
    doc["records"][0]["installCommand"] = f"touch {marcador}"
    doc["records"][0]["postinstall"] = f"rm -rf /tmp/nada"
    doc["records"][0]["entrypoint"] = f"python -c 'open(\"{marcador}\",\"w\")'"
    leitura = ler(_bytes(doc))

    assert leitura.ok is True
    assert not marcador.exists(), "o intake NUNCA executa conteúdo do inventário"
    reg = leitura.envelope.registros[0]
    assert "installCommand" in reg.desconhecidos


# --------------------------------------------------------------------------
# Classificação
# --------------------------------------------------------------------------
def _registro(doc):
    return ler(_bytes(doc)).envelope.registros[0]


def test_classificacao_novo(doc):
    reg = _registro(doc)
    (c,) = classificar([reg], [])
    assert c.classe is Classe.NOVO
    assert c.admitido is True


def test_classificacao_duplicata_exata_e_idempotente(doc):
    reg = _registro(doc)
    conhecido = Conhecido(reg.id, reg.revision_id, reg.digest,
                          name=reg.name, version=reg.version)
    (c,) = classificar([reg], [conhecido])
    assert c.classe is Classe.DUPLICATA_EXATA
    assert c.admitido is True


def test_classificacao_conflito_de_identidade_bloqueia(doc):
    """Mesmo id + mesma revisão + digest diferente: bloqueia e preserva."""
    reg = _registro(doc)
    conhecido = Conhecido(reg.id, reg.revision_id, "b" * 64)
    (c,) = classificar([reg], [conhecido])
    assert c.classe is Classe.CONFLITO_IDENTIDADE
    assert c.admitido is False, "sobrescrever revisão disputada perderia o outro relato"
    assert c.relacionados == [reg.id]


def test_classificacao_atualizacao_preserva_anterior(doc):
    reg = _registro(doc)
    conhecido = Conhecido(reg.id, "rev-000", "c" * 64, version="0.9.0")
    (c,) = classificar([reg], [conhecido])
    assert c.classe is Classe.ATUALIZACAO
    assert c.admitido is True
    assert "anterior permanece" in c.motivo


def test_classificacao_downgrade_exige_escolha(doc):
    doc["records"][0]["version"] = "1.0.0"
    reg = _registro(doc)
    conhecido = Conhecido(reg.id, "rev-000", "c" * 64, version="2.0.0")
    (c,) = classificar([reg], [conhecido])
    assert c.classe is Classe.DOWNGRADE
    assert c.admitido is False, "downgrade exige escolha explícita do host"


def test_classificacao_mesmo_conteudo_em_id_diferente(doc):
    reg = _registro(doc)
    outro_id = "urn:lia:cap:11111111-2222-3333-4444-555555555555"
    conhecido = Conhecido(outro_id, "rev-x", reg.digest)
    (c,) = classificar([reg], [conhecido])
    assert c.classe is Classe.MESMO_CONTEUDO
    assert c.admitido is True
    assert c.relacionados == [outro_id]
    assert "hash não identifica autoria" in c.motivo


def test_classificacao_sobreposicao_por_nome(doc):
    reg = _registro(doc)
    outro_id = "urn:lia:cap:11111111-2222-3333-4444-555555555555"
    conhecido = Conhecido(outro_id, "rev-x", "d" * 64, name=reg.name)
    (c,) = classificar([reg], [conhecido])
    assert c.classe is Classe.SOBREPOSICAO
    assert c.admitido is True
    assert c.relacionados == [outro_id]


def test_classificacao_tipo_pendente_nao_e_admitido(doc):
    doc["records"][0]["kind"] = "framework"
    reg = _registro(doc)
    (c,) = classificar([reg], [])
    assert c.classe is Classe.TIPO_PENDENTE
    assert c.admitido is False


def test_downgrade_com_esquema_desconhecido_nao_e_inventado(doc):
    """Sem semver nos dois lados, não se afirma downgrade — preserva a grafia."""
    doc["records"][0]["version"] = "v1"
    reg = _registro(doc)
    conhecido = Conhecido(reg.id, "rev-000", "c" * 64, version="v9")
    (c,) = classificar([reg], [conhecido])
    assert c.classe is Classe.ATUALIZACAO


# --------------------------------------------------------------------------
# Aliases escopados e colisões de identidade
# --------------------------------------------------------------------------
def test_alias_precisa_de_scheme_value_e_authority(doc):
    doc["records"][0]["aliases"] = [
        {"scheme": "upstream", "value": "skill:abc"}
    ]
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "ALIAS_MISSING_FIELD" in _erros(leitura)


def test_alias_repetido_no_mesmo_registro_e_rejeitado(doc):
    alias = {"scheme": "upstream", "value": "skill:abc",
             "authority": "lia-forge"}
    doc["records"][0]["aliases"] = [alias, copy.deepcopy(alias)]
    leitura = ler(_bytes(doc))
    assert leitura.ok is False
    assert "ALIAS_DUPLICATE" in _erros(leitura)


def test_alias_igual_sob_mesma_authority_exige_revisao(doc):
    alias = {"scheme": "upstream", "value": "skill:abc",
             "authority": "lia-forge"}
    doc["records"][0]["aliases"] = [alias]
    primeiro = ler(_bytes(doc)).envelope.registros[0]
    conhecido = Conhecido(
        id=primeiro.id, revision_id=primeiro.revision_id,
        digest=primeiro.digest, name=primeiro.name,
        kind=primeiro.kind, version=primeiro.version,
        aliases=[alias],
    )
    outro = copy.deepcopy(doc)
    outro["records"][0]["id"] = "urn:lia:cap:11111111-2222-3333-4444-555555555555"
    outro["records"][0]["name"] = "Outra capacidade"
    registro_novo = ler(_bytes(outro)).envelope.registros[0]
    (classificado,) = classificar([registro_novo], [conhecido])
    assert classificado.classe is Classe.ALIAS_CANDIDATO
    assert classificado.admitido is False
    assert classificado.relacionados == [primeiro.id]


def test_alias_igual_de_autoridades_diferentes_nao_colide(doc):
    alias_a = {"scheme": "upstream", "value": "skill:abc",
               "authority": "lia-forge"}
    alias_b = {"scheme": "upstream", "value": "skill:abc",
               "authority": "lia-studio"}
    doc["records"][0]["aliases"] = [alias_a]
    conhecido = ler(_bytes(doc)).envelope.registros[0]
    outro = copy.deepcopy(doc)
    outro["records"][0]["id"] = "urn:lia:cap:11111111-2222-3333-4444-555555555555"
    outro["records"][0]["name"] = "Outra capacidade"
    outro["records"][0]["aliases"] = [alias_b]
    novo = ler(_bytes(outro)).envelope.registros[0]
    (classificado,) = classificar([novo], [
        Conhecido(id=conhecido.id, revision_id=conhecido.revision_id,
                  digest=conhecido.digest, aliases=[alias_a])
    ])
    assert classificado.classe is Classe.NOVO
    assert classificado.admitido is True


def test_duas_identidades_no_mesmo_lote_com_alias_igual_sao_retidas(doc):
    alias = {"scheme": "upstream", "value": "skill:abc",
             "authority": "lia-forge"}
    doc["records"][0]["aliases"] = [alias]
    outro = copy.deepcopy(doc["records"][0])
    outro["id"] = "urn:lia:cap:11111111-2222-3333-4444-555555555555"
    outro["revisionId"] = "rev-002"
    outro["name"] = "Outra capacidade"
    doc["records"].append(outro)
    leitura = ler(_bytes(doc))
    assert leitura.ok is True
    classificados = classificar(leitura.envelope.registros, [])
    assert [c.classe for c in classificados] == [
        Classe.ALIAS_CANDIDATO, Classe.ALIAS_CANDIDATO]
    assert all(not c.admitido for c in classificados)
