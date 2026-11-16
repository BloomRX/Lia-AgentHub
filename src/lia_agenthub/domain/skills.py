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
    # Um nível de aninhamento é preservado, achatado em `pai.filho`.
    #
    # Antes, linhas indentadas eram descartadas e o pai ficava com valor
    # VAZIO: `metadata:` virava `""`. Não era "ignorar de propósito" — era
    # CORROMPER. E não é caso de borda: 9 dos 53 SKILL.md reais do acervo
    # escrevem `metadata:` com `author:` e `version:` indentados, então esses
    # dois campos se perdiam em silêncio.
    #
    # Continua sem PyYAML: só o recorte que o formato usa (um nível,
    # `chave: valor`). Aninhamento mais profundo continua fora, e continua
    # virando valor textual em vez de erro.
    # Valor em bloco YAML (`description: >-` seguido de linhas indentadas).
    #
    # Medido no acervo oficial do Google Stitch: 8 das 16 SKILL.md escrevem a
    # descrição assim. Antes o parser guardava o INDICADOR (`>-`) como valor e
    # descartava o texto — o catálogo registrava `description: ">-"`, que não
    # descreve nada. Agora as linhas indentadas são dobradas no valor.
    #
    # `>` dobra quebras em espaço, `|` preserva. O modificador `-` remove a
    # quebra final. É o subconjunto que o formato Agent Skills usa; YAML
    # completo continua fora, e continua sem dependência.
    pai: str | None = None
    chave_em_bloco: str | None = None
    linhas_em_bloco: list[str] = []

    def _fechar_bloco() -> None:
        nonlocal chave_em_bloco, linhas_em_bloco
        if chave_em_bloco is None:
            return
        separador = "\n" if fm.get("__estilo__" + chave_em_bloco) == "literal" else " "
        fm[chave_em_bloco] = separador.join(linhas_em_bloco).strip()
        fm.pop("__estilo__" + chave_em_bloco, None)
        chave_em_bloco, linhas_em_bloco = None, []

    for line in raw.splitlines():
        bruto = line.rstrip()
        if not bruto.strip() or bruto.lstrip().startswith("#"):
            continue
        indentado = bruto.startswith((" ", "\t"))
        linha = bruto.strip()
        if indentado:
            if chave_em_bloco is not None:
                linhas_em_bloco.append(linha)
                continue
        if ":" not in linha:
            continue
        key, _, value = linha.partition(":")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        # Abre um bloco? `>` ou `|`, com modificadores opcionais.
        if not indentado and value[:1] in (">", "|"):
            _fechar_bloco()
            chave_em_bloco = key
            linhas_em_bloco = []
            fm["__estilo__" + key] = "literal" if value.startswith("|") else "folded"
            continue
        if not indentado:
            _fechar_bloco()
        if indentado:
            if pai is None:
                continue                      # indentado sem pai: ignora
            chave = f"{pai}.{key}"
            # O pai só tinha cabeçalho (`metadata:`). Mantemos o mapa
            # achatado e também o cabeçalho vazio, para quem lê o formato
            # bruto saber que existe.
            fm[chave] = value
            continue
        fm[key] = value
        pai = key if value == "" else None

    _fechar_bloco()

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

    # Só chaves de NÍVEL DE CIMA contam para "campo desconhecido". Subchave
    # aninhada (`metadata.author`) é campo do pai, não do frontmatter — sem
    # isto o parser achatado faria todo `metadata:` aninhado do acervo real
    # emitir dois avisos falsos por Skill.
    de_topo = {k for k in fm if "." not in k}
    unknown = de_topo - KNOWN_FIELDS
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
        # Nome com namespace (`plugin::skill`) é formato de mercado, não erro.
        #
        # Medido: 8 das 16 Skills oficiais do google-labs-code/stitch-skills
        # usam `stitch::<skill>` no frontmatter. A regra anterior recusava
        # todas as 8 como NAME_FORMAT — ou seja, o Hub rejeitava Skills
        # oficiais do Google por usarem a convenção do próprio ecossistema.
        #
        # A regra não afrouxa: CADA parte precisa ser válida isoladamente.
        # `stitch::react-components` passa; `Stitch::x`, `a::B` e `a:::b`
        # continuam erro. Namespace não é desculpa para aceitar nome ruim.
        partes = name.split("::")
        nome_local = partes[-1]
        if not all(NAME_RE.match(parte) for parte in partes):
            issues.append(Issue(Severity.ERROR, "NAME_FORMAT",
                                "`name` deve ser minúsculo, com hífens simples "
                                "(ex.: `minha-skill`), sem hífen duplo nem hífen nas pontas. "
                                "Namespace `plugin::skill` é aceito desde que cada parte "
                                "obedeça à mesma regra.",
                                "name"))
        elif len(partes) > 1:
            issues.append(Issue(Severity.INFO, "NAME_NAMESPACED",
                                f"`name` usa namespace (`{name}`). O Hub indexa pelo "
                                f"nome local `{nome_local}` e preserva o namespace "
                                f"no metadado — ele identifica o plugin de origem.",
                                "name"))
        # A pasta é comparada com o nome LOCAL: `stitch::react-components`
        # vive em `.../skills/react-components/`, não em
        # `.../skills/stitch::react-components/`.
        if folder_name and nome_local != folder_name:
            issues.append(Issue(Severity.WARNING, "NAME_FOLDER_MISMATCH",
                                f"`name` é `{nome_local}` mas a pasta é `{folder_name}`. A "
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


#: Referências a arquivos no corpo: links Markdown relativos e caminhos
#: citados em código.
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_CODE_PATH_RE = re.compile(r"`([\w./-]+\.(?:md|py|js|ts|json|ya?ml|txt|sh|csv|toml))`")

#: Trecho em crase que "parece caminho". Usado só para LINT de prosa — nunca
#: para decidir se um pacote é aceito.
_CODE_PATH_AMPLO_RE = re.compile(r"`((?:[A-Za-z]:)?[^`\s:]*[\\/][^`\s]*)`")

#: Esquemas de URL que aparecem em prosa técnica e não são arquivo.
_URL_PREFIXOS = ("http://", "https://", "mailto:", "ftp://", "ws://", "wss://",
                 "file://", "chrome://", "devtools://")

#: Prefixo UNC (`\\servidor\share`).
_UNC_RE = re.compile(r"^[/\\]{2}")


def _parece_url_ou_rota(alvo: str) -> bool:
    """`/json/list`, `/`, `/api/v1/x` — rota de servidor citada em prosa.

    Rota tem segmentos sem extensão e começa com barra. Caminho de arquivo
    absoluto que importa para segurança é `C:\...` ou UNC, tratados à parte.
    """
    if not alvo.startswith(("/", "\\")):
        return False
    if _UNC_RE.match(alvo):
        return False                       # UNC é caminho de rede, não rota
    ultimo = alvo.rstrip("/").rsplit("/", 1)[-1]
    return "." not in ultimo or ultimo.startswith(".")


def _referencias_brutas(text: str) -> list[str]:
    """Toda referência plausível, antes de qualquer classificação."""
    achados: list[str] = []
    for padrao in (_MD_LINK_RE, _CODE_PATH_RE, _CODE_PATH_AMPLO_RE):
        for bruto in padrao.findall(text):
            alvo = bruto.strip()
            if not alvo or alvo.startswith(("#", "<")):
                continue
            if alvo.lower().startswith(_URL_PREFIXOS):
                continue
            alvo = alvo.split("#", 1)[0].rstrip(".,;:")
            if alvo:
                achados.append(alvo)
    return achados


def _dedup(itens: list[str]) -> list[str]:
    vistos, saida = set(), []
    for a in itens:
        if a not in vistos:
            vistos.add(a)
            saida.append(a)
    return saida


def referenced_files(text: str) -> list[str]:
    """Caminhos relativos citados no corpo que podem ser conferidos no payload.

    Exclui URL, âncora, rota de servidor (`/json/list`), caminho absoluto e
    fuga (`..`). O que fica são candidatos a arquivo DESTE recurso.
    """
    return _dedup([
        a for a in _referencias_brutas(text)
        if not a.startswith("..")
        and not _parece_url_ou_rota(a)
        and not re.match(r"^[A-Za-z]:[\\/]", a)
    ])


def escaping_references(text: str) -> list[str]:
    """Caminhos que apontam para FORA do payload (`..` além da raiz, drive, UNC).

    ESTE é o sinal de segurança. Não inclui rota HTTP: `/json/list` é endpoint,
    não tentativa de escape.
    """
    saida = []
    for a in _referencias_brutas(text):
        if a.startswith("..") or _UNC_RE.match(a) or re.match(r"^[A-Za-z]:[\\/]", a):
            saida.append(a)
    return _dedup(saida)


def cross_skill_reference(alvo: str) -> str | None:
    """Extrai o nome da Skill citada, se o alvo apontar para outra Skill.

    Reconhece a convenção real do acervo: `.agents/skills/<nome>/SKILL.md`
    (e variações com 1–3 segmentos antes de `skills/`). É o caso dominante —
    uma Skill citando outra do mesmo monorepo. Não é "arquivo ausente".
    """
    partes = alvo.replace("\\", "/").split("/")
    for i, parte in enumerate(partes[:-1]):
        if parte.lower() == "skills" and i + 1 < len(partes):
            return partes[i + 1]
    # Forma curta: `<nome>/SKILL.md`
    if len(partes) == 2 and partes[-1].lower() == "skill.md":
        return partes[0]
    return None


def check_references(text: str, available: set[str] | frozenset[str],
                     *, folder_name: str | None = None) -> list[Issue]:
    """Lint de referências do corpo. NUNCA recusa um recurso.

    Decisão de projeto, tomada depois de medir: esta função roda sobre os 48
    `SKILL.md` reais do acervo, e tratá-la como gate de segurança bloqueou 16
    de 53 Skills (33%) que importavam corretamente — entre elas Skills de
    operação que citam `/json/list` (endpoint CDP) e Skills de monorepo que
    citam `../../../docs/...` de propósito.

    Referência é TEXTO: descreve intenção do autor, não é caminho que o Hub
    vá abrir. A segurança real de caminho acontece onde arquivos são lidos e
    escritos (`domain/paths.py`, `adapters/safe_extract.py`), e continua
    intacta. Por isso aqui tudo é AVISO ou INFO — o pior veredito possível é
    "vale conferir", jamais "não pode importar".

    Códigos:
      * `REFERENCE_CROSS_SKILL` (info) — cita outra Skill. Normal em monorepo.
      * `REFERENCE_ESCAPE` (warning) — `..`/drive/UNC: portabilidade, não ataque.
      * `REFERENCE_MISSING` (warning) — citado e não encontrado no payload.
      * `REFERENCE_EXTERNAL` (info) — rota/endpoint, não é arquivo.
    """
    issues: list[Issue] = []
    normalizados = {a.replace("\\", "/").lstrip("./").rstrip("/").lower()
                    for a in available}
    raiz = (folder_name or "").lower()

    for alvo in escaping_references(text):
        issues.append(Issue(
            Severity.WARNING, "REFERENCE_ESCAPE",
            f"O corpo cita `{alvo}`, que aponta para fora do payload. Se o "
            f"recurso for importado sozinho, esse alvo não virá junto. "
            f"Documente a dependência ou traga o arquivo para o payload.", alvo))

    for alvo in referenced_files(text):
        chave = alvo.replace("\\", "/").lstrip("./").rstrip("/").lower()
        if chave in normalizados:
            continue
        outra = cross_skill_reference(alvo)
        if outra and outra.lower() != raiz:
            issues.append(Issue(
                Severity.INFO, "REFERENCE_CROSS_SKILL",
                f"O corpo cita `{alvo}`, da Skill `{outra}`. Funciona para quem "
                f"tem ambas; quem importar só esta não terá o arquivo.", alvo))
            continue
        if folder_name and chave.split("/")[0] == raiz:
            # `minha-skill/x.md` dentro do payload de `minha-skill`
            chave = "/".join(chave.split("/")[1:])
            if chave in normalizados:
                continue
        issues.append(Issue(
            Severity.WARNING, "REFERENCE_MISSING",
            f"O corpo cita `{alvo}`, que não está no recurso. Se for arquivo "
            f"de apoio, importe-o junto ou ajuste o texto.", alvo))
    return issues


def rotas_citadas(text: str) -> list[str]:
    """Rotas/endpoints citados em prosa (`/json/list`). Informação, não issue."""
    return _dedup([a for a in _referencias_brutas(text) if _parece_url_ou_rota(a)])


def has_blocking(issues: list[Issue]) -> bool:
    return any(i.severity is Severity.ERROR for i in issues)


def summarize(issues: list[Issue]) -> dict[str, int]:
    out = {s.value: 0 for s in Severity}
    for i in issues:
        out[i.severity.value] += 1
    return out


def folder_name_do_recurso(upstream: str | None,
                           files: list[str] | set[str] | None = None) -> str | None:
    """Nome da pasta do recurso, para a checagem `name` vs pasta.

    Semântica (antes implícita e errada):

    * A pasta é a do DIRETÓRIO que o usuário apontou na importação
      (`.../minha-skill` → `minha-skill`). É o que ele vê no explorador.
    * NÃO é o primeiro segmento de um caminho interno do payload. Antes, um
      recurso flat com `docs/guia.md` era comparado contra a pasta `docs` —
      e recurso sem subpasta virava `None`, então a checagem nunca rodava.
    * `None` quando não existe pasta declarada: ZIP, `.lia-capability`,
      arquivo solto, ou um `upstream` que é RÓTULO e não caminho
      (`probe`, `BloomRX/Lia-Studio@abc:...`). Inventar seria mentir.

    `upstream` é a origem registrada na importação. `files` é aceito por
    compatibilidade de assinatura e não é mais usado para derivar a pasta.
    """
    if not upstream:
        return None
    from pathlib import PurePosixPath, PureWindowsPath

    bruto = str(upstream).strip()
    if not bruto:
        return None
    # `repo@commit:caminho` é uma REFERÊNCIA, não um caminho local. Pegar o
    # último segmento de `BloomRX/Lia-Studio@abc:.agents/skills/x` daria `x`,
    # que é plausível mas não é a pasta que o usuário apontou.
    if "@" in bruto and ":" in bruto.split("@", 1)[1]:
        bruto = bruto.split(":", 1)[1] if ":" in bruto else bruto
    tem_separador = ("/" in bruto) or ("\\" in bruto)
    if not tem_separador:
        return None                     # rótulo, não caminho
    p = PureWindowsPath(bruto) if "\\" in bruto or ":" in bruto else PurePosixPath(bruto)
    if not p.name:
        return None
    if p.suffix.lower() in (".zip", ".lia-capability"):
        return None
    return p.name if p.suffix == "" else None
