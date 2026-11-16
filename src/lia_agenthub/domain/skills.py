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


#: Referências a arquivos no corpo: links Markdown relativos e caminhos citados
#: em código. Só o que aponta para DENTRO do recurso — URL e âncora ficam fora.
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_CODE_PATH_RE = re.compile(r"`([\w./-]+\.(?:md|py|js|ts|json|ya?ml|txt|sh|csv|toml))`")


#: Referências que tentam sair do recurso. Detectadas separadamente para
#: poderem ser REPORTADAS como problema em vez de sumirem no filtro.
_ESCAPE_RE = re.compile(r"^(?:[a-zA-Z]:[\\/]|[/\\]{2}|[/\\])")


def referenced_files(text: str) -> list[str]:
    """Caminhos relativos citados no corpo. Ignora URL, âncora e absoluto."""
    vistos, saida = set(), []
    for alvo in _referencias_brutas(text):
        if alvo.startswith(("..", "/", "\\")) or _ESCAPE_RE.match(alvo):
            continue
        if alvo not in vistos:
            vistos.add(alvo)
            saida.append(alvo)
    return saida


def escaping_references(text: str) -> list[str]:
    """Referências que apontariam para FORA do recurso (`..` ou absoluto).

    Existem à parte porque `referenced_files` as descarta de propósito — e
    descartar sem registrar faria uma tentativa de fuga parecer "sem
    referências". Para validação isso é informação, não ruído.
    """
    vistos, saida = set(), []
    for alvo in _referencias_brutas(text):
        if not (alvo.startswith("..") or _ESCAPE_RE.match(alvo)):
            continue
        if alvo not in vistos:
            vistos.add(alvo)
            saida.append(alvo)
    return saida


#: Qualquer trecho em crase que pareça caminho, COM OU SEM extensão conhecida.
#: Necessário para pegar `C:/Windows/win.ini` e `C:/x.md`, que `_CODE_PATH_RE`
#: não vê porque não termina em extensão da lista. Fuga de fronteira precisa
#: ser detectada independentemente de a extensão ser "de conteúdo".
# Prefixo de drive opcional ANTES da classe que exclui `:` — senão
# `C:/x.md` nunca casaria, porque o `:` de `C:` cairia na exclusão.
_CODE_PathAmplo_RE = re.compile(r"`((?:[A-Za-z]:)?[^`\s:]*[\\/][^`\s]*)`")


def _referencias_brutas(text: str) -> list[str]:
    """Toda referência plausível, antes de qualquer filtro de segurança."""
    achados: list[str] = []
    for padrao in (_MD_LINK_RE, _CODE_PATH_RE, _CODE_PathAmplo_RE):
        for bruto in padrao.findall(text):
            alvo = bruto.strip()
            if not alvo or alvo.startswith(("#", "http://", "https://", "mailto:", "<")):
                continue
            alvo = alvo.split("#", 1)[0].rstrip(".,;:")
            if alvo:
                achados.append(alvo)
    return achados


def _normaliza_referencia(caminho: str) -> str:
    """Forma canônica para comparar referência com arquivo presente."""
    return caminho.replace("\\", "/").lstrip("./").rstrip("/").lower()


