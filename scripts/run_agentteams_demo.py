from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx


MATRIX_BASE_URL = "http://127.0.0.1:18080"
MATRIX_HOST = "matrix-local.agentteams.io"
SANDBOX_BASE_URL = "http://127.0.0.1:18100"


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def docker_json(*args: str) -> Any:
    result = subprocess.run(
        ["docker", "exec", "agentteams-controller", "agt", *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


def manager_matrix_token() -> str:
    result = subprocess.run(
        [
            "docker",
            "exec",
            "agentteams-manager",
            "printenv",
            "AGENTTEAMS_MANAGER_MATRIX_TOKEN",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    token = result.stdout.strip()
    if not token:
        raise RuntimeError("Manager Matrix token is unavailable")
    return token


class MatrixClient:
    def __init__(self) -> None:
        self.client = httpx.Client(
            base_url=MATRIX_BASE_URL,
            headers={"Host": MATRIX_HOST},
            timeout=20.0,
        )

    def login(self, username: str, password: str) -> str:
        response = self.client.post(
            "/_matrix/client/v3/login",
            json={
                "type": "m.login.password",
                "identifier": {"type": "m.id.user", "user": username},
                "password": password,
            },
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise RuntimeError("Matrix login returned no access token")
        return token

    def messages(self, token: str, room_id: str, limit: int = 100) -> list[dict[str, Any]]:
        response = self.client.get(
            f"/_matrix/client/v3/rooms/{quote(room_id, safe='')}/messages",
            params={"dir": "b", "limit": limit},
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json().get("chunk", [])

    def send(self, token: str, room_id: str, message: str) -> str:
        txn_id = f"officeops-{time.time_ns()}"
        response = self.client.put(
            f"/_matrix/client/v3/rooms/{quote(room_id, safe='')}/send/m.room.message/{txn_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"msgtype": "m.text", "body": message},
        )
        response.raise_for_status()
        return response.json()["event_id"]


def transcript(events: list[dict[str, Any]], started_ms: int) -> list[dict[str, Any]]:
    rows = []
    for event in reversed(events):
        body = event.get("content", {}).get("body")
        timestamp = int(event.get("origin_server_ts", 0))
        if not body or timestamp < started_ms:
            continue
        rows.append(
            {
                "event_id": event.get("event_id"),
                "timestamp": datetime.fromtimestamp(
                    timestamp / 1000, tz=timezone.utc
                ).isoformat(),
                "sender": event.get("sender"),
                "body": body,
            }
        )
    return rows


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# AgentTeams OfficeOps Account-Lock Demo",
        "",
        f"- Task: `{payload['task_id']}`",
        f"- Started: `{payload['started_at']}`",
        f"- Final sandbox state: `{json.dumps(payload['sandbox_final'], ensure_ascii=False)}`",
        "",
    ]
    for room_name, rows in payload["transcripts"].items():
        lines.extend([f"## {room_name}", ""])
        if not rows:
            lines.extend(["_No task-window messages captured._", ""])
            continue
        for row in rows:
            lines.extend([f"**{row['sender']}**", "", row["body"], ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the real AgentTeams OfficeOps demo")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path.home() / "agentteams-manager.env",
    )
    args = parser.parse_args()

    env = load_env_file(args.env_file)
    username = env.get("AGENTTEAMS_ADMIN_USER", "admin")
    password = env.get("AGENTTEAMS_ADMIN_PASSWORD", "")
    if not password:
        raise RuntimeError("AGENTTEAMS_ADMIN_PASSWORD is missing from env file")

    manager = docker_json("get", "managers", "default", "-o", "json")
    workers = docker_json("get", "workers", "-o", "json")["workers"]
    expected = {
        "officeops-context",
        "officeops-diagnosis",
        "officeops-remediation-verification",
    }
    actual = {worker["name"] for worker in workers if worker["phase"] == "Running"}
    if not expected.issubset(actual):
        raise RuntimeError(f"OfficeOps Workers are not all Running: {sorted(actual)}")

    with httpx.Client(base_url=SANDBOX_BASE_URL, timeout=10.0) as sandbox:
        sandbox.post("/admin/reset").raise_for_status()
        initial = sandbox.get("/users/alice").json()
    if initial["locked"] is not True:
        raise RuntimeError("Sandbox reset did not restore locked=true")

    task_id = f"agentteams-account-lock-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    task = f"""真实企业访问工单 {task_id}：Alice 突然无法访问 Docs。请不要自己执行企业工具，必须严格按以下顺序协调现有 Worker：
1. @officeops-context 使用 employee-context Skill 和 officeops-readonly MCP 收集身份、VPN、Docs 权限、服务健康、功能访问五类新鲜证据，并回传结构化结果。
2. 收到证据后，必须把 Context Worker 返回的完整 JSON 原样内联到给 @officeops-diagnosis 的 Matrix 消息里，不能只说“已收集”或引用文件；等待它亲自输出 root_cause、confidence、recommended_action，禁止你代替它推断。
3. 仅当 Diagnosis Worker 的实际回复为 root_cause=account_locked 且 recommended_action=unlock_account 时，才委派 @officeops-remediation-verification；把诊断 JSON 内联到消息，由它使用 task_id 作为幂等键调用解锁工具，然后重新读取 identity.locked 并重新探测 Docs accessible。工具 success=true 不是任务成功。
4. 若验证失败最多再尝试一次，否则 fail closed。中风险账号解锁按当前策略允许自动执行。
5. 本次演示只用现有 Matrix 房间直接委派和回传结构化 JSON；禁止使用 taskflow、ack_task、meta.json、spec.md 或共享文件提交，不得虚构工具结果。
完成后在本 DM 只给最终总结；第一行必须恰好为 OFFICEOPS_DONE，后续列出最终状态、根因、工具确认值、验证观测值以及三个 Worker 的贡献。任何进度消息中都不要出现该标记。"""

    matrix = MatrixClient()
    admin_token = matrix.login(username, password)
    room_id = manager["roomID"]
    baseline_ids = {
        event.get("event_id") for event in matrix.messages(admin_token, room_id, 30)
    }
    started_ms = int(time.time() * 1000) - 1000
    matrix.send(admin_token, room_id, task)
    print(f"Sent {task_id} to OfficeOps Manager.", flush=True)

    deadline = time.monotonic() + args.timeout
    final_reply = ""
    last_progress = 0
    while time.monotonic() < deadline:
        time.sleep(5)
        events = matrix.messages(admin_token, room_id, 50)
        new_manager_messages = [
            event.get("content", {}).get("body", "")
            for event in events
            if event.get("sender", "").startswith("@manager:")
            and event.get("event_id") not in baseline_ids
        ]
        final_reply = next(
            (
                body
                for body in new_manager_messages
                if body.lstrip().startswith("OFFICEOPS_DONE")
            ),
            "",
        )
        if final_reply:
            break
        elapsed = args.timeout - int(deadline - time.monotonic())
        if elapsed - last_progress >= 15:
            print(f"Waiting for coordinated result... {elapsed}s", flush=True)
            last_progress = elapsed

    manager_token = manager_matrix_token()
    transcripts = {
        "admin-manager": transcript(
            matrix.messages(admin_token, room_id, 100), started_ms
        )
    }
    for worker in workers:
        transcripts[f"manager-{worker['name']}"] = transcript(
            matrix.messages(manager_token, worker["roomID"], 100), started_ms
        )

    with httpx.Client(base_url=SANDBOX_BASE_URL, timeout=10.0) as sandbox:
        sandbox_final = {
            "identity": sandbox.get("/users/alice").json(),
            "access": sandbox.get("/apps/docs/access/alice").json(),
        }

    payload = {
        "task_id": task_id,
        "started_at": datetime.fromtimestamp(
            started_ms / 1000, tz=timezone.utc
        ).isoformat(),
        "manager_final_reply": final_reply,
        "sandbox_initial": initial,
        "sandbox_final": sandbox_final,
        "resources": {"manager": manager, "workers": workers},
        "transcripts": transcripts,
    }

    context_results = [
        row
        for row in transcripts["manager-officeops-context"]
        if row["sender"].startswith("@officeops-context:")
        and "get_employee_identity" in row["body"]
        and "check_application_access" in row["body"]
        and "locked" in row["body"]
    ]
    diagnosis_results = [
        row
        for row in transcripts["manager-officeops-diagnosis"]
        if row["sender"].startswith("@officeops-diagnosis:")
        and "BLOCKED" not in row["body"]
        and "root_cause" in row["body"]
        and "recommended_action" in row["body"]
    ]
    remediation_results = [
        row
        for row in transcripts["manager-officeops-remediation-verification"]
        if row["sender"].startswith("@officeops-remediation-verification:")
        and "verification_identity_locked" in row["body"]
        and "verification_docs_accessible" in row["body"]
    ]
    protocol_checks = {
        "context_worker_returned_tool_evidence": bool(context_results),
        "diagnosis_worker_returned_result": bool(diagnosis_results),
        "remediation_worker_returned_verification": bool(remediation_results),
        "diagnosis_preceded_remediation": bool(
            diagnosis_results
            and remediation_results
            and diagnosis_results[-1]["timestamp"] < remediation_results[-1]["timestamp"]
        ),
    }
    payload["protocol_checks"] = protocol_checks
    output_dir = Path("artifacts") / "agentteams" / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "evidence.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "transcript.md").write_text(
        render_markdown(payload), encoding="utf-8"
    )
    print(f"Evidence saved to {output_dir.resolve()}", flush=True)

    if not final_reply:
        raise TimeoutError(f"Manager did not return OFFICEOPS_DONE in {args.timeout}s")
    if not all(protocol_checks.values()):
        raise RuntimeError(f"Agent collaboration evidence is incomplete: {protocol_checks}")
    if sandbox_final["identity"]["locked"] or not sandbox_final["access"]["accessible"]:
        raise RuntimeError("Manager reported completion without verified recovery")
    print(final_reply, flush=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
