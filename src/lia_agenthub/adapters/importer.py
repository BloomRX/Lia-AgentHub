"""Pipeline de importação — 6 passos, nenhum efeito colateral antes da admissão.

SECURITY §8: nada é executado, nada é copiado para a biblioteca antes de
todas as verificações passarem.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import stat
from dataclasses import dataclass, field
from pathlib import Path

from ..domain.errors import ImportRejected, SecurityError
from ..domain.integrity import content_hashes, sha256_bytes, tree_hash
from ..domain.model import (
    Capability, License, LicenseStatus, ResourceType, Severity, Source, Trust,
    new_id, notice_obrigatorio,
)
from ..domain.mcp import DESCRITOR, MCPServer, DescritorInvalido, ler_descritor
from ..domain.paths import looks_like_script
from ..domain.skills import (
    check_references, folder_name_do_recurso, has_blocking, summarize,
    validate_skill,
)
from ..domain.unicode_policy import Context, has_bom, scan, strip_bom
from .repository import Repository
from .safe_extract import (
    Extraction, inspect_directory, inspect_package, inspect_zip, stat_import_path,
)

MANIFEST_NAME = "manifest.json"


@dataclass
class ImportReport:
    """O que se sabe, o que não se sabe, e o que exige humano."""

    ok: bool
    capability_id: str | None = None
    name: str = ""
    resource_type: str = ResourceType.UNKNOWN.value
    files: list[dict] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)
    unicode_findings: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    detected_license: str | None = None
    license_status: str = LicenseStatus.UNKNOWN.value
    requires_review: bool = False
    blocked_reason: str = ""
    hint: str = ""
    contains_scripts: bool = False
    hashes: dict[str, str] = field(default_factory=dict)
    staged_at: str | None = None
    already_present: bool = False

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "capabilityId": self.capability_id,
            "name": self.name,
            "resourceType": self.resource_type,
            "files": self.files,
            "issues": self.issues,
            "unicodeFindings": self.unicode_findings,
            "warnings": self.warnings,
            "detectedLicense": self.detected_license,
            "licenseStatus": self.license_status,
            "requiresReview": self.requires_review,
            "blockedReason": self.blocked_reason,
            "hint": self.hint,
            "containsScripts": self.contains_scripts,
            "hashes": self.hashes,
            "stagedAt": self.staged_at,
            "alreadyPresent": self.already_present,
            "note": (
                "Hashes verificam integridade, não autoria. Nenhum arquivo foi "
                "executado. Confiança é decisão humana."
            ),
        }


LICENSE_FILE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "LICENCE")


def _detect_license(files: dict[str, bytes]) -> tuple[str | None, str]:
    """Detecta PRESENÇA de licença. Não infere SPDX. Não presume permissão."""
    for rel, data in files.items():
        if "/" in rel:
            continue
        if rel.upper().split(".")[0] in ("LICENSE", "LICENCE", "COPYING"):
            head = data[:2048].decode("utf-8", "replace")
            for known, label in (
                ("MIT License", "MIT"),
                ("Apache License", "Apache-2.0"),
                ("GNU GENERAL PUBLIC LICENSE", "GPL"),
                ("GNU LESSER GENERAL PUBLIC LICENSE", "LGPL"),
                ("BSD 3-Clause", "BSD-3-Clause"),
                ("BSD 2-Clause", "BSD-2-Clause"),
                ("Mozilla Public License", "MPL"),
                ("Creative Commons", "CC (ver arquivo)"),
                ("The Unlicense", "Unlicense"),
            ):
                if known in head:
                    return label, LicenseStatus.DECLARED.value
            # Arquivo presente, texto não reconhecido: NÃO inventamos um código.
            return None, LicenseStatus.UNKNOWN.value
    return None, LicenseStatus.UNKNOWN.value


def _extra_do_registro(namespace: str, servidor: "MCPServer | None") -> dict:
    """Metadado de origem que vive fora do schema fixo do registro.

    `extra` é o mecanismo do Hub para campo que não é conhecido do modelo mas
    precisa sobreviver ao roundtrip: namespace do plugin e descritor MCP.
    Manter aqui evita inchar `Capability` com campo específico de um
    ecossistema e continua serializando no arquivo.
    """
    extra: dict = {}
    if namespace:
        extra["namespace"] = namespace
    if servidor is not None:
        extra["mcp"] = servidor.as_dict()
    return extra


def _detect_type(files: dict[str, bytes]) -> ResourceType:
    names = {p.lower() for p in files}
    if "skill.md" in names:
        return ResourceType.AGENT_SKILL
    if any(n.endswith("package.json") for n in names):
        return ResourceType.MCP_SERVER
    if any(n.endswith((".md", ".txt")) for n in names):
        return ResourceType.REFERENCE
    return ResourceType.UNKNOWN


def _resolve_version(manifest: dict | None, skill_text: bytes | None) -> str:
    """Versão declarada pelo próprio recurso, na ordem mais confiável.

    Manifesto de pacote vence (foi escrito pelo Hub). Depois o frontmatter da
    SKILL.md. Sem declaração, `0.1.0` — e `0.1.0` significa "não declarada",
    não "primeira versão": o histórico é quem diz o que aconteceu.
    """
    if manifest and manifest.get("version"):
        return str(manifest["version"])
    if skill_text is not None:
        from ..domain.skills import parse_frontmatter
        fm = parse_frontmatter(skill_text.decode("utf-8", "replace")).frontmatter
        if fm.get("version"):
            return str(fm["version"]).strip()
    return "0.1.0"


def _read_manifest(files: dict[str, bytes]) -> dict | None:
    raw = files.get(MANIFEST_NAME)
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


class Importer:
    def __init__(self, repo: Repository):
        self.repo = repo

    # ---- entrada ---------------------------------------------------------
    def from_path(self, raw_path: str | Path, *, upstream: str | None = None,
                  dry_run: bool = False,
                  version_of: str | None = None) -> ImportReport:
        path = Path(raw_path)
        try:
            metadata = stat_import_path(path)
            if stat.S_ISDIR(metadata.st_mode):
                extraction = inspect_directory(path)
            elif path.name.endswith(".lia-capability"):
                # Pacote do Hub: o conteúdo vive sob payload/. Desembrulhar antes
                # de tudo — senão o reimport produziria payload/payload/SKILL.md
                # e o hash nunca casaria com a origem.
                extraction = inspect_package(path)
            elif path.suffix.lower() == ".zip":
                extraction = inspect_zip(path.read_bytes())
            else:
                # arquivo solto: vira um pacote de um arquivo só
                data = path.read_bytes()
                from .safe_extract import ExtractedFile
                extraction = Extraction(files=[
                    ExtractedFile(path=path.name, data=data,
                                  is_executable=looks_like_script((path.name,)))])
        except FileNotFoundError:
            return ImportReport(False, blocked_reason=f"Caminho não existe: {path}",
                                hint="Verifique o caminho e tente novamente.")
        except PermissionError:
            return ImportReport(False, blocked_reason=f"Acesso negado: {path}",
                                hint="Selecione uma origem que você possa ler.")
        except SecurityError as e:
            return ImportReport(False, blocked_reason=e.message, hint=e.hint)

        return self.from_extraction(extraction, upstream=upstream or str(path),
                                    dry_run=dry_run, version_of=version_of)

    def from_extraction(self, extraction: Extraction, *, upstream: str | None = None,
                        dry_run: bool = False,
                        version_of: str | None = None) -> ImportReport:
        files = {f.path: f.data for f in extraction.files}
        report = ImportReport(ok=False, warnings=list(extraction.warnings))
        report.contains_scripts = extraction.contains_scripts

        # ---- 1. BOM: normaliza e REGISTRA (nunca silencioso) -------------
        normalized: dict[str, bytes] = {}
        for rel, data in files.items():
            if has_bom(data):
                report.warnings.append(
                    f"`{rel}` tinha BOM (U+FEFF) no início; removido e registrado.")
                data = strip_bom(data)
            normalized[rel] = data
        files = normalized

        # ---- 2. Unicode por região, sem apagar nada ----------------------
        unicode_block = False
        # O NOME do arquivo também é conteúdo não confiável. Antes só o corpo
        # de .md/.txt/.json era varrido; `a\u202egnp.exe` passava limpo mesmo
        # sendo o caso clássico de spoof de extensão (o bidi inverte o que o
        # usuário vê). Um script com nome forjado não precisa de extensão de
        # texto para enganar quem lê a lista de arquivos.
        for rel in files:
            res_nome = scan(rel, context=Context.IDENTIFIER)
            if res_nome.findings:
                report.unicode_findings.extend(
                    {**f.as_dict(), "file": rel, "where": "nome do arquivo"}
                    for f in res_nome.findings
                )
                report.issues.append({
                    "severity": "warning", "code": "UNICODE_FILENAME",
                    "message": "O NOME do arquivo contém caractere invisível ou "
                               "direcional. O nome exibido pode não ser o nome real.",
                    "where": rel,
                })
                report.requires_review = True

        for rel, data in files.items():
            if not rel.lower().endswith((".md", ".txt", ".json")):
                continue
            text = data.decode("utf-8", "replace")
            res = scan(text, context=Context.PROSE)
            report.unicode_findings.extend(
                {**f.as_dict(), "file": rel} for f in res.findings
            )
            if res.rejected:
                unicode_block = True
                report.issues.append({
                    "severity": "error", "code": "UNICODE_REJECT",
                    "message": f"{len(res.rejected)} caractere(s) bidirecional(is) ou de "
                               f"tag em contexto que não admite uso legítimo.",
                    "where": rel,
                })

        if unicode_block:
            report.blocked_reason = (
                "O recurso contém caracteres invisíveis que não têm uso legítimo "
                "em bloco de código ou identificador.")
            report.hint = (
                "Abra o arquivo apontado e remova os caracteres listados. Eles podem "
                "ter sido inseridos por acidente ou de propósito.")
            return report

        if any(f["category"] == "B" for f in report.unicode_findings):
            report.requires_review = True
        if any(f["category"] == "D" for f in report.unicode_findings):
            report.requires_review = True

        # ---- 3. tipo + validação estrutural ------------------------------
        rtype = _detect_type(files)
        report.resource_type = rtype.value

        # ---- 3a. descritor de servidor MCP ------------------------------
        # `mcp.json` no payload classifica o recurso como `mcp-server`. O Hub
        # REGISTRA endpoint, transporte e fluxo de autenticação — não conecta,
        # não autentica e não guarda segredo.
        #
        # Descritor com cara de credencial RECUSA o recurso inteiro em vez de
        # sanear em silêncio: sanear deixaria o autor achando que o segredo
        # estava protegido, quando o certo é ele nunca ter estado ali.
        servidor_mcp = None
        if DESCRITOR in files:
            if rtype is ResourceType.AGENT_SKILL:
                report.issues.append({
                    "severity": "warning", "code": "MCP_DESCRIPTOR_IGNORED",
                    "message": f"O recurso tem `{DESCRITOR}` e `SKILL.md`. Fica "
                               f"classificado como Skill; o descritor é "
                               f"preservado como arquivo.",
                    "where": DESCRITOR})
            else:
                try:
                    servidor_mcp = ler_descritor(files)
                    rtype = ResourceType.MCP_SERVER
                    report.resource_type = rtype.value
                except DescritorInvalido as exc:
                    report.blocked_reason = str(exc)
                    report.hint = (f"Corrija `{DESCRITOR}` ou remova-o. O Hub "
                                   f"não conecta, não autentica e não guarda "
                                   f"segredo algum.")
                    return report

        # Armadilha do `or`: um SKILL.md VAZIO é `b""`, que é FALSO em Python.
        # A expressão `files.get("SKILL.md") or ...` pulava a validação
        # inteira, e um recurso sem uma única linha de frontmatter era
        # estagiado com zero issues. Tem que testar presença da CHAVE.
        skill_text = files.get("SKILL.md")
        if skill_text is None:
            skill_text = files.get("skill.md")
        skill_name = ""
        declared_license: str | None = None
        namespace_declarado = ""
        declared_description = ""
        domain, tags, author = "", [], None

        if rtype is ResourceType.AGENT_SKILL and skill_text is not None:
            text = skill_text.decode("utf-8", "replace")
            # A pasta do recurso vem do CAMINHO DE ORIGEM, não do layout
            # interno do payload. Antes usava-se o primeiro segmento de
            # qualquer arquivo com "/", então um recurso flat com `docs/x.md`
            # era comparado contra a pasta `docs`. Ver folder_name_do_recurso.
            folder = folder_name_do_recurso(upstream, list(files))
            issues = validate_skill(text, folder_name=folder)
            # Referências a arquivos: só faz sentido com o pacote completo em mãos.
            # folder_name é necessário aqui: sem ele, uma referência no
            # formato `<a-propria-skill>/x.md` não é reconhecida como interna.
            issues.extend(check_references(text, set(files), folder_name=folder))
            report.issues.extend(i.as_dict() for i in issues)
            if has_blocking(issues):
                # R-4.1d: citar o CÓDIGO real. A mensagem genérica mandava
                # "corrigir os campos apontados como erro" mesmo quando a
                # causa era outra — o usuário caçava um problema inexistente
                # no frontmatter.
                erros = [i for i in issues if i.severity is Severity.ERROR]
                codigos = sorted({i.code for i in erros})
                report.blocked_reason = (
                    "O recurso foi recusado por erro estrutural: "
                    + ", ".join(codigos) + ".")
                report.hint = "; ".join(sorted({i.message for i in erros})[:3])
                return report
            from ..domain.skills import parse_frontmatter
            fm = parse_frontmatter(text).frontmatter
            skill_name = fm.get("name", "")
            # Namespace (`stitch::react-components`): o id, o nome exibido e
            # a pasta usam o nome LOCAL. O namespace identifica o plugin de
            # origem e vai para `extra.namespace`, para não se perder nem
            # poluir o identificador do recurso.
            if "::" in skill_name:
                namespace_declarado, _, skill_name = skill_name.rpartition("::")
            else:
                namespace_declarado = ""
            # P-E2: declaração de licença no frontmatter.
            declared_license = (fm.get("license") or "").strip() or None
            declared_description = (fm.get("description") or "").strip()
            # `metadata` é um saco de chaves livres do formato Agent Skills.
            # Jogá-lo inteiro em `domain` rotulava toda skill com a string crua
            # ("tags:juridico,..."). Extraímos só o que sabemos interpretar.
            meta = fm.get("metadata", "") or ""
            domain = ""
            # Forma aninhada primeiro (`metadata:\n  domain: x`), que é a que
            # o parser agora preserva. Se lêssemos só a forma inline, o
            # `domain` continuaria vazio para quem usa bloco — e o campo é
            # usado para descoberta no catálogo.
            for chave in ("metadata.domain", "metadata.dominio", "metadata.domínio"):
                if fm.get(chave):
                    domain = fm[chave].strip()
                    break
            if not domain:
                for chave in ("domain", "dominio", "domínio"):
                    for par in meta.replace(";", ",").split(","):
                        if par.strip().lower().startswith(chave + ":"):
                            domain = par.split(":", 1)[1].strip()
            if fm.get("metadata.tags"):
                # Bloco aninhado: o valor já vem limpo do parser.
                tags = [x.strip() for x in
                        fm["metadata.tags"].replace(";", ",").split(",") if x.strip()]
            elif "tags:" in meta:
                bruto = meta.split("tags:", 1)[1]
                # corta na próxima chave conhecida, se houver
                for sep in (" domain:", " dominio:", " author:", " license:"):
                    if sep in bruto:
                        bruto = bruto.split(sep, 1)[0]
                tags = [x.strip() for x in bruto.replace(";", ",").split(",") if x.strip()]
            # `author` pode vir do `metadata:` aninhado (forma dominante no
            # acervo real: `metadata:\n  author: ...`) ou inline. O parser
            # achatou o aninhado em `metadata.author`, então checamos os dois.
            for chave in ("metadata.author", "metadata.autor"):
                if fm.get(chave):
                    author = fm[chave].split(",")[0].strip() or None
                    break
            if author is None:
                for chave in ("author", "autor"):
                    if chave + ":" in meta:
                        author = meta.split(chave + ":", 1)[1].split(",")[0].strip() or None
                        break

        # ---- 4. manifesto de pacote .lia-capability ----------------------
        # Preferir o manifesto lido pelo extrator de pacotes: ele não está em
        # `files` porque `payload/` foi desembrulhado.
        manifest = extraction.manifest or _read_manifest(files)
        if manifest:
            declared = manifest.get("files") or manifest.get("payload", {}).get("files") or []
            for entry in declared:
                rel = entry.get("path") if isinstance(entry, dict) else None
                if not rel:
                    continue
                if rel not in files:
                    report.issues.append({
                        "severity": "warning", "code": "MANIFEST_MISSING_FILE",
                        "message": f"O manifesto declara `{rel}`, que não está no pacote.",
                        "where": MANIFEST_NAME,
                    })
            extra = set(files) - {"manifest.json"} - {
                (e.get("path") if isinstance(e, dict) else None) for e in declared
            } - {"provenance.json", "NOTICE", "THIRD_PARTY_NOTICES.md"}
            for rel in sorted(x for x in extra if x):
                report.issues.append({
                    "severity": "warning", "code": "UNMANIFESTED_FILE",
                    "message": f"`{rel}` está no pacote mas não consta no manifesto.",
                    "where": MANIFEST_NAME,
                })

        # ---- 5. licença: presença, nunca inferência ----------------------
        #
        # P-E2 / R-2.3: o campo `license` do frontmatter é uma DECLARAÇÃO do
        # autor, não permissão. Antes ele era ignorado: se não houvesse
        # arquivo `LICENSE`, o registro saía `unknown` — 47 recursos do acervo
        # real "sem licença" que na verdade tinham licença escrita no texto.
        #
        # Ordem de confiança: arquivo de licença (evidência física) vence
        # frontmatter (afirmação). Se só há frontmatter, registramos como
        # declarado e a base aponta que a evidência é textual — nunca
        # `redistributable=True`, que continua exigindo decisão humana.
        detected, lstatus = _detect_license(files)
        base_declarada = "arquivo de licença no payload" if detected else ""
        if detected is None and declared_license:
            detected = declared_license
            lstatus = LicenseStatus.DECLARED.value
            base_declarada = ("frontmatter da SKILL.md — afirmação do autor, "
                              "não verificação")
        report.detected_license = detected
        report.license_status = lstatus
        if detected is None:
            report.warnings.append(
                "Nenhum arquivo de licença encontrado. Ausência de licença NÃO "
                "significa que o recurso é livre.")

        # ---- 6. metadados e staging -------------------------------------
        display = skill_name or (manifest or {}).get("name") or Path(upstream or "recurso").stem
        cap_id = new_id(display, salt=tree_hash({k: sha256_bytes(v) for k, v in files.items()}))
        report.capability_id = cap_id
        report.name = display

        # Hashes ANTES de qualquer atalho: o relatório precisa dos mesmos
        # campos em todos os caminhos. Antes o atalho de "já existe" voltava
        # com `hashes` vazio, e o consumidor que verifica integridade recebia
        # um relatório sem hash nenhum — silenciosamente pior justo no caso em
        # que ele mais precisa comparar com o que já tem.
        per_file = {rel: sha256_bytes(data) for rel, data in files.items()}
        th = tree_hash(per_file)
        primario = files.get("SKILL.md")
        if primario is None:
            primario = files.get("skill.md")
        if primario is None:
            # Nem toda capacidade tem SKILL.md: um `mcp.json` sozinho é um
            # recurso válido. Antes o contentHash saía VAZIO nesse caso, e o
            # consumidor que confere integridade recebia nada justamente para
            # o tipo que mais depende de conferir o descritor. Cai no arquivo
            # primário de fato; se não houver primário, o treeHash cobre.
            for candidato in ("mcp.json", "workflow.md", "README.md", "manifest.json"):
                if candidato in files:
                    primario = files[candidato]
                    break
        ch = sha256_bytes(primario) if primario else ""
        report.hashes = {"contentHash": ch, "treeHash": th}

        # Conteúdo idêntico já na biblioteca: o id é derivado do conteúdo,
        # então isto é IDENTIDADE, não conflito. Reportar como tal é mais
        # honesto do que fingir que é uma importação nova.
        if self.repo.exists_anywhere(cap_id):
            report.ok = True
            report.already_present = True
            report.blocked_reason = ""
            report.warnings.append(
                "Conteúdo idêntico já está na sua biblioteca. Nada foi duplicado.")
            report.hint = "Se quiser outra cópia, altere o conteúdo ou renomeie o recurso."
            return report

        if dry_run:
            report.ok = True
            report.warnings.append("Simulação: nada foi gravado no disco.")
            return report
        # `report.hashes` já foi calculado acima, com fallback para recursos
        # sem SKILL.md. Recalcular aqui com a regra antiga apagava o fallback.
        report.files = [
            {"path": rel, "size": len(data),
             "sha256": per_file[rel],
             "normalizedSha256": content_hashes(data)["normalized"],
             "executable": looks_like_script(tuple(rel.split("/")))}
            for rel, data in sorted(files.items())
        ]

        now = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        cap = Capability(
            id=cap_id,
            name=display,
            version=_resolve_version(manifest, skill_text),
            type=rtype,
            # P-E1: manifesto primeiro; frontmatter como fallback quando não
            # houver manifesto. Antes o fallback não existia e o catálogo
            # inteiro saía com 48 descrições vazias mesmo tendo o texto no
            # SKILL.md. Só preenche o que estava vazio — aditivo.
            description=((manifest or {}).get("description", "") or ""
                         or declared_description),
            domain=domain,
            tags=tags,
            author=author,
            # Licença DETECTADA é registrada como declarada — mas nunca como
            # permissão. Detectar um arquivo MIT não é revisar a licença, e o
            # direito de redistribuir continua sendo decisão humana.
            #
            # `notice_required` é DERIVADO da licença identificada, não lido do
            # payload: um recurso importado não decide obrigação legal sobre si
            # mesmo. Antes o campo era omitido e voltava sempre False, então
            # um MIT era exportado sem NOTICE — obrigação do texto MIT
            # descumprida por omissão, não por decisão.
            license=License(
                code=detected,
                status=LicenseStatus(lstatus),
                redistributable=False,
                notice_required=notice_obrigatorio(detected),
                redistribution_basis=base_declarada or None,
            ),
            source=Source(upstream=upstream, imported_at=now, method="local"),
            trust=Trust.UNREVIEWED,
            extra=_extra_do_registro(namespace_declarado, servidor_mcp),
            # Saída de rede DECLARADA. Para um servidor MCP o endpoint é a
            # informação de egress mais importante que existe: é para lá que
            # o host vai falar. Registrá-lo faz o risco e a revisão humana
            # enxergarem o destino, em vez de o dado ficar só no descritor.
            egress=([servidor_mcp.endpoint] if servidor_mcp else []),
            content_hash=report.hashes["contentHash"],
            tree_hash=th,
            contains_scripts=report.contains_scripts,
            version_of=version_of,
        )
        provider = {"schemaVersion": 1, "upstream": upstream, "importedAt": now,
                    "method": "local", "files": report.files,
                    "hashes": report.hashes,
                    "note": "Hashes provam integridade, não autoria."}

        # `alreadyPresent` era declarado, serializado e NUNCA atribuído:
        # sempre saía False. Quem reimportava o mesmo conteúdo não tinha como
        # saber que o registro já existia — e a quarentena era sobrescrita em
        # silêncio, inclusive quando o `upstream` era outro (aí a procedência
        # gravada passava a ser a nova, sem aviso).
        #
        # O id é derivado do CONTEÚDO, então conteúdo idêntico é identidade e
        # não conflito: dizer `alreadyPresent=True` é a informação correta. O
        # registro antigo é preservado em backup pelo `stage` (escrita
        # atômica com versão anterior guardada), e o aviso abaixo diz o que
        # foi reescrito quando a procedência muda.
        anterior = None
        if self.repo.exists_anywhere(cap_id):
            try:
                anterior = self.repo._load_any(cap_id).capability
            except Exception:
                anterior = None
        report.already_present = anterior is not None
        if anterior is not None:
            up_antigo = anterior.source.upstream
            if up_antigo and upstream and up_antigo != upstream:
                report.warnings.append(
                    f"Registro existente tinha procedência `{up_antigo}`; "
                    f"esta importação grava `{upstream}`. O conteúdo é "
                    f"idêntico (o id vem do hash), mas a procedência mudou.")

        self.repo.stage(cap_id, files, cap.as_dict(), provider,
                        {"action": "import", "at": now, "upstream": upstream})

        report.ok = True
        report.staged_at = now
        report.warnings.append(
            "O recurso está na quarentena. A promoção à biblioteca é uma decisão sua.")
        return report

    def promote(self, cap_id: str) -> Capability:
        return self.repo.promote(cap_id).capability
