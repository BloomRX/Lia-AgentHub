"""Serviço de aplicação — orquestra adaptadores. A UI fala só com isto."""
from __future__ import annotations

import datetime as _dt
import logging
from dataclasses import dataclass
from pathlib import Path

from .adapters.importer import ImportReport, Importer
from .adapters.index_builder import check_consistency, publish, read_index, validate_index
from .adapters.packager import Target, export, verify_package
from .adapters.paths_resolver import Locations, resolve_locations
from .adapters.repository import Repository
from .domain.errors import LiaError
from .domain.integrity import sha256_bytes
from .domain.model import Capability, Lifecycle, Trust
from .domain.risk import assess
from .domain.skills import validate_skill

log = logging.getLogger("lia_agenthub")


@dataclass
class SearchQuery:
    text: str = ""
    type: str = ""
    domain: str = ""
    tag: str = ""
    trust: str = ""
    lifecycle: str = ""


class AgentHub:
    """Fachada do produto. Não executa nada que venha de fora."""

    def __init__(self, locations: Locations | None = None):
        self.locations = locations or resolve_locations()
        self.locations.ensure()
        self.repo = Repository(self.locations)
        self.importer = Importer(self.repo)

    # ---- C2 biblioteca ---------------------------------------------------
    def items(self, query: SearchQuery | None = None) -> list[dict]:
        q = query or SearchQuery()
        out = []
        source = (self.repo.list_quarantine()
                  if q.lifecycle == "quarantined" else self.repo.list_all())
        for stored in source:
            cap = stored.capability
            if q.lifecycle and cap.lifecycle.value != q.lifecycle:
                continue
            if q.type and cap.type.value != q.type:
                continue
            if q.domain and cap.domain != q.domain:
                continue
            if q.trust and cap.trust.value != q.trust:
                continue
            if q.tag and q.tag not in cap.tags:
                continue
            if q.text:
                hay = " ".join([cap.id, cap.name, cap.description, " ".join(cap.tags)]).lower()
                if q.text.lower() not in hay:
                    continue
            out.append(self._summary(cap))
        return sorted(out, key=lambda d: d["name"].lower())

    def _summary(self, cap: Capability) -> dict:
        risk = assess(cap)
        return {
            "id": cap.id,
            "name": cap.name,
            "version": cap.version,
            "type": cap.type.value,
            "domain": cap.domain,
            "tags": list(cap.tags),
            "description": cap.description,
            "trust": cap.trust.value,
            "lifecycle": cap.lifecycle.value,
            "license": cap.license.code,
            "licenseKnown": cap.license.is_known,
            "risk": risk.level.value,
            "containsScripts": cap.contains_scripts,
        }

    def detail(self, cap_id: str) -> dict:
        stored = self.repo.load(cap_id)
        cap = stored.capability
        risk = assess(cap)
        return {
            **cap.as_dict(),
            "risk": risk.as_dict(),
            "validation": self.repo.read_validation(cap_id),
            "history": self.repo.history(cap_id),
            "duplicates": self.repo.find_duplicates(cap_id),
            "files": sorted(self.repo.payload_files(cap_id).keys()),
            "integrityNow": self.repo.recompute_hashes(cap_id),
        }

    # ---- C3 importação ---------------------------------------------------
    def import_path(self, path: str, *, dry_run: bool = False) -> ImportReport:
        report = self.importer.from_path(path, dry_run=dry_run)
        log.info("import %s ok=%s id=%s", path, report.ok, report.capability_id)
        return report

    def promote(self, cap_id: str) -> dict:
        cap = self.importer.promote(cap_id)
        self.repo.append_history(cap_id, {
            "action": "promote", "at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "trustBefore": "unreviewed", "trustAfter": cap.trust.value,
        })
        try:
            publish(self.repo, packages_dir=self.locations.exports)
        except LiaError as e:
            log.warning("índice não publicado: %s", e)
        return self._summary(cap)

    def discard(self, cap_id: str) -> None:
        self.repo.delete(cap_id, confirmed=True)

    # ---- C4 validação ----------------------------------------------------
    def validate(self, cap_id: str) -> dict:
        stored = self.repo.load(cap_id)
        files = self.repo.payload_files(cap_id)
        primary = files.get("SKILL.md") or files.get("skill.md")
        if primary is None:
            report = {"issues": [], "summary": {k: 0 for k in
                      ("error", "warning", "info", "review")},
                      "note": "Este recurso não tem SKILL.md; só a contenção de "
                              "caminho e o Unicode foram verificados."}
        else:
            folder = next((p.split("/")[0] for p in files if "/" in p), None)
            issues = validate_skill(primary.decode("utf-8", "replace"), folder_name=folder)
            report = {
                "issues": [i.as_dict() for i in issues],
                "summary": {
                    **{k: 0 for k in ("error", "warning", "info", "review")},
                    **{s: sum(1 for i in issues if i.severity.value == s)
                       for s in ("error", "warning", "info", "review")},
                },
                "note": "Validação estrutural. Não avalia se o conteúdo é seguro.",
            }
        report["at"] = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        self.repo.save_validation(cap_id, report)
        return report

    # ---- C5 confiança ----------------------------------------------------
    def set_trust(self, cap_id: str, trust: str, *, decided_by: str = "humano") -> dict:
        if trust not in {t.value for t in Trust}:
            raise LiaError(f"Confiança inválida: {trust}", "Use um valor da escala.")
        stored = self.repo.load(cap_id)
        before = stored.capability.trust.value
        stored.capability.trust = Trust(trust)
        from .adapters.atomic import atomic_write_json
        atomic_write_json(stored.meta / "capability.json", stored.capability.as_dict())
        self.repo.append_history(cap_id, {
            "action": "trust", "at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "trustBefore": before, "trustAfter": trust, "decidedBy": decided_by,
        })
        return self._summary(stored.capability)

    def set_license(self, cap_id: str, *, code: str = "", redistributable: bool = False,
                    basis: str = "") -> dict:
        from .adapters.atomic import atomic_write_json
        from .domain.model import LicenseStatus
        stored = self.repo.load(cap_id)
        lic = stored.capability.license
        lic.code = code or None
        lic.status = LicenseStatus.DECLARED if code else LicenseStatus.UNKNOWN
        lic.redistributable = redistributable
        lic.redistribution_basis = basis or None
        atomic_write_json(stored.meta / "capability.json", stored.capability.as_dict())
        self.repo.append_history(cap_id, {
            "action": "license", "at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "license": lic.code, "redistributable": redistributable,
        })
        return self._summary(stored.capability)

    # ---- C6 versões ------------------------------------------------------
    def history(self, cap_id: str) -> list[dict]:
        return self.repo.history(cap_id)

    def duplicates(self, cap_id: str) -> list[str]:
        return self.repo.find_duplicates(cap_id)

    def diff_versions(self, cap_a: str, cap_b: str) -> dict:
        a, b = self.repo.payload_files(cap_a), self.repo.payload_files(cap_b)
        only_a = sorted(set(a) - set(b))
        only_b = sorted(set(b) - set(a))
        changed = sorted(p for p in set(a) & set(b) if a[p] != b[p])
        return {"onlyInA": only_a, "onlyInB": only_b, "changed": changed,
                "identical": not only_a and not only_b and not changed}

    # ---- C7 exportação ---------------------------------------------------
    def export(self, cap_id: str, target: str = "private",
               destination: str | None = None) -> dict:
        dest = Path(destination) if destination else self.locations.exports
        result = export(cap_id, self.repo, dest, target=Target(target))
        if result.ok:
            self.repo.append_history(cap_id, {
                "action": "export", "target": target,
                "at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
                "package": Path(result.path).name, "packageHash": result.package_hash,
            })
        return {"ok": result.ok, "path": result.path, "packageHash": result.package_hash,
                "warnings": result.warnings or [], "refusedReason": result.refused_reason,
                "hint": result.hint}

    def verify_package(self, path: str) -> dict:
        return verify_package(path)

    # ---- C8 índice -------------------------------------------------------
    def publish_index(self) -> dict:
        idx = publish(self.repo, packages_dir=self.locations.exports)
        return {"ok": True, "count": len(idx["capabilities"]),
                "path": str(self.locations.common / "index.json")}

    def read_index(self) -> dict | None:
        return read_index(self.locations.common)

    def index_health(self) -> dict:
        idx = read_index(self.locations.common)
        if idx is None:
            # Sem índice não é erro: é o estado inicial. Não inventamos um.
            return {"exists": False, "problems": [], "missingPackages": [],
                    "orphanPackages": [], "notIndexed": [], "ok": True,
                    "note": "Nenhum índice publicado ainda."}
        problems = validate_index(idx)
        cons = check_consistency(idx, self.locations.exports, self.locations.library)
        return {"exists": True, "problems": problems, **cons,
                "ok": not problems and cons["ok"]}

    # ---- C9 diagnóstico --------------------------------------------------
    def diagnostics(self) -> dict:
        from .adapters.paths_resolver import is_frozen
        import platform, sys
        return {
            "app": "Lia Agent Hub",
            "version": __import__("lia_agenthub").__version__,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "frozen": is_frozen(),
            "paths": self.locations.as_dict(),
            "counts": {
                "library": len(self.repo.list_all()),
                "quarantine": len([p for p in self.locations.quarantine.iterdir()
                                   if p.is_dir()]) if self.locations.quarantine.is_dir() else 0,
            },
            "index": self.index_health(),
        }
