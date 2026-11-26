"""Exercise the external execution protocol through separate CLI processes."""

import json
import subprocess
import sys

import pytest

from lia_agenthub.adapters import supervised_execution as execution


def invoke(root, *args, payload=None):
    completed = subprocess.run(
        [sys.executable, "-m", "lia_agenthub", "--home", str(root), "execution", *args],
        input=json.dumps(payload).encode("utf-8") if payload is not None else b"",
        capture_output=True, timeout=15, check=False,
    )
    assert not completed.stderr, completed.stderr
    response = json.loads(completed.stdout)
    assert response["schemaVersion"] == 1
    assert completed.returncode == (0 if response["ok"] else 1)
    return response


def test_external_execution_validate_cancel_and_isolate(tmp_path):
    operator = invoke(tmp_path, "init")["result"]
    admin = {"operatorToken": operator["operatorToken"]}
    token = invoke(tmp_path, "provision", "lia-project", payload=admin)["result"]["token"]
    other = invoke(tmp_path, "provision", "other-host", payload=admin)["result"]["token"]
    assert not invoke(tmp_path, "grant", "lia-project", "--ttl", "60",
                      payload={"operatorToken": token})["ok"]
    assert not invoke(tmp_path, "init")["ok"]

    def call(action, bearer=token, **fields):
        return invoke(tmp_path, "call", payload={
            "schemaVersion": 1, "token": bearer, "action": action, **fields,
        })

    discovery = call("discover")["result"]
    assert discovery["capabilities"][0]["id"] == "skill.validate"
    data = {"requestId": "request-1", "capability": "skill.validate",
            "grantId": "unknown", "context": {
                "text": "---\nname: sample\ndescription: Safe test skill\n---\n\nBody.\n",
            }}
    assert not call("submit", **data)["ok"]
    data["grantId"] = invoke(tmp_path, "grant", "lia-project", "--ttl", "60",
                             payload=admin)["result"]["grantId"]
    queued = call("submit", **data)["result"]
    task = queued["taskId"]
    assert queued["state"] == "queued"
    assert call("submit", **data)["result"]["taskId"] == task
    assert not call("submit", **{**data, "context": {"text": "different"}})["ok"]
    assert not call("status", bearer=other, taskId=task)["ok"]
    assert not call("audit", bearer=other, taskId=task)["ok"]
    done = call("start", taskId=task)["result"]
    assert done["state"] in {"completed", "succeeded"}
    assert isinstance(done["result"], dict)
    assert call("status", taskId=task)["result"] == done
    audit = call("audit", taskId=task)["result"]
    assert len(audit["events"]) >= 3
    assert "Safe test skill" not in json.dumps(audit)

    second = invoke(tmp_path, "grant", "lia-project", "--ttl", "60",
                    payload=admin)["result"]["grantId"]
    cancelled = call("submit", **{**data, "requestId": "request-2", "grantId": second})["result"]
    assert call("cancel", taskId=cancelled["taskId"])["result"]["state"] == "cancelled"
    after = call("start", taskId=cancelled["taskId"])
    assert not after["ok"] or after["result"]["state"] == "cancelled"


def test_unavailable_storage_is_redacted(tmp_path):
    (tmp_path / "SupervisedExecution").touch()
    response = invoke(tmp_path, "call", payload={
        "schemaVersion": 1, "token": "x" * 43, "action": "discover",
    })
    assert response["error"]["code"] == "unavailable"
    assert str(tmp_path) not in response["error"]["message"]


@pytest.fixture
def broker_calls(tmp_path):
    broker = execution.Broker(tmp_path)
    token = broker.provision("lia-project")["token"]

    def call(action, **fields):
        return broker.call({"schemaVersion": 1, "token": token, "action": action, **fields})

    def submit():
        grant = broker.grant("lia-project", 60)
        return call("submit", requestId="example", grantId=grant["grantId"],
                    capability="skill.validate", context={"text": "bound context"})["taskId"]

    return call, submit


def test_expired_grant_cannot_start(broker_calls, monkeypatch):
    call, submit = broker_calls
    time_at_submit = execution.time.time()
    task_id = submit()
    monkeypatch.setattr(execution.time, "time", lambda: time_at_submit + 61)
    task = call("start", taskId=task_id)
    assert task["state"] == "failed"
    assert task["error"] == {"code": "grant-expired"}
    assert task["result"] is None


def test_validator_failure_does_not_expose_details(broker_calls, monkeypatch):
    call, submit = broker_calls

    def failing_validator(_):
        raise RuntimeError("private failure detail")

    monkeypatch.setattr(execution, "validate_skill", failing_validator)
    task_id = submit()
    task = call("start", taskId=task_id)
    assert task["state"] == "failed"
    assert task["error"] == {"code": "execution-failed"}
    assert task["result"] is None
    assert "private failure detail" not in json.dumps(call("events", taskId=task_id))


def test_running_cancel_discards_validator_result(broker_calls, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    call, submit = broker_calls
    running, release = Event(), Event()

    def wait_in_validator(_):
        running.set()
        assert release.wait(5)
        return []

    monkeypatch.setattr(execution, "validate_skill", wait_in_validator)
    task_id = submit()
    with ThreadPoolExecutor(max_workers=1) as pool:
        result = pool.submit(call, "start", taskId=task_id)
        try:
            assert running.wait(5)
            assert call("status", taskId=task_id)["state"] == "running"
            assert call("cancel", taskId=task_id)["state"] == "cancelled"
        finally:
            release.set()
        cancelled = result.result(timeout=5)
    assert cancelled["state"] == "cancelled"
    assert cancelled["result"] is None
    assert [event["state"] for event in call("events", taskId=task_id)["events"]] == [
        "queued", "running", "cancelled",
    ]
