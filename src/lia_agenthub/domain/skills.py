"""Validador estrutural de Agent Skills (SKILL.md).

Especificação: 6 campos de frontmatter (agentskills.io), conforme
INTEGRATION-CANDIDATES §2 e D-03.

Este módulo valida ESTRUTURA. Ele não julga se o texto é malicioso —
SECURITY §6: análise semântica de prosa tem confiabilidade nenhuma, e o
produto não pode afirmar o que não pode provar.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .model import Issue, Severity
from .unicode_policy import Context, scan

NAME_MAX = 64
DESCRIPTION_MAX = 1024
COMPATIBILITY_MAX = 500
BODY_HINT = 400  # recomendação, não regra

KNOWN_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
REQUIRED_FIELDS = {"name", "description"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass
class ParsedSkill:
    frontmatter: dict[str, str] = field(default_factory=dict)
    body: str = ""
    raw_frontmatter: str = ""
    ok: bool = False


def parse_frontmatter(text: str) -> ParsedSkill:
    """Parser deliberadamente simples — não YAML completo.

    O formato canônico é `chave: valor` por linha. Valores multilinha e
    estruturas aninhadas não são suportados; se aparecerem, viram Issue,
    não exceção. Um parser YAML completo seria dependência (PyYAML) para
    um caso que a spec não exige.
    """
    if not text.startswith("---"):
        return ParsedSkill(ok=False, body=text)

    end = text.find("\n---", 3)
    if end < 0:
        return ParsedSkill(ok=False, body=text)

    raw = text[4:end] if text.startswith("---\n") else text[3:end]
    body = text[end + 4:]

    fm: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            continue  # aninhamento: ignorado de propósito
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip('"').strip("'")

    return ParsedSkill(frontmatter=fm, body=body, raw_frontmatter=raw, ok=True)


def validate_skill(text: str, *, folder_name: str | None = None) -> list[Issue]:
    """Valida um SKILL.md. Retorna issues ordenadas por severidade."""
    issues: list[Issue] = []
    parsed = parse_frontmatter(text)

    if "\ufeff" in text[:1]:
        issues.append(Issue(Severity.WARNING, "BOM_PRESENT",
                            "Arquivo começa com BOM (U+FEFF). O BOM quebra o parser de "
                            "frontmatter em alguns leitores e será removido na importação.",
                            "byte 0"))

    if not parsed.ok:
        issues.append(Issue(Severity.ERROR, "NO_FRONTMATTER",
                            "O arquivo não começa com bloco de frontmatter (`---` na "
                            "primeira linha). Sem frontmatter não é uma Agent Skill.",
                            "início do arquivo"))
        return issues

    fm = parsed.frontmatter

    missing = REQUIRED_FIELDS - fm.keys()
    for m in sorted(missing):
        issues.append(Issue(Severity.ERROR, "MISSING_FIELD",
                            f"Campo obrigatório ausente: `{m}`.", "frontmatter"))

    unknown = set(fm) - KNOWN_FIELDS
    for u in sorted(unknown):
        issues.append(Issue(Severity.WARNING, "UNKNOWN_FIELD",
                            f"Campo desconhecido no frontmatter: `{u}`. Clientes que "
                            f"seguem a especificação podem rejeitar o arquivo.",
                            "frontmatter"))

    name = fm.get("name", "")
    if name:
        if len(name) > NAME_MAX:
            issues.append(Issue(Severity.ERROR, "NAME_TOO_LONG",
                                f"`name` tem {len(name)} caracteres; o limite é {NAME_MAX}.",
                                "name"))
        if not NAME_RE.match(name):
            issues.append(Issue(Severity.ERROR, "NAME_FORMAT",
                                "`name` deve ser minúsculo, com hífens simples "
                                "(ex.: `minha-skill`), sem hífen duplo nem hífen nas pontas.",
                                "name"))
        if folder_name and name != folder_name:
            issues.append(Issue(Severity.WARNING, "NAME_FOLDER_MISMATCH",
                                f"`name` é `{name}` mas a pasta é `{folder_name}`. A "
                                f"especificação recomenda que sejam iguais.",
                                "name"))

    desc = fm.get("description", "")
    if desc and len(desc) > DESCRIPTION_MAX:
        issues.append(Issue(Severity.ERROR, "DESCRIPTION_TOO_LONG",
                            f"`description` tem {len(desc)} caracteres; o limite é "
                            f"{DESCRIPTION_MAX}.", "description"))

    compat = fm.get("compatibility", "")
    if compat and len(compat) > COMPATIBILITY_MAX:
        issues.append(Issue(Severity.WARNING, "COMPATIBILITY_TOO_LONG",
                            f"`compatibility` tem {len(compat)} caracteres; o recomendado "
                            f"é até {COMPATIBILITY_MAX}.", "compatibility"))

    if not parsed.body.strip():
        issues.append(Issue(Severity.WARNING, "EMPTY_BODY",
                            "O corpo da Skill está vazio. Sem instruções, a Skill não "
                            "faz nada quando o host a carrega.", "corpo"))

    # ---- Unicode: por região, nunca por arquivo inteiro ------------------
    result = scan(text, context=Context.PROSE)
    for f in result.rejected:
        issues.append(Issue(Severity.ERROR, "UNICODE_REJECT",
                            f"{f.escaped} ({f.name}) em {f.context.value}, linha "
                            f"{f.line}: {f.excerpt}", f"linha {f.line}"))
    for f in result.needs_review:
        issues.append(Issue(Severity.REVIEW, "UNICODE_REVIEW",
                            f"{f.escaped} ({f.name}) em {f.context.value}, linha "
                            f"{f.line}. Pode ser legítimo; exige revisão humana.",
                            f"linha {f.line}"))
    for f in result.invisible:
        issues.append(Issue(Severity.INFO, "UNICODE_INVISIBLE",
                            f"{f.escaped} ({f.name}) na linha {f.line}. Preservado; "
                            f"exibido escapado na revisão.", f"linha {f.line}"))

    if len(parsed.body) > 20000:
        issues.append(Issue(Severity.INFO, "BODY_LONG",
                            "O corpo tem mais de 20.000 caracteres. Skills longas "
                            "consomem contexto do host.", "corpo"))

    order = {Severity.ERROR: 0, Severity.REVIEW: 1, Severity.WARNING: 2, Severity.INFO: 3}
    return sorted(issues, key=lambda i: (order[i.severity], i.code))


def has_blocking(issues: list[Issue]) -> bool:
    return any(i.severity is Severity.ERROR for i in issues)


def summarize(issues: list[Issue]) -> dict[str, int]:
    out = {s.value: 0 for s in Severity}
    for i in issues:
        out[i.severity.value] += 1
    return out
