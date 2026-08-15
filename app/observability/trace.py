from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return value


class TraceRecorder:
    def __init__(
        self,
        task_id: str,
        trace_id: str,
        *,
        artifacts_root: str | Path = "artifacts/runs",
    ) -> None:
        self.task_id = task_id
        self.trace_id = trace_id
        self.run_dir = Path(artifacts_root).resolve() / task_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.events: list[dict[str, Any]] = []
        self.tool_calls_path = self.run_dir / "tool_calls.jsonl"
        self.tool_calls_path.write_text("", encoding="utf-8")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def record(self, event_type: str, **data: Any) -> dict[str, Any]:
        event = {
            "timestamp": self._now(),
            "task_id": self.task_id,
            "trace_id": self.trace_id,
            "event_type": event_type,
            **data,
        }
        self.events.append(event)
        return event

    def record_tool_call(
        self,
        *,
        agent: str,
        skill: str,
        tool: str,
        operation: str,
        request: dict[str, Any],
        response: dict[str, Any],
    ) -> None:
        call = self.record(
            "tool_call",
            agent=agent,
            skill=skill,
            tool=tool,
            operation=operation,
            request=request,
            response=response,
        )
        with self.tool_calls_path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(call, ensure_ascii=False) + "\n")

    def write_json(self, filename: str, value: Any) -> Path:
        path = self.run_dir / filename
        path.write_text(
            json.dumps(jsonable(value), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def flush_trace(self) -> Path:
        return self.write_json("trace.json", self.events)
