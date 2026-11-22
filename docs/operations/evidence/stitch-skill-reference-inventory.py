"""Emit central inventory references from the pinned legacy Stitch catalog."""

import json
import subprocess
import uuid

COMMIT = "90b6e5cbb8658c898046dae6e8d210960a09558e"
PATH = "docs/stitch/catalog/google-stitch.records.json"
REPOSITORY = "https://github.com/BloomRX/Lia-AgentHub"
NAMESPACE = uuid.UUID("81737276-5209-4cae-aae3-533452355a04")


def main():
    catalog = json.loads(subprocess.check_output(["git", "show", f"{COMMIT}:{PATH}"]))
    records = []
    for item in catalog["records"]:
        cap = item["capability"]
        if cap["type"] != "agent-skill":
            continue
        provenance = item["provenance"]
        upstream, _, skill_path = provenance["upstream"].partition(":")
        old_id = cap["id"]
        records.append({
            "id": f"urn:lia:cap:{uuid.uuid5(NAMESPACE, old_id)}",
            "revisionId": COMMIT,
            "kind": "agent-skill",
            "name": cap["name"],
            "version": None,
            "description": f"Referência à Skill Stitch {cap['name']} no catálogo legado.",
            "origins": [
                {"project": "lia-agent-hub", "repository": REPOSITORY,
                 "path": PATH, "commit": COMMIT},
                {"project": "external", "repository": provenance["upstreamRepo"],
                 "path": f"{skill_path}/SKILL.md"},
            ],
            "aliases": [{"scheme": "lia-capability-v1", "value": old_id,
                         "authority": "lia-agent-hub"}],
            "license": {
                "declared": provenance["licenseEvidence"]["spdx"],
                "redistribution": {"status": "pending", "authorizationIds": []},
            },
            "integrity": [
                {"algorithm": "sha256", "scope": "legacy-content",
                 "digest": provenance["hashes"]["contentHash"]},
                {"algorithm": "sha256", "scope": "legacy-tree",
                 "digest": provenance["hashes"]["treeHash"]},
            ],
            "details": {"upstreamReference": upstream, "sourceClass": "legacy-catalog-reference"},
        })
    if len(records) != 16:
        raise ValueError("Esperadas 16 referências Stitch.")
    print(json.dumps({
        "inventoryVersion": 1,
        "inventoryId": "lia-agent-hub-stitch-skill-references",
        "revision": COMMIT,
        "generatedAt": "2026-11-22T00:00:00Z",
        "complete": False,
        "issuer": {"project": "lia-agent-hub", "repository": REPOSITORY,
                   "maintainer": "Lia Agent Hub"},
        "records": records,
        "evidence": [],
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
