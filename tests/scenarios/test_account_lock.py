import json

from app.models import TaskStatus
from tests.conftest import build_manager


def test_successful_unlock(tmp_path, incident):
    sandbox, manager = build_manager(tmp_path)
    result = manager.run(incident, task_id="successful-unlock")
    assert result.status == TaskStatus.COMPLETED
    assert sandbox.get_user("alice")["locked"] is False
    assert result.attempts == 1


def test_verification_after_unlock(tmp_path, incident):
    _, manager = build_manager(tmp_path)
    result = manager.run(incident, task_id="verified-unlock")
    verification = json.loads(
        (tmp_path / result.task_id / "verification.json").read_text(encoding="utf-8")
    )
    assert verification["success"] is True
    assert verification["checks"] == {
        "account_unlocked": True,
        "application_accessible": True,
    }


def test_fake_success_detection(tmp_path, incident):
    sandbox, manager = build_manager(tmp_path, fake_success=True)
    result = manager.run(incident, task_id="fake-success")
    assert result.status == TaskStatus.FAILED
    assert result.attempts == 2
    assert sandbox.get_user("alice")["locked"] is True
    verification = json.loads(
        (tmp_path / result.task_id / "verification.json").read_text(encoding="utf-8")
    )
    assert verification["success"] is False
    trace = json.loads(
        (tmp_path / result.task_id / "trace.json").read_text(encoding="utf-8")
    )
    states = [
        event["current"]
        for event in trace
        if event["event_type"] == "state_transition"
    ]
    assert "RETRYING" in states
    assert states[-1] == "FAILED"


def test_run_writes_required_observability_artifacts(tmp_path, incident):
    _, manager = build_manager(tmp_path)
    result = manager.run(incident, task_id="artifact-check")
    expected = {
        "input.json",
        "context.json",
        "diagnosis.json",
        "tool_calls.jsonl",
        "verification.json",
        "trace.json",
        "result.json",
    }
    assert expected.issubset({path.name for path in (tmp_path / result.task_id).iterdir()})