def check_references(text: str, available: set[str] | frozenset[str],
                     *, folder_name: str | None = None) -> list[Issue]:
    """Confere que cada arquivo citado existe no recurso.

    Este é o ÚNICO verificador de referências do projeto. Quem gera catálogo,
    quem valida e quem importa chamam esta função — duas implementações
    paralelas divergiriam, e foi exatamente o que aconteceu antes: o relatório
    de catálogo dizia "2 avisos" enquanto a verificação real encontrava 29
    Skills com referências ausentes.

    Distingue três situações, porque tratá-las igual esconde problemas:

    * `REFERENCE_MISSING` — o caminho não existe no recurso. Aviso.
    * `REFERENCE_CROSS_SKILL` — o caminho aponta para a pasta de OUTRA Skill
      (primeiro segmento é uma pasta de Skill conhecida, diferente desta).
      Não é erro: o autor citou deliberadamente algo externo. É aviso de
      portabilidade, porque quem importar só este recurso não terá o alvo.
    * `REFERENCE_INVALID` — o caminho escaparia do recurso (`..`, absoluto,
      drive). Não é "ausente": é tentativa de sair da fronteira. Erro.

    Referência quebrada NUNCA é `ERROR` (exceto fuga de fronteira): o autor
    pode ter citado arquivo que o host gera. Bloquear por isso recusaria
    Skills legítimas — e o produto promete não inventar reparos.
    """
    issues: list[Issue] = []
    normalizados = {_normaliza_referencia(a) for a in available}

    # Pastas que são uma outra SKILL — não basta ter subpasta. `docs/guia.md`
    # é conteúdo DESTA skill; `outra-skill/SKILL.md` é outra skill. O critério
    # é a pasta conter um SKILL.md próprio e não ser a raiz deste recurso.
    pastas_de_skill = {a.split("/")[0].lower() for a in available
                       if a.lower().endswith("/skill.md")}

    # Fugas de fronteira: reportadas, não silenciadas.
    for alvo in escaping_references(text):
        issues.append(Issue(
            Severity.ERROR, "REFERENCE_INVALID",
            f"O corpo cita `{alvo}`, que aponta para FORA do recurso. "
            f"Referências só podem apontar para dentro do próprio recurso.", alvo))

    for alvo in referenced_files(text):
        chave = _normaliza_referencia(alvo)
        if chave in normalizados:
            continue

        primeira = chave.split("/")[0]
        if primeira in pastas_de_skill and (folder_name is None
                                            or primeira != folder_name.lower()):
            issues.append(Issue(
                Severity.WARNING, "REFERENCE_CROSS_SKILL",
                f"O corpo cita `{alvo}`, que fica em outra Skill. Funciona para "
                f"quem tem as duas; quem importar só esta não terá o arquivo.", alvo))
            continue

        issues.append(Issue(
            Severity.WARNING, "REFERENCE_MISSING",
            f"O corpo cita `{alvo}`, que não está no recurso. Se for um arquivo "
            f"de apoio, ele precisa ser importado junto.", alvo))
    return issues


def has_blocking(issues: list[Issue]) -> bool:
    return any(i.severity is Severity.ERROR for i in issues)


def summarize(issues: list[Issue]) -> dict[str, int]:
    out = {s.value: 0 for s in Severity}
    for i in issues:
        out[i.severity.value] += 1
    return out


def folder_name_do_recurso(upstream: str | None, files: list[str] | set[str]) -> str | None:
    """Nome da pasta do recurso, para a checagem `name` vs pasta.

    Semântica (antes implícita e errada):

    * O nome da pasta é o do DIRETÓRIO que o usuário apontou na importação —
      `.../minha-skill` → `minha-skill`. É o que um humano vê no explorador.
    * NÃO é o primeiro segmento de um caminho interno do payload. Para um
      recurso `flat` (SKILL.md na raiz, mais `docs/guia.md`), o "primeiro
      segmento" é `docs` — uma subpasta de conteúdo, não a pasta do recurso.
      Era assim que `folder_name` virava `scripts` ou `docs` e a checagem
      de coerência passava a comparar nome com coisa errada.
    * Recurso que não veio de uma pasta (arquivo solto, ZIP) devolve `None`:
      não existe pasta para comparar, e inventar uma seria mentir.

    `upstream` é a origem registrada na importação. Quando ela é um diretório,
    a pasta é o próprio diretório. Quando é um arquivo, a pasta é o diretório
    que o contém — é o contexto que o usuário escolheu.
    """
    if not upstream:
        return None
    from pathlib import PurePosixPath, PureWindowsPath

    # `upstream` pode ser POSIX ou Windows; escolhe o parser pela forma.
    p = PureWindowsPath(upstream) if ("\\" in upstream or ":" in upstream) \
        else PurePosixPath(upstream)
    if not p.name:
        return None                      # terminou em separador: sem pasta
    if p.suffix.lower() in (".zip", ".lia-capability"):
        return None                      # arquivo compactado não tem pasta
    # Diretório apontado: o último segmento É a pasta do recurso.
    # Arquivo solto: tratamos o último segmento como nome do arquivo e
    # devolvemos None — não há pasta declarada a comparar.
    if any(f.lower().endswith("skill.md") for f in files) and \
            not any("/" in f for f in files):
        # Recurso flat: só faz sentido comparar se o upstream é a pasta.
        return p.name if p.suffix == "" else None
    return p.name if p.suffix == "" else None
