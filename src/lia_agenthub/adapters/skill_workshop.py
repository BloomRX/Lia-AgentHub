"""Local Skill drafts and immutable revisions, without loading their content."""
from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from ..domain.integrity import sha256_bytes, tree_hash
from ..domain.paths import validate_relative
from ..domain.skills import check_references, diff_corpo, diff_frontmatter, has_blocking, parse_frontmatter, validate_skill
from ..domain.unicode_policy import Context, scan


class WorkshopError(ValueError):
    pass


class SkillWorkshop:
    def __init__(self, database: Path):
        self.database = database

    @contextmanager
    def _connect(self):
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.database)) as connection:
            connection.row_factory = sqlite3.Row
            with connection:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS drafts (
                        id TEXT PRIMARY KEY, generation INTEGER NOT NULL, text TEXT NOT NULL
                    )
                """)
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS revisions (
                        id TEXT NOT NULL, revision INTEGER NOT NULL, generation INTEGER NOT NULL,
                        digest TEXT NOT NULL, text TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (id, revision), UNIQUE (id, generation)
                    )
                """)
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS draft_files (
                        id TEXT NOT NULL, path TEXT NOT NULL, data BLOB NOT NULL,
                        PRIMARY KEY (id, path)
                    )
                """)
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS revision_files (
                        id TEXT NOT NULL, revision INTEGER NOT NULL, path TEXT NOT NULL,
                        data BLOB NOT NULL, PRIMARY KEY (id, revision, path)
                    )
                """)
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS revision_trees (
                        id TEXT NOT NULL, revision INTEGER NOT NULL, digest TEXT NOT NULL,
                        PRIMARY KEY (id, revision)
                    )
                """)
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS origins (
                        id TEXT PRIMARY KEY, evidence TEXT NOT NULL
                    )
                """)
                yield connection

    @classmethod
    def _validate_origin(cls, origin: dict, text: str, files: dict[str, bytes]) -> dict:
        fields = {"repository", "commit", "path", "author", "maintainer",
                  "licensePath", "licenseSha256", "treeSha256"}
        if not isinstance(origin, dict) or fields != origin.keys():
            raise WorkshopError("A procedência precisa declarar os campos do snapshot Git.")
        for field in fields - {"author", "maintainer"}:
            if not isinstance(origin[field], str) or not origin[field]:
                raise WorkshopError(f"Procedência inválida: {field}.")
        for field in ("author", "maintainer"):
            value = origin[field]
            if value is not None and (not isinstance(value, str) or not value.strip()
                                      or len(value) > 300 or any(ord(c) < 32 for c in value)):
                raise WorkshopError(f"Procedência inválida: {field}.")
        url = urlsplit(origin["repository"])
        if (url.scheme != "https" or not url.hostname or url.username is not None
                or url.query or url.fragment or not re.fullmatch(r"/[\w.-]+/[\w.-]+/?", url.path)):
            raise WorkshopError("URL de repositório inválida.")
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", origin["commit"]):
            raise WorkshopError("Informe o commit Git completo.")
        for field in ("path", "licensePath"):
            if validate_relative(origin[field]).posix != origin[field]:
                raise WorkshopError(f"Caminho de origem inválido: {field}.")
        if not re.fullmatch(r"[0-9a-f]{64}", origin["licenseSha256"]):
            raise WorkshopError("SHA-256 da evidência de licença inválido.")
        if cls._tree_hash(text, files) != origin["treeSha256"]:
            raise WorkshopError("A pasta não confere com o hash de origem.")
        return {"kind": "git-snapshot", **origin}

    def create(self, text: str, files: dict[str, bytes] | None = None,
               origin: dict | None = None) -> dict:
        attachments = files or {}
        evidence = self._validate_origin(origin, text, attachments) if origin is not None else None
        with self._connect() as connection:
            return self._insert_draft(connection, text, attachments, evidence)

    def _insert_draft(self, connection, text: str, files: dict[str, bytes],
                      origin: dict | None) -> dict:
        skill_id = str(uuid4())
        connection.execute("INSERT INTO drafts VALUES (?, 1, ?)", (skill_id, text))
        self._save_files(connection, skill_id, files)
        if origin is not None:
            connection.execute("INSERT INTO origins VALUES (?, ?)",
                               (skill_id, json.dumps(origin, ensure_ascii=False)))
        return {"id": skill_id, "generation": 1}

    def fork(self, skill_id: str, revision: int, copy_basis_sha256: str) -> dict:
        if not re.fullmatch(r"[0-9a-f]{64}", copy_basis_sha256):
            raise WorkshopError("Informe a evidência de autorização de cópia.")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            source = self._revision(connection, skill_id, revision)
            files = self._revision_files(connection, source)
            origin = {
                "kind": "workshop-fork",
                "parentSkillId": f"urn:lia:cap:{source['id']}",
                "parentRevision": source["revision"],
                "parentTreeSha256": self._tree_hash(source["text"], files),
                "copyBasisSha256": copy_basis_sha256,
                "parentOrigin": source["origin"],
            }
            return self._insert_draft(connection, source["text"], files, origin)

    def _draft(self, connection, skill_id: str) -> dict:
        row = connection.execute(
            "SELECT * FROM drafts WHERE id = ?", (str(UUID(skill_id)),)
        ).fetchone()
        if row is None:
            raise WorkshopError("Rascunho desconhecido.")
        return {**dict(row), "origin": self._origin(connection, str(UUID(skill_id)))}

    @staticmethod
    def _origin(connection, skill_id: str) -> dict | None:
        row = connection.execute(
            "SELECT evidence FROM origins WHERE id = ?", (skill_id,)
        ).fetchone()
        return json.loads(row["evidence"]) if row else None

    def _save_files(self, connection, skill_id: str, files: dict[str, bytes]) -> None:
        connection.execute("DELETE FROM draft_files WHERE id = ?", (skill_id,))
        connection.executemany("INSERT INTO draft_files VALUES (?, ?, ?)",
                               ((skill_id, path, data) for path, data in files.items()))

    def _draft_files(self, connection, skill_id: str) -> dict[str, bytes]:
        return dict(connection.execute(
            "SELECT path, data FROM draft_files WHERE id = ?", (skill_id,)
        ).fetchall())

    def _revision_files(self, connection, record: dict) -> dict[str, bytes]:
        key = (record["id"], record["revision"])
        files = dict(connection.execute(
            "SELECT path, data FROM revision_files WHERE id = ? AND revision = ?", key
        ).fetchall())
        digest = connection.execute(
            "SELECT digest FROM revision_trees WHERE id = ? AND revision = ?", key
        ).fetchone()
        observed = self._tree_hash(record["text"], files)
        if (digest is None and files) or (digest is not None and digest["digest"] != observed):
            raise WorkshopError("A árvore da revisão não confere.")
        return files

    @staticmethod
    def _tree_hash(text: str, files: dict[str, bytes]) -> str:
        entries = {path: sha256_bytes(data) for path, data in files.items()}
        entries["SKILL.md"] = sha256_bytes(text.encode("utf-8"))
        return tree_hash(entries)

    def _replace(self, connection, skill_id: str, generation: int, text: str) -> dict:
        result = connection.execute(
            "UPDATE drafts SET generation = generation + 1, text = ? "
            "WHERE id = ? AND generation = ?",
            (text, str(UUID(skill_id)), generation),
        )
        if result.rowcount != 1:
            current = self._draft(connection, skill_id)
            raise WorkshopError(f"Rascunho mudou. Geração atual: {current['generation']}.")
        return {"id": skill_id, "generation": generation + 1}

    def edit(self, skill_id: str, generation: int, text: str,
             files: dict[str, bytes] | None = None) -> dict:
        skill_id = str(UUID(skill_id))
        with self._connect() as connection:
            updated = self._replace(connection, skill_id, generation, text)
            if files is not None:
                self._save_files(connection, skill_id, files)
            return updated

    @staticmethod
    def validate(text: str, paths=()) -> dict:
        issues = validate_skill(text) + check_references(text, {"SKILL.md", *paths})
        unicode_report = scan(text, context=Context.PROSE)
        return {
            "ok": not has_blocking(issues) and not unicode_report.rejected,
            "issues": [issue.as_dict() for issue in issues],
            "unicode": [finding.as_dict() for finding in unicode_report.findings],
        }

    def preview(self, skill_id: str) -> dict:
        with self._connect() as connection:
            connection.execute("BEGIN")
            draft = self._draft(connection, skill_id)
            paths = sorted(self._draft_files(connection, draft["id"]))
        return {**draft, "files": paths, "validation": self.validate(draft["text"], paths)}

    def _revision(self, connection, skill_id: str, revision: int) -> dict:
        row = connection.execute(
            "SELECT * FROM revisions WHERE id = ? AND revision = ?",
            (str(UUID(skill_id)), revision),
        ).fetchone()
        if row is None:
            raise WorkshopError("Revisão desconhecida.")
        result = dict(row)
        if sha256_bytes(result["text"].encode("utf-8")) != result["digest"]:
            raise WorkshopError("A integridade da revisão não confere.")
        return {**result, "origin": self._origin(connection, result["id"])}

    def publish(self, skill_id: str, generation: int) -> dict:
        skill_id = str(UUID(skill_id))
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            draft = self._draft(connection, skill_id)
            if draft["generation"] != generation:
                raise WorkshopError(f"Rascunho mudou. Geração atual: {draft['generation']}.")
            text = draft["text"]
            files = self._draft_files(connection, skill_id)
            if not self.validate(text, files)["ok"]:
                raise WorkshopError("Rascunho inválido. Use preview para ver os achados.")
            previous = connection.execute(
                "SELECT revision FROM revisions WHERE id = ? AND generation = ?",
                (skill_id, generation),
            ).fetchone()
            if previous is not None:
                return self._revision(connection, skill_id, previous["revision"])
            revision = connection.execute(
                "SELECT COALESCE(MAX(revision), 0) + 1 FROM revisions WHERE id = ?",
                (skill_id,),
            ).fetchone()[0]
            connection.execute(
                "INSERT INTO revisions (id, revision, generation, digest, text) VALUES (?, ?, ?, ?, ?)",
                (skill_id, revision, generation, sha256_bytes(text.encode("utf-8")), text),
            )
            connection.executemany(
                "INSERT INTO revision_files VALUES (?, ?, ?, ?)",
                ((skill_id, revision, path, data) for path, data in files.items()),
            )
            connection.execute("INSERT INTO revision_trees VALUES (?, ?, ?)",
                               (skill_id, revision, self._tree_hash(text, files)))
            return self._revision(connection, skill_id, revision)

    def list_skills(self) -> list[dict]:
        with self._connect() as connection:
            connection.execute("BEGIN")
            rows = connection.execute("""
                SELECT drafts.id, drafts.generation, drafts.text, origins.evidence,
                       (SELECT MAX(revision) FROM revisions WHERE revisions.id = drafts.id)
                       AS latest_revision
                FROM drafts LEFT JOIN origins ON origins.id = drafts.id
                ORDER BY drafts.id
            """).fetchall()
        return [{
            "id": row["id"],
            "generation": row["generation"],
            "name": parse_frontmatter(row["text"]).frontmatter.get("name"),
            "latestRevision": row["latest_revision"],
            "origin": json.loads(row["evidence"]) if row["evidence"] else None,
        } for row in rows]

    def history(self, skill_id: str) -> list[dict]:
        skill_id = str(UUID(skill_id))
        with self._connect() as connection:
            self._draft(connection, skill_id)
            return [dict(row) for row in connection.execute(
                "SELECT revision, generation, digest, created_at FROM revisions "
                "WHERE id = ? ORDER BY revision DESC", (skill_id,),
            )]

    def diff(self, skill_id: str, revision: int) -> dict:
        with self._connect() as connection:
            connection.execute("BEGIN")
            record = self._revision(connection, skill_id, revision)
            base = record["text"]
            draft = self._draft(connection, skill_id)["text"]
            before = self._revision_files(connection, record)
            after = self._draft_files(connection, record["id"])
        paths = before.keys() | after.keys()
        changes = {path: ("added" if path not in before else
                          "removed" if path not in after else "changed")
                   for path in sorted(paths) if before.get(path) != after.get(path)}
        return {"frontmatter": diff_frontmatter(base, draft), "body": diff_corpo(base, draft),
                "files": changes}

    def restore(self, skill_id: str, generation: int, revision: int) -> dict:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            record = self._revision(connection, skill_id, revision)
            files = self._revision_files(connection, record)
            updated = self._replace(connection, skill_id, generation, record["text"])
            self._save_files(connection, record["id"], files)
            return updated

    def read_revision(self, skill_id: str, revision: int) -> dict:
        with self._connect() as connection:
            return self._revision(connection, skill_id, revision)

    def payload(self, skill_id: str, revision: int) -> dict[str, bytes]:
        with self._connect() as connection:
            connection.execute("BEGIN")
            record = self._revision(connection, skill_id, revision)
            files = self._revision_files(connection, record)
            return {"SKILL.md": record["text"].encode("utf-8"), **files}
