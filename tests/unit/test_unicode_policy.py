"""Política Unicode — as categorias são o contrato da SECURITY §3.2.2.1."""
import pytest

from lia_agenthub.domain.unicode_policy import Context, scan


def cats(text, ctx=Context.PROSE):
    return [f.category for f in scan(text, context=ctx).findings]


def test_texto_limpo_nao_gera_achado():
    res = scan("Um texto normal, sem nada invisível.", context=Context.PROSE)
    assert res.findings == []
    assert not res.blocks_import


@pytest.mark.parametrize("char,esperado", [
    ("\u202e", "B"),   # RLO em prosa: ambíguo, não bloqueia
    ("\u202d", "B"),
    ("\u2066", "B"),   # LRI
    ("\u2069", "B"),
    ("\u200b", "B"),   # ZWSP
    ("\u2060", "B"),   # word joiner
])
def test_controles_em_prosa_sao_b_nao_bloqueiam(char, esperado):
    res = scan(f"antes{char}depois", context=Context.PROSE)
    assert cats(f"antes{char}depois") == [esperado]
    assert not res.blocks_import


@pytest.mark.parametrize("char", ["\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
                                  "\u2066", "\u2067", "\u2068", "\u2069"])
def test_bidi_em_codigo_e_A_e_bloqueia(char):
    texto = f"```\nvalor = 'x{char}y'\n```\n"
    res = scan(texto, context=Context.PROSE)
    assert "A" in [f.category for f in res.findings]
    assert res.blocks_import


@pytest.mark.parametrize("char", ["\u200e", "\u200f", "\u061c",
                                  "\ufff9", "\ufffa", "\ufffb"])
def test_marcacao_de_codigo_e_A(char):
    res = scan(f"```\na{char}b\n```\n", context=Context.PROSE)
    assert any(f.category == "A" for f in res.findings)


def test_zwj_zwnj_em_prosa_e_D_e_nao_bloqueia():
    res = scan("ک\u200cتاب", context=Context.PROSE)   # persa: ZWNJ legítimo
    assert [f.category for f in res.findings] == ["D"]
    assert not res.blocks_import


def test_zwj_zwnj_em_codigo_e_B():
    res = scan("```\nx = 'a\u200db'\n```\n", context=Context.PROSE)
    assert "B" in [f.category for f in res.findings]
    assert not res.blocks_import


def test_bom_no_inicio_nao_e_o_byte_zero():
    res = scan("\ufeffOlá", context=Context.PROSE)
    assert not res.blocks_import


def test_tags_fora_das_tres_bandeiras_rgi_sao_A():
    # U+E0076 é 'v' em tag; sozinho não forma bandeira RGI
    res = scan("```\n" + chr(0xE0076) + "\n```\n", context=Context.PROSE)
    assert any(f.category == "A" for f in res.findings)


def test_bandeira_rgi_legitima_nao_bloqueia():
    # gbeng = 🏴 + E0067 E0062 E0065 E006E E0067 + E007F (Inglaterra)
    bandeira = ("\U0001F3F4"
                "\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067"
                "\U000E007F")
    res = scan(f"Vamos torcer pela Inglaterra {bandeira}", context=Context.PROSE)
    assert not res.blocks_import


def test_identificador_com_espaco_invisivel_e_A():
    res = scan("nome\u200bmalicioso", context=Context.IDENTIFIER)
    assert any(f.category == "A" for f in res.findings)
    assert res.blocks_import


def test_findings_trazem_posicao_para_o_usuario_localizar():
    res = scan("abc\u202edef", context=Context.PROSE)
    f = res.findings[0]
    assert f.column == 4          # 1-based: o caractere está após "abc"
    assert f.escaped == "U+202E"
    assert f.name and f.excerpt


def test_nunca_apaga_caractere_do_conteudo():
    original = "antes\u202edepois"
    scan(original, context=Context.PROSE)
    assert original == "antes\u202edepois"   # scan é puro: não mutila a entrada


def test_tag_sem_ribbon_e_A_mesmo_com_as_letras_de_bandeira():
    """O ataque é justamente passar letras de tag sem a bandeira completa."""
    res = scan("```\n" + chr(0xE0067) + chr(0xE0062) + "\n```\n", context=Context.PROSE)
    assert res.blocks_import


def test_as_dict_expoe_os_campos_que_a_ui_usa():
    d = scan("abc\u202edef", context=Context.PROSE).findings[0].as_dict()
    for key in ("codepoint", "name", "category", "context", "line", "column", "excerpt"):
        assert key in d, key
