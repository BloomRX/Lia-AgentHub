"""Local Skill drafts and immutable revisions, without loading their content."""
from __future__ import annotations

import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from uuid import UUID, uuid4

from ..domain.integrity import sha256_bytes
from ..domain.skills import check_references, diff_corpo, diff_frontmatter, has_blocking, validate_skill
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
                yield connection

    def create(self, text: str) -> dict:
        skill_id = str(uuid4())
        with self._connect() as connection:
            connection.execute("INSERT INTO drafts VALUES (?, 1, ?)", (skill_id, text))
        return {"id": skill_id, "generation": 1}

    def _draft(self, connection, skill_id: str) -> dict:
        row = connection.execute(
            "SELECT * FROM drafts WHERE id = ?", (str(UUID(skill_id)),)
        ).fetchone()
        if row is None:
            raise WorkshopError("Rascunho desconhecido.")
        return dict(row)

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

    def edit(self, skill_id: str, generation: int, text: str) -> dict:
        with self._connect() as connection:
            return self._replace(connection, skill_id, generation, text)

    @staticmethod
    def validate(text: str) -> dict:
        issues = validate_skill(text) + check_references(text, {"SKILL.md"})
        unicode_report = scan(text, context=Context.PROSE)
        return {
            "ok": not has_blocking(issues) and not unicode_report.rejected,
            "issues": [issue.as_dict() for issue in issues],
            "unicode": [finding.as_dict() for finding in unicode_report.findings],
        }

    def preview(self, skill_id: str) -> dict:
        with self._connect() as connection:
            draft = self._draft(connection, skill_id)
        return {**draft, "validation": self.validate(draft["text"])}

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
        return result

    def publish(self, skill_id: str, generation: int) -> dict:
        skill_id = str(UUID(skill_id))
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            draft = self._draft(connection, skill_id)
            if draft["generation"] != generation:
                raise WorkshopError(f"Rascunho mudou. Geração atual: {draft['generation']}.")
            text = draft["text"]
            if not self.validate(text)["ok"]:
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
            return self._revision(connection, skill_id, revision)

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
            base = self._revision(connection, skill_id, revision)["text"]
            draft = self._draft(connection, skill_id)["text"]
        return {"frontmatter": diff_frontmatter(base, draft), "body": diff_corpo(base, draft)}

    def restore(self, skill_id: str, generation: int, revision: int) -> dict:
        with self._connect() as connection:
            text = self._revision(connection, skill_id, revision)["text"]
            return self._replace(connection, skill_id, generation, text)

    def read_revision(self, skill_id: str, revision: int) -> dict:
        with self._connect() as connection:
            return self._revision(connection, skill_id, revision)
