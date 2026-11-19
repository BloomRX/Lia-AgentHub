"""Annotate the Project inventory from pinned Git blobs and historical research."""

import argparse
import base64
import csv
import hashlib
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from lia_agenthub.domain.integrity import sha256_bytes
from lia_agenthub.domain.skills import parse_frontmatter

RESEARCH = "BloomRX/Lia-Research"
RESEARCH_REVISION = "33074e280cb557ac23537eac9a6883a0b89d0283"
RESEARCH_PATH = "data/inventory/skills-provenance.tsv"
REPOSITORY = "BloomRX/Lia-Project"


def fetch(endpoint: str) -> bytes:
    result = subprocess.run(["gh", "api", endpoint, "--jq", ".content"],
                            check=True, capture_output=True)
    return base64.b64decode(result.stdout)


def historical_records() -> dict:
    location = f"repos/{RESEARCH}/contents/{RESEARCH_PATH}?ref={RESEARCH_REVISION}"
    lines = (line for line in io.StringIO(fetch(location).decode("utf-8"))
             if not line.startswith("#") and line.strip())
    return {(row["grupo"], row["skill"]): row for row in csv.DictReader(lines, delimiter="\t")}


def annotate(item: dict, historical: dict, commit: str, history_url: str) -> None:
    path = item["origins"][0]["path"]
    pin = item["integrity"][0]["digest"]
    content = fetch(f"repos/{REPOSITORY}/git/blobs/{pin}")
    if hashlib.sha1(f"blob {len(content)}\0".encode("ascii") + content).hexdigest() != pin:
        raise ValueError(f"Blob divergente: {path}")
    parsed = parse_frontmatter(content.decode("utf-8"))
    metadata = parsed.frontmatter
    candidate = historical.get(("airi" if path.startswith("airi/") else "root", item["name"]))
    item["revisionId"] = f"{commit}-component-evidence-1"
    item["license"]["declared"] = metadata.get("license")
    item["origins"][0]["author"] = metadata.get("metadata.author") or metadata.get("author")
    item["integrity"].append({"algorithm": "sha256", "scope": "source-skill-md",
                              "digest": sha256_bytes(content), "evidenceIds": ["project-tree"]})
    item["details"]["licenseReview"] = {
        "state": "declaration-observed" if item["license"]["declared"] else "scope-unresolved",
        "source": "frontmatter",
        "nestedRepositoryLicense": "airi/LICENSE" if path.startswith("airi/") else None,
    }
    if candidate:
        item["details"]["historicalProvenance"] = {
            "record": "LR-LIC-003",
            "locator": history_url,
            "name": candidate["skill"],
            "scope": "historical-name-match-only",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    feed = json.loads(args.inventory.read_bytes())
    commit = feed["revision"]
    historical = historical_records()
    history_url = f"https://github.com/{RESEARCH}/blob/{RESEARCH_REVISION}/{RESEARCH_PATH}"
    # Alethe already has richer component-level evidence in its own receipt.
    records = [item for item in feed["records"] if item["origins"][0]["path"] != ".agents/skills/alethe/SKILL.md"]
    for item in records:
        annotate(item, historical, commit, history_url)
    feed.update(inventoryId="lia-project-skill-component-evidence",
                revision=f"{commit}-component-evidence-1",
                generatedAt=datetime.now(timezone.utc).isoformat(), complete=False, records=records)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(feed, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
