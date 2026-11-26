"""Run a real first-party Skill validation in a fresh, disposable Hub home."""

import argparse
import json
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", help="Absolute path to LiaAgentHubCli.exe")
    args = parser.parse_args()
    executable = [args.cli] if args.cli else [sys.executable, "-m", "lia_agenthub"]

    with tempfile.TemporaryDirectory(prefix="lia-execution-demo-") as home:
        def invoke(*command, payload=None):
            raw = b"" if payload is None else json.dumps(payload).encode("utf-8")
            process = subprocess.run(
                [*executable, "--home", home, "execution", *command],
                input=raw, capture_output=True, timeout=30, check=False,
            )
            response = json.loads(process.stdout)
            if process.returncode != 0 or not response["ok"]:
                raise SystemExit(response.get("error", {}).get("code", "execution_failed"))
            return response["result"]

        operator = {"operatorToken": invoke("init")["operatorToken"]}
        token = invoke("provision", "lia-project", payload=operator)["token"]

        def call(action, **parameters):
            return invoke("call", payload={
                "schemaVersion": 1, "token": token, "action": action, **parameters,
            })

        print(json.dumps(call("discover"), indent=2))
        grant = invoke("grant", "lia-project", "--ttl", "60", payload=operator)
        task = call("submit", requestId="local-demo-1", grantId=grant["grantId"],
                    capability="skill.validate", context={
                        "text": "---\nname: sample\ndescription: Sample Skill\n---\n\nBody.\n",
                    })
        done = call("start", taskId=task["taskId"])
        print(json.dumps(done, indent=2))
        print(json.dumps(call("audit", taskId=task["taskId"]), indent=2))
        if done["state"] not in {"completed", "succeeded"}:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
