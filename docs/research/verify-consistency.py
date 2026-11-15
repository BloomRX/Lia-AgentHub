#!/usr/bin/env python3
"""
Verificação de consistência Unicode da documentação do Lia Agent Hub.

Não é código de produto: não importa nada do projeto, não escreve arquivo,
não toca a biblioteca. Lê apenas os documentos e verifica asserções.

Uso:  python3 docs/research/verify-consistency.py
Saída: uma linha por asserção, PASS/FAIL, e o total. Exit 1 se houver FAIL.
"""
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

REV = (ROOT / "docs/research/PHASE-0-1-CONSISTENCY-REVIEW.md").read_text(encoding="utf-8")
SEC = (ROOT / "docs/architecture/SECURITY-AND-TRUST-MODEL.md").read_text(encoding="utf-8")
REG = (ROOT / "docs/DECISION-REGISTER.md").read_text(encoding="utf-8")
REL = (ROOT / "docs/research/PHASE-0-1-1-FINAL-CONSISTENCY-FIXES.md").read_text(encoding="utf-8")

checks = []


def check(name, condition):
    checks.append((name, bool(condition)))


def row(text, codepoint):
    """Linha da tabela cuja primeira célula contém o codepoint dado.

    Aceita formas como `U+200C` e `U+202A`–`U+202E` (com backtick no meio).
    """
    needle = codepoint.split("`")[0]
    for line in text.splitlines():
        if not line.startswith("| `U+"):
            continue
        first = line.split("|")[1]
        if needle in first:
            return line
    return ""


def section(text, start_marker, end_marker):
    return text[text.index(start_marker):text.index(end_marker)]


# ---- 1. Tabela normativa das faixas bidi (fonte única) --------------------
check("SEC 3.2.2.1 tabela normativa existe", "#### 3.2.2.1 Tabela normativa" in SEC)

norm = section(SEC, "#### 3.2.2.1", "#### 3.2.3")
def bidi_categories(line):
    """Extrai (prosa, codigo, identificador) de uma linha de categoria bidi.

    Aceita células com texto descritivo: '**B** — sinalizar' -> 'B'.
    """
    cells = [c.strip() for c in line.split("|")[3:-1]]  # últimas 3 colunas: categoria
    out = []
    for cell in cells:
        m = re.match(r"\*\*([A-D])\*\*", cell)
        out.append(m.group(1) if m else "?")
    return tuple(out)


check("SEC norm U+202A-U+202E = B/A/A",
      bidi_categories(row(norm, "U+202A")) == ("B", "A", "A"))
check("SEC norm U+2066-U+2069 = B/A/A",
      bidi_categories(row(norm, "U+2066")) == ("B", "A", "A"))

# ---- 2. Catálogo por codepoint da segurança -------------------------------
cat = section(SEC, "#### 3.2.2 Catálogo", "#### 3.2.2.1")
check("SEC cat U+202A-U+202E prosa = B", "**B**" in row(cat, "U+202A`–`U+202E"))
check("SEC cat U+2066-U+2069 prosa = B", "**B**" in row(cat, "U+2066`–`U+2069"))

# ---- 3. ZWNJ e ZWJ = D em TODAS as fontes (Fase 0.1.2) --------------------
check("SEC cat U+200C = D", "**D**" in row(cat, "U+200C"))
check("SEC cat U+200D = D", "**D**" in row(cat, "U+200D"))

rev_cat = section(REV, "#### 3.2.3 Os caracteres", "#### 3.2.4 A política")
check("REV 3.2.3 U+200C = ESCAPAR (D)", "**ESCAPAR**" in row(rev_cat, "U+200C"))
check("REV 3.2.3 U+200D = ESCAPAR (D)", "**ESCAPAR**" in row(rev_cat, "U+200D"))

rel_cat = section(REL, "### 3.4 Tabela Unicode reconciliada", "### 3.5")
check("REL 3.4 U+200C = D", "**D**" in row(rel_cat, "U+200C"))
check("REL 3.4 U+200D = D", "**D**" in row(rel_cat, "U+200D"))

check("D-26 registra ZWNJ/ZWJ como D, nao C",
      "ZWNJ e ZWJ são `D`, não `C`" in section(REG, "### D-26", "### D-27"))

# ---- 4. Referência cruzada das condições de uso ---------------------------
check("REV U+200C aponta UTS #39 3.1.1 (nao 3.2.5)", "UTS #39 §3.1.1" in row(rev_cat, "U+200C"))
check("REV U+200D aponta UTS #39 3.1.1 (nao 3.2.5)", "UTS #39 §3.1.1" in row(rev_cat, "U+200D"))
check("REV nao remete mais a 3.2.5 para ZWNJ/ZWJ",
      "§3.2.5" not in row(rev_cat, "U+200C") and "§3.2.5" not in row(rev_cat, "U+200D"))

# ---- 5. Tabela de contexto: C e D separados ------------------------------
ctx = section(REV, "Regra de contexto", "Fonte única da verdade")
prosa = next(l for l in ctx.splitlines() if l.startswith("| **Prosa**"))
check("REV 3.2.4 prosa classifica U+202A-U+202E em B",
      prosa.index("U+202A") < prosa.index("**C**"))
check("REV 3.2.4 prosa classifica U+2066-U+2069 em B",
      prosa.index("U+2066") < prosa.index("**C**"))
check("REV 3.2.4 C e D separados (sem ambiguidade C/D)", "**C/D**" not in ctx)

codigo = next(l for l in ctx.splitlines() if l.startswith("| **Bloco de código**"))
check("REV 3.2.4 codigo U+202A-U+202E = A", "A (rejeitar)" in codigo and "U+202A–202E" in codigo)
check("REV 3.2.4 codigo U+2066-U+2069 = A", "A (rejeitar)" in codigo and "U+2066–2069" in codigo)

# ---- 6. D-26: regras explicitas -----------------------------------------
d26 = section(REG, "### D-26", "### D-27")
check("D-26 regra U+202A-U+202E explicita",
      "`U+202A–202E` → **B** em prosa, **A** em código, **A** em identificador" in d26)
check("D-26 regra U+2066-U+2069 explicita",
      "`U+2066–2069` → **B** em prosa, **A** em código, **A** em identificador" in d26)
check("D-26 analise por regiao", "por região" in d26)

# ---- 7. Pendencias de fonte oficial -------------------------------------
check("D-26 cita PropList.txt e DerivedCoreProperties.txt",
      "PropList.txt" in d26 and "DerivedCoreProperties.txt" in d26)
check("D-26 exige fixar a versao do Unicode",
      "versão do Unicode precisa ser fixada" in d26)

# ---- 8. D-17 e D-27 nao se confundem -----------------------------------
check("D-17 = sistemas operacionais", "### D-17 — Sistemas operacionais" in REG)
check("D-27 = biblioteca de interface", "### D-27 — Biblioteca de interface" in REG)

# ---- 9. Nenhuma decisao aprovada ---------------------------------------
estados = re.findall(r"\| \*\*Estado\*\* \| `([A-Z]+)`", REG)
check("0 decisoes APPROVED", estados.count("APPROVED") == 0)
check("D-01, D-05, D-16, D-18 continuam OPEN",
      all(f"### {d} —" in REG for d in ("D-01", "D-05", "D-16", "D-18")))

# ---- 10. LICENSE ausente ------------------------------------------------
check("LICENSE ausente", not (ROOT / "LICENSE").exists())

# ---- saida --------------------------------------------------------------
failed = [n for n, ok in checks if not ok]
for name, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
print(f"\n{len(checks) - len(failed)}/{len(checks)} PASS")
sys.exit(1 if failed else 0)
