"""Modelo canônico de capacidade — PRODUCT-BOUNDARIES §6.

Invariantes que o código garante e os testes verificam:
- `secrets` guarda NOMES de variável, nunca valores.
- `license: None` significa NÃO SEI, jamais "livre".
- `hash` ≠ assinatura. Não existe campo `signed` no MVP.
- `requirements` desconhecido é None, nunca 0 nem "ok".
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from enum import Enum

SCHEMA_VERSION = 1


class ResourceType(str, Enum):
    """Tipos previstos. Só `agent_skill` é implementado de ponta a ponta no MVP."""

    AGENT_SKILL = "agent-skill"
    MCP_SERVER = "mcp-server"
    CLI_TOOL = "cli-tool"
    API_SERVICE = "api-service"
    PLUGIN = "plugin"
    FRAMEWORK = "framework"
    PROVIDER_MODEL = "provider-model"
    WORKFLOW = "workflow"
    TEMPLATE = "template"
    REFERENCE = "reference"
    UNKNOWN = "unknown"


class Trust(str, Enum):
    """Escala de confiança. Promoção a `reviewed_external` exige humano."""

    UNREVIEWED = "unreviewed"
    USER_PROVIDED = "user-provided"
    REVIEWED_EXTERNAL = "reviewed-external"
    FIRST_PARTY = "first-party"


class Lifecycle(str, Enum):
    QUARANTINED = "quarantined"
    ACTIVE = "active"
    #: Substituída por uma versão mais nova. Fica no disco, consultável.
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class LicenseStatus(str, Enum):
    DECLARED = "declared"
    UNKNOWN = "unknown"
    CONFLICTING = "conflicting"


class Severity(str, Enum):
    ERROR = "error"       # impeditivo
    WARNING = "warning"   # aviso
    INFO = "info"         # informação
    REVIEW = "review"     # exige humano


SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[\w.-]+)?(?:\+[\w.-]+)?$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


@dataclass
class Issue:
    severity: Severity
    code: str
    message: str
    where: str = ""

    def as_dict(self) -> dict:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "where": self.where,
        }


@dataclass
class License:
    """Licença POR CAMADA (código, conteúdo, pesos) — §6.4."""

    code: str | None = None
    content: str | None = None
    weights: str | None = None
    status: LicenseStatus = LicenseStatus.UNKNOWN
    redistributable: bool = False
    redistribution_basis: str | None = None
    notice_required: bool = False

    def as_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, d: dict | None) -> "License":
        if not d:
            return cls()
        return cls(
            code=d.get("code"),
            content=d.get("content"),
            weights=d.get("weights"),
            status=LicenseStatus(d.get("status", "unknown")),
            redistributable=bool(d.get("redistributable", False)),
            redistribution_basis=d.get("redistribution_basis"),
            notice_required=bool(d.get("notice_required", False)),
        )

    @property
    def is_known(self) -> bool:
        """True só se ALGUMA camada tem licença declarada."""
        return any((self.code, self.content, self.weights))


@dataclass
class Source:
    """Procedência declarada. Não é prova de autoria — SECURITY §3.7.1."""

    upstream: str | None = None
    commit: str | None = None
    imported_at: str | None = None
    method: str = "local"
    original_name: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Capability:
    id: str
    name: str
    version: str
    type: ResourceType = ResourceType.UNKNOWN
    description: str = ""
    domain: str = ""
    tags: list[str] = field(default_factory=list)
    author: str | None = None
    license: License = field(default_factory=License)
    source: Source = field(default_factory=Source)
    trust: Trust = Trust.UNREVIEWED
    lifecycle: Lifecycle = Lifecycle.QUARANTINED
    content_hash: str = ""
    tree_hash: str = ""
    contains_scripts: bool = False
    declared_permissions: list[str] = field(default_factory=list)
    egress: list[str] = field(default_factory=list)
    secrets_env_vars: list[str] = field(default_factory=list)
    requirements: dict | None = None
    history: list[dict] = field(default_factory=list)
    #: Id da versão que esta substitui, quando houver. Forma a linhagem.
    version_of: str | None = None

    # ---- serialização -----------------------------------------------------
    def as_dict(self) -> dict:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "type": self.type.value,
            "description": self.description,
            "domain": self.domain,
            "tags": list(self.tags),
            "author": self.author,
            "license": self.license.as_dict(),
            "source": self.source.as_dict(),
            "trust": self.trust.value,
            "lifecycle": self.lifecycle.value,
            "contentHash": self.content_hash,
            "treeHash": self.tree_hash,
            "containsScripts": self.contains_scripts,
            "declaredPermissions": list(self.declared_permissions),
            "egress": list(self.egress),
            "secrets": {"envVars": list(self.secrets_env_vars)},
            "requirements": self.requirements,
            "history": list(self.history),
            "versionOf": self.version_of,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Capability":
        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            version=d.get("version", "0.0.0"),
            type=ResourceType(d.get("type", "unknown")),
            description=d.get("description", ""),
            domain=d.get("domain", ""),
            tags=list(d.get("tags", [])),
            author=d.get("author"),
            license=License.from_dict(d.get("license")),
            source=Source(**d.get("source", {})),
            trust=Trust(d.get("trust", "unreviewed")),
            lifecycle=Lifecycle(d.get("lifecycle", "quarantined")),
            content_hash=d.get("contentHash", ""),
            tree_hash=d.get("treeHash", ""),
            contains_scripts=bool(d.get("containsScripts", False)),
            declared_permissions=list(d.get("declaredPermissions", [])),
            egress=list(d.get("egress", [])),
            secrets_env_vars=list(d.get("secrets", {}).get("envVars", [])),
            requirements=d.get("requirements"),
            history=list(d.get("history", [])),
            version_of=d.get("versionOf"),
        )

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), ensure_ascii=False, indent=2, sort_keys=True)


def new_id(name: str, *, salt: str = "") -> str:
    """ID estável derivado do nome. Nunca usa apenas o nome: colidiria."""
    import hashlib

    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:48] or "cap"
    digest = hashlib.sha256((name + salt).encode("utf-8")).hexdigest()[:8]
    return f"{base}-{digest}"
