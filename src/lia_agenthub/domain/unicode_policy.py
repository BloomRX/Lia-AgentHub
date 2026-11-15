"""Política Unicode — categorias A/B/C/D por contexto.

Fonte normativa: SECURITY-AND-TRUST-MODEL.md §3.2.2.1 (tabela normativa) e
DECISION-REGISTER.md D-26.

Regra central: a análise é POR REGIÃO, nunca por arquivo. Um U+202E legítimo
em prosa não condena um arquivo; o mesmo caractere em bloco de código condena.

Nada aqui altera bytes. Este módulo só CLASSIFICA. A gravação preserva o
conteúdo original exatamente como veio (§3.2.4: NFC para comparar, nunca
NFKC para gravar).
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from enum import Enum

# --------------------------------------------------------------------------
# Categorias — SECURITY §3.2.1
# --------------------------------------------------------------------------


class Category(str, Enum):
    """A = rejeitar · B = revisar · C = preservar · D = preservar e escapar."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"


class Context(str, Enum):
    """Onde o caractere aparece. Muda a categoria."""

    PROSE = "prose"
    CODE = "code"
    IDENTIFIER = "identifier"


# --------------------------------------------------------------------------
# Tabela normativa das duas faixas bidi — SECURITY §3.2.2.1
# --------------------------------------------------------------------------
# Chave: (inicio, fim) inclusive. Valor: categoria por contexto.
# FONTE ÚNICA: se este dict mudar, a documentação está errada, não ele.

BIDI_RANGES: dict[tuple[int, int], dict[Context, Category]] = {
    (0x202A, 0x202E): {  # LRE RLE PDF LRO RLO — overrides reordenam o texto
        Context.PROSE: Category.B,
        Context.CODE: Category.A,
        Context.IDENTIFIER: Category.A,
    },
    (0x2066, 0x2069): {  # LRI RLI FSI PDI — isolates, forma recomendada pelo UAX #9
        Context.PROSE: Category.B,
        Context.CODE: Category.A,
        Context.IDENTIFIER: Category.A,
    },
}

# Demais caracteres relevantes. Mesma estrutura, uma entrada por codepoint/faixa.
SINGLE_RANGES: dict[tuple[int, int], dict[Context, Category]] = {
    (0x200B, 0x200B): {  # ZERO WIDTH SPACE
        Context.PROSE: Category.B,
        Context.CODE: Category.B,
        Context.IDENTIFIER: Category.A,
    },
    (0x200C, 0x200C): {  # ZWNJ — D: preserva o byte, exibe escapado
        Context.PROSE: Category.D,
        Context.CODE: Category.B,
        Context.IDENTIFIER: Category.B,  # só nas condições A1/A2 (ver kanji_ok)
    },
    (0x200D, 0x200D): {  # ZWJ — D
        Context.PROSE: Category.D,
        Context.CODE: Category.B,
        Context.IDENTIFIER: Category.B,  # só na condição B
    },
    (0x200E, 0x200E): {  # LRM
        Context.PROSE: Category.B,
        Context.CODE: Category.A,
        Context.IDENTIFIER: Category.A,
    },
    (0x200F, 0x200F): {  # RLM
        Context.PROSE: Category.B,
        Context.CODE: Category.A,
        Context.IDENTIFIER: Category.A,
    },
    (0x061C, 0x061C): {  # ALM — ausente na lista da Fase 0
        Context.PROSE: Category.B,
        Context.CODE: Category.A,
        Context.IDENTIFIER: Category.A,
    },
    (0x2060, 0x2060): {  # WORD JOINER
        Context.PROSE: Category.B,
        Context.CODE: Category.B,
        Context.IDENTIFIER: Category.A,
    },
    (0x2061, 0x2064): {  # FUNCTION APPLICATION, INVISIBLE TIMES/SEPARATOR/PLUS
        Context.PROSE: Category.B,
        Context.CODE: Category.B,
        Context.IDENTIFIER: Category.A,
    },
    (0xFEFF, 0xFEFF): {  # BOM — tratado à parte no byte 0
        Context.PROSE: Category.A,
        Context.CODE: Category.A,
        Context.IDENTIFIER: Category.A,
    },
    (0x3164, 0x3164): {  # HANGUL FILLER
        Context.PROSE: Category.B,
        Context.CODE: Category.B,
        Context.IDENTIFIER: Category.A,
    },
    (0x115F, 0x1160): {  # HANGUL CHOSEONG / JUNGSEONG FILLER
        Context.PROSE: Category.B,
        Context.CODE: Category.B,
        Context.IDENTIFIER: Category.A,
    },
    (0x180E, 0x180E): {  # MONGOLIAN VOWEL SEPARATOR
        Context.PROSE: Category.B,
        Context.CODE: Category.B,
        Context.IDENTIFIER: Category.A,
    },
    (0xFFF9, 0xFFFB): {  # INTERLINEAR ANNOTATION
        Context.PROSE: Category.B,
        Context.CODE: Category.A,
        Context.IDENTIFIER: Category.A,
    },
    # Preservar sem aviso — C
    (0x00A0, 0x00A0): {
        Context.PROSE: Category.C,
        Context.CODE: Category.C,
        Context.IDENTIFIER: Category.A,
    },
    (0x00AD, 0x00AD): {  # SOFT HYPHEN — hifenização em pt-BR
        Context.PROSE: Category.C,
        Context.CODE: Category.C,
        Context.IDENTIFIER: Category.A,
    },
}

# --------------------------------------------------------------------------
# Bandeiras RGI — allowlist LITERAL (SECURITY §3.2.3)
# --------------------------------------------------------------------------
# O UTS #51 aceita QUALQUER tag de U+E0020 a U+E007E, então "sequência
# bem-formada" é backdoor. Só estas três strings exatas passam.

