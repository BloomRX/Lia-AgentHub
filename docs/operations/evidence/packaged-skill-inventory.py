"""Build an inventory from locally prepared, hash-pinned Skill packages."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from lia_agenthub.adapters.packager import verify_package
from lia_agenthub.domain.integrity import sha256_bytes, sha256_file


def entry(project: str, lock_path: Path, package_path: Path) -> tuple[dict, dict]:
    pin = json.loads(lock_path.read_bytes())
    if pin["lockVersion"] != 1 or pin["profile"] != project:
        raise ValueError(f"Perfil ou versão do manifesto incorreto: {lock_path.name}")
    if sha256_file(package_path) != pin["packageSha256"]:
        raise ValueError(f"Pacote diverge do SHA-256: {package_path.name}")
    checked = verify_package(package_path)
    manifest = checked["manifest"]
    if (not checked["ok"] or checked["computedTreeHash"] != pin["treeSha256"]
            or manifest["id"] != pin["capabilityId"] or manifest["version"] != pin["version"]
            or manifest["type"] != "agent-skill"):
        raise ValueError(f"Pacote diverge da revisão fixada: {package_path.name}")
    with ZipFile(package_path) as bundle:
        provenance = json.loads(bundle.read("provenance.json"))["source"]
    if provenance["upstream"] != f"{pin['skillId']}:{pin['revision']}":
        raise ValueError(f"Procedência divergente: {package_path.name}")
    origin = provenance["workshopOrigin"]
    repository = origin["repository"]
    evidence_id = f"git-{pin['capabilityId']}"
    record = {
        "id": pin["skillId"],
        "revisionId": f"workshop-{pin['revision']}",
        "kind": "agent-skill",
        "name": manifest["name"],
        "description": None,
        "version": manifest["version"],
        "origins": [{
            "project": project,
            "repository": repository,
            "path": origin["path"],
            "commit": origin["commit"],
            "author": origin["author"],
            "maintainer": origin["maintainer"],
            "evidenceIds": [evidence_id],
        }],
        "aliases": [
            {"scheme": "git-path", "value": origin["path"], "authority": repository},
            {"scheme": "lia-capability-v1", "value": pin["capabilityId"], "authority": project},
        ],
        "license": {
            "declared": None,
            "components": [],
            "redistribution": {"status": "pending", "authorizationIds": []},
        },
        "integrity": [
            {"algorithm": "sha256", "scope": "tree", "digest": pin["treeSha256"]},
            {"algorithm": "sha256", "scope": "package", "digest": pin["packageSha256"]},
        ],
        "details": {
            "sourceLicensePath": origin["licensePath"],
            "sourceLicenseSha256": origin["licenseSha256"],
            "privatePackagePrepared": True,
        },
    }
    evidence = {
        "id": evidence_id,
        "kind": "commit",
        "locator": f"{repository}/blob/{origin['commit']}/{origin['path']}",
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "recordedBy": "Lia Agent Hub",
        "subject": record["id"],
    }
    return record, evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", choices=("lia-forge", "lia-studio"))
    parser.add_argument("output", type=Path)
    parser.add_argument("--artifact", action="append", nargs=2, type=Path,
                        required=True, metavar=("LOCK", "PACKAGE"))
    args = parser.parse_args()
    records, evidence = zip(*(entry(args.project, *pair) for pair in args.artifact))
    origins = [record["origins"][0] for record in records]
    repositories = {origin["repository"] for origin in origins}
    if len(repositories) != 1 or len({record["id"] for record in records}) != len(records):
        raise ValueError("O lote exige uma origem de repositório e identidades distintas.")
    # A revisão do feed representa o conjunto exato de pacotes selecionados.
    pins = sorted(record["integrity"][1]["digest"] for record in records)
    output = {
        "inventoryVersion": 1,
        "inventoryId": f"{args.project}-skills-workshop",
        "revision": sha256_bytes("\n".join(pins).encode("ascii")),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "issuer": {"project": args.project, "repository": origins[0]["repository"],
                   "maintainer": origins[0]["maintainer"]},
        "complete": False,
        "records": records,
        "evidence": evidence,
    }
    if args.output.exists():
        previous = json.loads(args.output.read_bytes())
        if (previous.get("revision") == output["revision"]
                and previous.get("issuer") == output["issuer"]
                and previous.get("records") == list(records)):
            return
        raise ValueError("O caminho já contém outro inventário. Preserve o recibo anterior.")
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
