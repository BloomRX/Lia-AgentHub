"""Local execution ledger for the fixed, first-party Skill validator."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import secrets
import sqlite3
import time
import uuid

from ..domain.skills import summarize, validate_skill

CAPABILITY = "skill.validate"
CONTEXT_MAX_BYTES = 65_536
MAX_TTL = 3_600
RUN_TIMEOUT = 30
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
TOKEN = re.compile(r"[A-Za-z0-9_-]{43}")
TERMINAL = {"completed", "failed", "cancelled"}
COMMON_FIELDS = {"schemaVersion", "token", "action"}
TASK_FIELDS = {
    "discover": set(),
    "submit": {"requestId", "grantId", "capability", "context"},
    **{action: {"taskId"} for action in ("start", "status", "events", "cancel", "audit")},
}


class ExecutionError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _bad(message: str):
    return ExecutionError("invalid-request", message)


def _id(value, field: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise _bad(f"Invalid {field}.")
    return value


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _encode(value: str) -> bytes:
    try:
        return value.encode("utf-8")
    except UnicodeError as exc:
        raise _bad("Text must be valid Unicode.") from exc


def _credential_hash(token) -> str:
    if not isinstance(token, str) or not TOKEN.fullmatch(token):
        raise ExecutionError("unauthorized", "Invalid credential.")
    return _sha(token.encode("ascii"))


class Broker:
    def __init__(self, root: Path):
        self.db = Path(root) / "supervised-execution-v1.sqlite3"
        self.db.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with self._transaction() as connection:
            # Individual statements preserve the enclosing transaction.
            for statement in (
                """CREATE TABLE IF NOT EXISTS operator (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1), token_hash TEXT NOT NULL)""",
                """CREATE TABLE IF NOT EXISTS consumers (
                    name TEXT PRIMARY KEY, token_hash TEXT UNIQUE NOT NULL)""",
                """CREATE TABLE IF NOT EXISTS grants (
                    id TEXT PRIMARY KEY, consumer TEXT NOT NULL REFERENCES consumers(name),
                    expires_at INTEGER NOT NULL)""",
                """CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, consumer TEXT NOT NULL REFERENCES consumers(name),
                    request_id TEXT NOT NULL, fingerprint TEXT NOT NULL,
                    grant_id TEXT UNIQUE NOT NULL REFERENCES grants(id), state TEXT NOT NULL,
                    context TEXT, deadline REAL, result TEXT, error TEXT,
                    UNIQUE(consumer, request_id))""",
                """CREATE TABLE IF NOT EXISTS events (
                    task_id TEXT NOT NULL REFERENCES tasks(id), sequence INTEGER NOT NULL,
                    state TEXT NOT NULL, at INTEGER NOT NULL, code TEXT,
                    PRIMARY KEY(task_id, sequence))""",
            ):
                connection.execute(statement)

    @contextmanager
    def _transaction(self):
        connection = sqlite3.connect(self.db, timeout=5, isolation_level=None)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA secure_delete=ON")
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> dict:
        """Explicit first-use bootstrap. Never called from the consumer protocol."""
        token = secrets.token_urlsafe(32)
        with self._transaction() as db:
            if db.execute("SELECT 1 FROM operator").fetchone():
                raise ExecutionError("conflict", "Operator already initialized.")
            db.execute("INSERT INTO operator VALUES (1, ?)", (_credential_hash(token),))
        return {"operatorToken": token}

    def authorize_operator(self, token: str) -> None:
        digest = _credential_hash(token)
        with self._transaction() as db:
            row = db.execute("SELECT token_hash FROM operator WHERE singleton=1").fetchone()
            if row is None or not secrets.compare_digest(row["token_hash"], digest):
                raise ExecutionError("unauthorized", "Invalid operator credential.")

    def provision(self, consumer: str) -> dict:
        consumer = _id(consumer, "consumer")
        token = secrets.token_urlsafe(32)
        with self._transaction() as db:
            if db.execute("SELECT 1 FROM consumers WHERE name=?", (consumer,)).fetchone():
                raise ExecutionError("conflict", "Consumer already provisioned.")
            db.execute("INSERT INTO consumers VALUES (?, ?)", (consumer, _credential_hash(token)))
        return {"consumer": consumer, "token": token}

    def grant(self, consumer: str, ttl: int) -> dict:
        consumer = _id(consumer, "consumer")
        if type(ttl) is not int or not 1 <= ttl <= MAX_TTL:
            raise _bad(f"TTL must be between 1 and {MAX_TTL} seconds.")
        grant_id = uuid.uuid4().hex
        with self._transaction() as db:
            if not db.execute("SELECT 1 FROM consumers WHERE name=?", (consumer,)).fetchone():
                raise ExecutionError("not-found", "Consumer not found.")
            expiry = int(time.time()) + ttl
            db.execute("INSERT INTO grants VALUES (?, ?, ?)", (grant_id, consumer, expiry))
        return {"grantId": grant_id, "consumer": consumer, "capability": CAPABILITY,
                "expiresAt": expiry}

    def call(self, request: dict) -> dict:
        if not isinstance(request, dict) or type(request.get("schemaVersion")) is not int or request["schemaVersion"] != 1:
            raise _bad("Expected a schemaVersion 1 request.")
        action = request.get("action")
        if not isinstance(action, str) or action not in TASK_FIELDS:
            raise _bad("Unknown action.")
        if set(request) != COMMON_FIELDS | TASK_FIELDS[action]:
            raise _bad("Unexpected or missing request fields.")
        digest = _credential_hash(request["token"])
        with self._transaction() as db:
            row = db.execute("SELECT name FROM consumers WHERE token_hash=?",
                             (digest,)).fetchone()
            if row is None:
                raise ExecutionError("unauthorized", "Invalid consumer credential.")
            consumer = row["name"]
            self._expire_queue(db, consumer)
            if action == "discover":
                return {"capabilities": [{
                    "id": CAPABILITY, "revision": 1, "contextMaxBytes": CONTEXT_MAX_BYTES,
                    "permission": CAPABILITY, "grantRequired": True,
                }]}
            if action == "submit":
                return self._submit(db, consumer, request)
            task_id = _id(request["taskId"], "taskId")
            task = self._load(db, consumer, task_id)
            if action in {"events", "audit"}:
                events = db.execute(
                    "SELECT sequence,state,at,code FROM events WHERE task_id=? ORDER BY sequence",
                    (task_id,),
                )
                return {"taskId": task_id, "events": [dict(event) for event in events]}
            if action == "status":
                return self._view(task)
            if action == "cancel":
                if task["state"] not in TERMINAL:
                    self._transition(db, task_id, "cancelled", code="cancelled")
                return self._view(self._load(db, consumer, task_id))
            if task["state"] != "queued":
                return self._view(task)
            try:
                expiry = self._authorize(db, consumer, task["grant_id"])
            except ExecutionError:
                self._transition(db, task_id, "failed", code="grant-expired")
                return self._view(self._load(db, consumer, task_id))
            context = task["context"]
            self._transition(db, task_id, "running", deadline=min(time.time() + RUN_TIMEOUT, expiry))
        return self._run(consumer, task_id, context)

    @staticmethod
    def _authorize(db, consumer, grant_id):
        grant = db.execute("SELECT expires_at FROM grants WHERE id=? AND consumer=?",
                           (grant_id, consumer)).fetchone()
        if grant is None or grant["expires_at"] <= time.time():
            raise ExecutionError("forbidden", "Grant is missing, expired or outside consumer scope.")
        return grant["expires_at"]

    def _expire_queue(self, db, consumer):
        expired = db.execute(
            """SELECT tasks.id FROM tasks JOIN grants ON grants.id=tasks.grant_id
               WHERE tasks.consumer=? AND tasks.state='queued' AND grants.expires_at<=?""",
            (consumer, time.time()),
        ).fetchall()
        for task in expired:
            self._transition(db, task["id"], "failed", code="grant-expired")

    def _submit(self, db, consumer, request):
        request_id = _id(request["requestId"], "requestId")
        grant_id = _id(request["grantId"], "grantId")
        if request["capability"] != CAPABILITY:
            raise ExecutionError("unavailable", "Capability is unavailable for execution.")
        context = request["context"]
        if not isinstance(context, dict) or set(context) != {"text"} or not isinstance(context["text"], str):
            raise _bad("Expected context.text only.")
        text = context["text"]
        content = _encode(text)
        if not content or len(content) > CONTEXT_MAX_BYTES:
            raise _bad(f"Text must contain 1–{CONTEXT_MAX_BYTES} UTF-8 bytes.")
        fingerprint = _sha(grant_id.encode() + b"\0" + content)
        existing = db.execute("SELECT id,fingerprint FROM tasks WHERE consumer=? AND request_id=?",
                              (consumer, request_id)).fetchone()
        if existing is not None:
            if existing["fingerprint"] != fingerprint:
                raise ExecutionError("conflict", "Request ID is already bound to different inputs.")
            return self._view(self._load(db, consumer, existing["id"]))
        self._authorize(db, consumer, grant_id)
        if db.execute("SELECT 1 FROM tasks WHERE grant_id=?", (grant_id,)).fetchone():
            raise ExecutionError("forbidden", "Grant already used.")
        task_id = uuid.uuid4().hex
        db.execute(
            """INSERT INTO tasks (id,consumer,request_id,fingerprint,grant_id,state,context)
               VALUES (?,?,?,?,?,'queued',?)""",
            (task_id, consumer, request_id, fingerprint, grant_id, text),
        )
        self._event(db, task_id, "queued")
        return self._view(self._load(db, consumer, task_id))

    def _load(self, db, consumer, task_id):
        query = "SELECT * FROM tasks WHERE id=? AND consumer=?"
        task = db.execute(query, (task_id, consumer)).fetchone()
        if task is None:
            raise ExecutionError("not-found", "Task not found.")
        if task["state"] == "running" and task["deadline"] <= time.time():
            self._transition(db, task_id, "failed", code="execution-timeout")
            task = db.execute(query, (task_id, consumer)).fetchone()
        return task

    @staticmethod
    def _event(db, task_id, state, code=None):
        db.execute(
            """INSERT INTO events
               SELECT ?, COALESCE(MAX(sequence), 0) + 1, ?, ?, ? FROM events WHERE task_id=?""",
            (task_id, state, int(time.time()), code, task_id),
        )

    def _transition(self, db, task_id, state, *, code=None, deadline=None, result=None):
        db.execute(
            "UPDATE tasks SET state=?, context=NULL, deadline=?, result=?, error=? WHERE id=?",
            (state, deadline, result, code, task_id),
        )
        self._event(db, task_id, state, code)

    @staticmethod
    def _view(task):
        state = task["state"]
        return {
            "taskId": task["id"], "requestId": task["request_id"], "capability": CAPABILITY,
            "state": state, "progress": 100 if state in TERMINAL else 0,
            "result": json.loads(task["result"]) if task["result"] is not None else None,
            "error": {"code": task["error"]} if task["error"] else None,
        }

    def _run(self, consumer, task_id, text):
        try:
            issues = validate_skill(text)
            result = json.dumps({"counts": summarize(issues)}, sort_keys=True)
            state, code = "completed", None
        except Exception:
            result = None
            state, code = "failed", "execution-failed"
        with self._transaction() as db:
            task = self._load(db, consumer, task_id)
            if task["state"] == "running":
                self._transition(db, task_id, state, code=code, result=result)
            return self._view(self._load(db, consumer, task_id))