RIBBON = "\U0001F3F4"
CANCEL_TAG = "\U000E007F"
RGI_FLAGS: tuple[str, ...] = (
    RIBBON + "\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067" + CANCEL_TAG,  # gbeng
    RIBBON + "\U000E0067\U000E0062\U000E0073\U000E0063\U000E0074" + CANCEL_TAG,  # gbsct
    RIBBON + "\U000E0067\U000E0062\U000E0077\U000E006C\U000E0073" + CANCEL_TAG,  # gbwls
)

TAG_START, TAG_END = 0xE0000, 0xE007F


@dataclass(frozen=True)
class Finding:
    """Um achado. `excerpt` é a linha, já escapada para exibição."""

    codepoint: int
    name: str
    category: Category
    context: Context
    line: int
    column: int
    excerpt: str

    @property
    def escaped(self) -> str:
        return f"U+{self.codepoint:04X}"

    def as_dict(self) -> dict:
        return {
            "codepoint": self.escaped,
            "name": self.name,
            "category": self.category.value,
            "context": self.context.value,
            "line": self.line,
            "column": self.column,
            "excerpt": self.excerpt,
        }


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)

    @property
    def rejected(self) -> list[Finding]:
        return [f for f in self.findings if f.category is Category.A]

    @property
    def needs_review(self) -> list[Finding]:
        return [f for f in self.findings if f.category is Category.B]

    @property
    def invisible(self) -> list[Finding]:
        """Categoria D: o usuário PRECISA ver, então a UI escapa."""
        return [f for f in self.findings if f.category is Category.D]

    @property
    def blocks_import(self) -> bool:
        return bool(self.rejected)

    def counts(self) -> dict[str, int]:
        out = {c.value: 0 for c in Category}
        for f in self.findings:
            out[f.category.value] += 1
        return out


def _flag_spans(text: str) -> list[tuple[int, int]]:
    """Intervalos ocupados por bandeiras RGI válidas."""
    spans = []
    for flag in RGI_FLAGS:
        start = 0
        while True:
            i = text.find(flag, start)
            if i < 0:
                break
            spans.append((i, i + len(flag)))
            start = i + len(flag)
    return spans


def _in_spans(idx: int, spans: list[tuple[int, int]]) -> bool:
    return any(a <= idx < b for a, b in spans)


def _detect_regions(text: str) -> list[tuple[int, int, Context]]:
    """Divide o texto em regiões prosa/código pelas cercas ```.

    A análise é por região — rejeitar o arquivo inteiro por um caractere
    legítimo em prosa seria o erro que a Fase 0.1 corrigiu.
    """
    regions: list[tuple[int, int, Context]] = []
    pos = 0
    in_code = False
    for line in text.splitlines(keepends=True):
        is_fence = line.lstrip().startswith("```")
        if is_fence:
            regions.append((pos, pos + len(line), Context.PROSE))
            in_code = not in_code
        else:
            regions.append((pos, pos + len(line), Context.CODE if in_code else Context.PROSE))
        pos += len(line)
    if pos < len(text):
        regions.append((pos, len(text), Context.CODE if in_code else Context.PROSE))
    return regions


def _category_for(cp: int, ctx: Context) -> Category | None:
    for (lo, hi), table in {**BIDI_RANGES, **SINGLE_RANGES}.items():
        if lo <= cp <= hi:
            return table[ctx]
    return None


def scan(text: str, *, context: Context = Context.PROSE) -> ScanResult:
    """Classifica todos os caracteres invisíveis relevantes do texto.

    `context` é o padrão quando a região não é detectada automaticamente
    (uso típico: varrer um identificador isolado).
    """
    result = ScanResult()
    flags = _flag_spans(text)
    regions = _detect_regions(text) if context is Context.PROSE else []

    line_no, col_no, line_start = 1, 1, 0
    for idx, ch in enumerate(text):
        cp = ord(ch)
        if ch == "\n":
            line_no += 1
            col_no = 1
            line_start = idx + 1
            continue

        # Bandeiras RGI: preservadas, sem achado
        if TAG_START <= cp <= TAG_END and _in_spans(idx, flags):
            col_no += 1
            continue

        ctx = context
        if regions:
            for a, b, c in regions:
                if a <= idx < b:
                    ctx = c
                    break

        if TAG_START <= cp <= TAG_END:
            cat = Category.A
        elif cp == 0xFEFF and idx == 0:
            col_no += 1
            continue  # BOM no byte 0: normaliza no import, registrado à parte
        else:
            got = _category_for(cp, ctx)
            if got is None:
                col_no += 1
                continue
            cat = got

        if cat is Category.C:
            col_no += 1
            continue

        # Trecho da linha, com o caractere já escapado — nunca renderizado
        end = text.find("\n", line_start)
        raw_line = text[line_start: end if end >= 0 else len(text)]
        excerpt = raw_line.replace(ch, f"<U+{cp:04X}>")

        result.findings.append(
            Finding(
                codepoint=cp,
                name=unicodedata.name(ch, f"<U+{cp:04X}>"),
                category=cat,
                context=ctx,
                line=line_no,
                column=col_no,
                excerpt=excerpt.strip()[:200],
            )
        )
        col_no += 1

    return result


def has_bom(data: bytes) -> bool:
    return data.startswith(b"\xef\xbb\xbf")


def strip_bom(data: bytes) -> bytes:
    """Remove BOM do byte 0. Registrado no relatório de import, nunca silencioso."""
    return data[3:] if has_bom(data) else data
