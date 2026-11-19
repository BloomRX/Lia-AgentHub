"""Project a pinned Lia-Project Git tree into a metadata-only Hub inventory."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from uuid import uuid4


REPOSITORY = "https://github.com/BloomRX/Lia-Project"
BRANCH = "arena/7fa837f0-lia-project"


def build_inventory(snapshot: dict, previous: dict | None) -> dict:
    if snapshot["status"] != "tree-inventoried":
        raise ValueError("A árvore do Project precisa estar disponível.")
    commit = snapshot["commit"]
    existing = {}
    if previous is not None:
        if previous["issuer"]["repository"] != REPOSITORY:
            raise ValueError("O inventário anterior pertence a outro repositório.")
        if previous["revision"] == commit:
            recorded = {
                record["origins"][0]["path"]: record["integrity"][0]["digest"]
                for record in previous["records"]
            }
            observed = {skill["path"]: skill["blob"] for skill in snapshot["skills"]}
            if recorded != observed:
                raise ValueError("O snapshot diverge do inventário fixado para o mesmo commit.")
            return previous
        for record in previous["records"]:
            existing[record["origins"][0]["path"]] = record["id"]

    now = datetime.now(timezone.utc).isoformat()
    source_id = "project-tree"
    records = []
    for skill in sorted(snapshot["skills"], key=lambda item: item["path"]):
        path = skill["path"]
        name = PurePosixPath(path).parent.name
        is_vendor = path.startswith("airi/")
        records.append({
            "id": existing[path] if path in existing else f"urn:lia:cap:{uuid4()}",
            "revisionId": commit,
            "kind": "agent-skill",
            "name": name,
            "description": None,
            "version": None,
            "origins": [{
                "project": "external" if is_vendor else "lia-project",
                "repository": REPOSITORY,
                "path": path,
                "branch": BRANCH,
                "commit": commit,
                "author": None,
                "maintainer": None,
                "evidenceIds": [source_id],
            }],
            "aliases": [{"scheme": "git-path", "value": path, "authority": REPOSITORY}],
            "license": {
                "declared": None,
                "components": [],
                "redistribution": {"status": "pending", "authorizationIds": []},
            },
            "integrity": [{
                "algorithm": "git-sha1",
                "scope": "source-blob",
                "digest": skill["blob"],
                "evidenceIds": [source_id],
            }],
            "details": {
                "sourceClass": "vendored-upstream" if is_vendor else "project-tree",
                "migrationDisposition": "reference-only",
                "attachedBlobCandidates": [
                    {"path": item["path"], "gitBlob": item["sha"]}
                    for item in skill["files"] if item["path"] != path
                ],
            },
        })
    return {
        "inventoryVersion": 1,
        "inventoryId": "lia-project-skills",
        "revision": commit,
        "generatedAt": now,
        "issuer": {"project": "lia-project", "repository": REPOSITORY,
                   "maintainer": "Lia-Project"},
        "complete": False,
        "records": records,
        "evidence": [{
            "id": source_id,
            "kind": "commit",
            "locator": f"{REPOSITORY}/tree/{commit}",
            "recordedAt": now,
            "recordedBy": "Lia Agent Hub",
            "subject": "Inventário de caminhos e blobs Git, sem importar payload",
        }],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--previous", type=Path, help="Inventário anterior para conservar IDs")
    args = parser.parse_args()
    snapshots = json.loads(args.snapshot.read_bytes())
    snapshot, = (item for item in snapshots if item["project"] == "Lia-Project")
    previous = json.loads(args.previous.read_bytes()) if args.previous else None
    inventory = build_inventory(snapshot, previous)
    with args.output.open("x", encoding="utf-8") as file:
        json.dump(inventory, file, ensure_ascii=False, indent=2)
        file.write("\n")


if __name__ == "__main__":
    main()
