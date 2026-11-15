"""Risco — regra transparente, sem julgamento automático (D-18)."""
from lia_agenthub.domain.model import Capability, ResourceType, Trust
from lia_agenthub.domain.risk import Risk, assess


def cap(**kw):
    base = dict(id="x-00000000", name="x", version="1.0.0")
    base.update(kw)
    return Capability(**base)


def test_capacidade_nua_nao_e_declarada_segura():
    r = assess(cap())
    assert r.level.value in {"medium", "high", "unknown"}
    assert r.disclaimer
    assert "não é aprovação" in r.disclaimer.lower() or "nao" in r.disclaimer.lower()


def test_fatores_observados_sao_listados():
    r = assess(cap(contains_scripts=True))
    assert any("script" in f.code.lower() or "script" in f.description.lower()
               for f in r.factors)


def test_mais_fatores_aumenta_o_nivel():
    simples = assess(cap())
    composta = assess(cap(contains_scripts=True, egress=["api.exemplo.com"],
                          secrets_env_vars=["CHAVE"], declared_permissions=["filesystem"]))
    ordem = ["low", "medium", "high"]
    assert ordem.index(composta.level.value) >= ordem.index(simples.level.value)


def test_o_que_nao_foi_avaliado_esta_explicito():
    r = assess(cap())
    assert len(r.not_evaluated) >= 4
    texto = " ".join(r.not_evaluated).lower()
    assert "script" in texto
    assert "prosa" in texto or "conteúdo" in texto


def test_risco_nunca_afirma_aprovacao():
    """O texto pode dizer "não é aprovação"; o que não pode é afirmar aprovação."""
    r = assess(cap(contains_scripts=True, egress=["x"], secrets_env_vars=["y"]))
    d = r.as_dict()
    assert d["level"] in {x.value for x in Risk}
    assert "signed" not in d
    assert "approved" not in d["level"]
    # nenhum fator declara o recurso seguro
    for f in d["factors"]:
        assert "é seguro" not in f["description"].lower()
        assert "is safe" not in f["description"].lower()


def test_confianca_primeira_parte_nao_zera_risco():
    """Confiança declarada muda o aviso, não a avaliação técnica."""
    r_unrev = assess(cap(contains_scripts=True, trust=Trust.UNREVIEWED))
    r_first = assess(cap(contains_scripts=True, trust=Trust.FIRST_PARTY))
    assert r_first.level.value == r_unrev.level.value


def test_tipo_desconhecido_entra_como_fator():
    r = assess(cap(type=ResourceType.UNKNOWN))
    assert any("tipo" in f.code.lower() or "tipo" in f.description.lower()
               for f in r.factors)


def test_licenca_desconhecida_entra_como_fator():
    r = assess(cap())
    assert any("licen" in f.code.lower() or "licença" in f.description.lower()
               for f in r.factors)
