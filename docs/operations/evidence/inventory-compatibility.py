"""Read-only verification of the inventory example and the existing Stitch records."""
import json
import re
from pathlib import Path
from uuid import UUID

from lia_agenthub.domain.model import Capability

ROOT = Path(__file__).resolve().parents[3]


def verify_example():
    path = ROOT / "docs/examples/central-capability-inventory.v1.json"
    envelope = json.loads(path.read_text(encoding="utf-8"))
    assert envelope["inventoryVersion"] == 1
    assert envelope["issuer"]["project"] == "lia-forge"
    record, = envelope["records"]
    assert record["id"].startswith("urn:lia:cap:")
    UUID(record["id"].removeprefix("urn:lia:cap:"))
    assert record["kind"] == "workflow"
    assert record["origins"][0]["commit"] is None
    assert record["compatibility"][0]["result"] == "declared"
    assert record["license"]["redistribution"]["status"] == "unknown"
    assert record["observations"] == []
    print("Exemplo v1: workflow com compatibilidade declarada e sem estados inferidos")


def verify_existing():
    path = ROOT / "docs/stitch/catalog/google-stitch.records.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    ids = set()
    types = set()
    for entry in catalog["records"]:
        raw = entry["capability"]
        cap = Capability.from_dict(raw)
        assert cap.as_dict() == raw, cap.id
        assert cap.id not in ids
        ids.add(cap.id)
        types.add(cap.type.value)
        assert cap.lifecycle.value == "quarantined"
        assert not cap.license.redistributable
        assert re.fullmatch(r"[a-f0-9]{64}", cap.tree_hash)
        assert entry["provenance"]["upstream"]
    assert len(ids) == catalog["recordCount"]
    assert types == {"agent-skill", "mcp-server"}
    print(f"Roundtrip v1: {len(ids)} registros, IDs e campos preservados")
    print("Tipos: agent-skill, mcp-server; todos em quarentena, sem redistribuição autorizada")


if __name__ == "__main__":
    verify_example()
    verify_existing()
