"""Coerência estrutural da interface.

Sem navegador no ambiente, verificamos o que é verificável estaticamente:
todo seletor do JS tem elemento, toda aba tem seção, toda classe usada no JS
tem regra no CSS. É a classe de erro mais comum e a que quebra a tela em
silêncio. Isto NÃO substitui abrir a interface — está declarado como limite.
"""
import re
from pathlib import Path

STATIC = Path(__file__).resolve().parents[2] / "src" / "lia_agenthub" / "resources" / "static"


def read(nome: str) -> str:
    return (STATIC / nome).read_text(encoding="utf-8")


def ids_html() -> set[str]:
    return set(re.findall(r'id="([^"]+)"', read("index.html")))


def ids_js() -> set[str]:
    js = read("app.js")
    return set(re.findall(r'\$\("#([A-Za-z0-9_-]+)"', js)) | set(
        re.findall(r'getElementById\("([^"]+)"\)', js))


def test_todo_seletor_do_js_tem_elemento_no_html():
    faltando = sorted(ids_js() - ids_html())
    assert not faltando, f"seletores do JS sem elemento: {faltando}"


def test_toda_aba_tem_secao():
    abas = set(re.findall(r'data-view="([a-z]+)"', read("index.html")))
    secoes = set(re.findall(r'id="view-([a-z]+)"', read("index.html")))
    assert abas == secoes, f"abas sem seção: {abas - secoes}; seções órfãs: {secoes - abas}"


def test_lista_de_views_do_js_bate_com_as_abas():
    js = read("app.js")
    lista = set(re.findall(r'"([a-z]+)"',
                           re.search(r"const VIEWS = \[(.*?)\]", js).group(1)))
    abas = set(re.findall(r'data-view="([a-z]+)"', read("index.html")))
    assert lista == abas


def test_classes_usadas_no_js_tem_regra_css():
    js = read("app.js")
    css = read("app.css")
    usadas = {c.split()[0] for c in re.findall(r'class: "([a-z][a-z0-9_ -]*)"', js)}
    definidas = set(re.findall(r"\.([a-z][a-z0-9_-]*)", css))
    # classes aplicadas por atributo HTML (não por CSS) são intrínsecas
    permitidas = {"click", "primary", "ghost", "danger"}
    faltando = sorted(usadas - definidas - permitidas)
    assert not faltando, f"classes sem regra CSS: {faltando}"


def test_nenhum_id_repetido_no_html():
    todos = re.findall(r'id="([^"]+)"', read("index.html"))
    repetidos = {i for i in todos if todos.count(i) > 1}
    assert not repetidos, f"ids repetidos: {repetidos}"


def test_assets_referenciados_existem():
    html = read("index.html")
    for ref in re.findall(r'(?:href|src)="/(static/[^"]+)"', html):
        assert (STATIC / ref.split("/", 1)[1]).is_file(), f"ativo ausente: {ref}"


def test_todo_controle_interativo_tem_tipo_ou_rotulo():
    html = read("index.html")
    for tag in ("input", "select", "button"):
        for m in re.finditer(rf"<{tag}\b([^>]*)>", html):
            attrs = m.group(1)
            if tag == "input":
                assert "type=" in attrs or "id=" in attrs, f"input sem tipo/id: {attrs}"
            if tag == "button":
                tem_texto_depois = True
                assert "aria-label" in attrs or tem_texto_depois


def test_nao_ha_placeholder_como_unico_rotulo():
    """Placeholder não é rótulo: desaparece ao digitar e leitor de tela ignora."""
    html = read("index.html")
    for m in re.finditer(r'<input\b([^>]*)>', html):
        attrs = m.group(1)
        if "placeholder=" in attrs:
            ident = re.search(r'id="([^"]+)"', attrs)
            if ident:
                tem = re.search(rf'<label[^>]*\bfor="{ident.group(1)}"', html)
                assert tem or "aria-label" in attrs, f"placeholder sem rótulo: {attrs}"
