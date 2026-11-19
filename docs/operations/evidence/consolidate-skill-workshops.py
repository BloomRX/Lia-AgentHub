"""Consolidate trusted local rollout databases into a new, verified workshop."""

import argparse
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from lia_agenthub.adapters.skill_workshop import SkillWorkshop
from lia_agenthub.domain.integrity import sha256_bytes, tree_hash

TABLES = {
    "drafts": "id, generation, text",
    "revisions": "id, revision, generation, digest, text, created_at",
    "draft_files": "id, path, data",
    "revision_files": "id, revision, path, data",
    "revision_trees": "id, revision, digest",
    "origins": "id, evidence",
}


def load_pins(inputs: list[tuple[Path, list[Path]]]) -> dict:
    pins = {}
    for _, files in inputs:
        for path in files:
            pin = json.loads(path.read_bytes())
            if pin["lockVersion"] != 1 or not pin["skillId"].startswith("urn:lia:cap:"):
                raise ValueError(f"Manifesto de consumo inválido: {path.name}")
            identity = pin["skillId"].removeprefix("urn:lia:cap:")
            if identity in pins:
                raise ValueError(f"Identidade repetida: {identity}")
            pins[identity] = pin
    return pins


def consolidate(destination: Path, inputs: list[tuple[Path, list[Path]]]) -> int:
    pins = load_pins(inputs)
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".lia-consolidate-", dir=destination.parent) as folder:
        staged = Path(folder) / "skills.sqlite3"
        workshop = SkillWorkshop(staged)
        workshop.list_skills()  # Initialize the current schema without copying SQL.
        with closing(sqlite3.connect(staged)) as target, target:
            for path, _ in inputs:
                uri = f"{path.resolve().as_uri()}?mode=ro"
                with closing(sqlite3.connect(uri, uri=True)) as source:
                    source.execute("PRAGMA trusted_schema = OFF")
                    source.execute("BEGIN")
                    for table, columns in TABLES.items():
                        slots = ", ".join("?" for _ in columns.split(","))
                        rows = source.execute(f"SELECT {columns} FROM {table}")
                        target.executemany(f"INSERT INTO {table} ({columns}) VALUES ({slots})", rows)

        records = workshop.list_skills()
        if {record["id"] for record in records} != pins.keys():
            raise ValueError("Identidades da oficina divergem dos manifestos fixados.")
        for record in records:
            pin = pins[record["id"]]
            if record["latestRevision"] != pin["revision"] or not record["origin"]:
                raise ValueError(f"Revisão ou procedência divergente: {record['id']}")
            files = workshop.payload(record["id"], pin["revision"])
            digest = tree_hash({name: sha256_bytes(data) for name, data in files.items()})
            if digest != pin["treeSha256"]:
                raise ValueError(f"Árvore divergente: {record['id']}")
        # Publica sem sobrescrever uma base criada no destino durante a operação.
        os.link(staged, destination.resolve())
    return len(pins)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--source", action="append", required=True, nargs="+", type=Path,
                        metavar="DB [LOCK ...]")
    args = parser.parse_args()
    inputs = [(db, pins) for db, *pins in args.source]
    if any(not pins for _, pins in inputs):
        parser.error("cada base precisa de pelo menos um manifesto")
    print(f"Revisões verificadas na oficina: {consolidate(args.destination, inputs)}")


if __name__ == "__main__":
    main()
