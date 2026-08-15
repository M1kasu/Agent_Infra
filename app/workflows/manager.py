from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.models import (
    StructuredIncident,
    TaskResult,
    TaskState,
    TaskStatus,
    VerificationResult,
)
from app.observability import TraceRecorder
from app.workflows.runtime import LocalRuntimeFactory


ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.RECEIVED: {TaskStatus.COLLECTING_CONTEXT, TaskStatus.FAILED},
    TaskStatus.COLLECTING_CONTEXT: {TaskStatus.DIAGNOSING, TaskStatus.FAILED},
    TaskStatus.DIAGNOSING: {TaskStatus.EXECUTING, TaskStatus.FAILED},
    TaskStatus.EXECUTING: {TaskStatus.VERIFYING, TaskStatus.FAILED},
    TaskStatus.VERIFYING: {
        TaskStatus.COMPLETED,
        TaskStatus.RETRYING,
        TaskStatus.FAILED,
    },
    TaskStatus.RETRYING: {TaskStatus.EXECUTING, TaskStatus.FAILED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: set(),
}


class OfficeOpsManager:
    def __init__(
        self,
        runtime_factory: LocalRuntimeFactory,
        *,
        artifacts_root: str | Path = "artifacts/runs",
        max_attempts: int = 2,
    ) -> None:
        self.runtime_factory = runtime_factory
        self.artifacts_root = artifacts_root
        self.max_attempts = max_attempts

    @staticmethod
    def _transition(
        state: TaskState, target: TaskStatus, trace: TraceRecorder
    ) -> None:
        if target not in ALLOWED_TRANSITIONS[state.status]:
            raise ValueError(f"invalid state transition: {state.status} -> {target}")
        previous = state.status
        state.status = target
        trace.record(
            "state_transition",
            agent="Manager Agent",
            previous=previous.value,
            current=target.value,
        )

    def run(
        self,
        incident: StructuredIncident,
        *,
        task_id: str | None = None,
    ) -> TaskResult:
        task_id = task_id or f"task-{uuid4().hex[:12]}"
        trace_id = f"trace-{uuid4().hex}"
        trace = TraceRecorder(
            task_id, trace_id, artifacts_root=self.artifacts_root
        )
        runtime = self.runtime_factory.build(trace)
        state = TaskState(
            task_id=task_id,
            trace_id=trace_id,
            status=TaskStatus.RECEIVED,
            input=incident,
            plan=[
                "collect multi-source enterprise context",
                "diagnose root cause from evidence",
                "execute policy-gated remediation",
                "re-read state and verify functional access",
            ],
        )
        trace.record("task_received", agent="Manager Agent", input=incident.model_dump())
        trace.write_json("input.json", incident)

        try:
            self._transition(state, TaskStatus.COLLECTING_CONTEXT, trace)
            state.context = runtime.collect_context(incident)
            trace.record("agent_result", agent="Context Agent", result="context_collected")
            trace.write_json("context.json", state.context)

            self._transition(state, TaskStatus.DIAGNOSING, trace)
            state.diagnosis = runtime.diagnose(
                state.context, application=incident.application
            )
            trace.record(
                "agent_result",
                agent="Diagnosis Agent",
                result=state.diagnosis.model_dump(mode="json"),
            )
            trace.write_json("diagnosis.json", state.diagnosis)

            if (
                state.diagnosis.root_cause != "account_locked"
                or state.diagnosis.recommended_action != "unlock_account"
            ):
                state.verification = VerificationResult(
                    success=False,
                    checks={"safe_automatic_action_available": False},
                    observed={"diagnosis": state.diagnosis.model_dump(mode="json")},
                    reason="No safe automatic remediation is available for this diagnosis.",
                )
                self._transition(state, TaskStatus.FAILED, trace)
            else:
                for attempt in range(1, self.max_attempts + 1):
                    self._transition(state, TaskStatus.EXECUTING, trace)
                    execution = runtime.remediate(
                        user=incident.user,
                        diagnosis=state.diagnosis,
                        task_id=task_id,
                        attempt=attempt,
                    )
                    state.execution.append(execution)
                    trace.record(
                        "agent_result",
                        agent="Remediation & Verification Agent",
                        result=execution.model_dump(mode="json"),
                    )

                    self._transition(state, TaskStatus.VERIFYING, trace)
                    state.verification = runtime.verify(
                        user=incident.user, application=incident.application
                    )
                    trace.record(
                        "verification",
                        agent="Remediation & Verification Agent",
                        result=state.verification.model_dump(mode="json"),
                    )
                    if state.verification.success:
                        self._transition(state, TaskStatus.COMPLETED, trace)
                        break
                    if attempt < self.max_attempts:
                        self._transition(state, TaskStatus.RETRYING, trace)
                    else:
                        self._transition(state, TaskStatus.FAILED, trace)
        except Exception as exc:
            trace.record(
                "workflow_error",
                agent="Manager Agent",
                error_type=type(exc).__name__,
                error=str(exc),
            )
            if TaskStatus.FAILED in ALLOWED_TRANSITIONS[state.status]:
                self._transition(state, TaskStatus.FAILED, trace)
            state.verification = state.verification or VerificationResult(
                success=False,
                checks={"workflow_completed": False},
                observed={"error_type": type(exc).__name__},
                reason=str(exc),
            )

        trace.write_json("verification.json", state.verification)
        root_cause = (
            state.diagnosis.root_cause if state.diagnosis else "context_collection_failed"
        )
        if state.status == TaskStatus.COMPLETED:
            message = (
                "检测到账号因连续认证失败被锁定，已完成解锁并重新验证 Docs 访问，"
                "当前访问已恢复。"
            )
        elif root_cause == "account_locked":
            message = (
                "解锁工具返回成功，但验证发现账号仍被锁定或 Docs 仍不可访问；"
                "重试后任务已失败，未关闭事件。"
            )
        else:
            message = "当前证据不足以执行安全的自动修复，任务已停止并保留诊断证据。"
        result = TaskResult(
            task_id=task_id,
            trace_id=trace_id,
            status=state.status,
            root_cause=root_cause,
            message=message,
            attempts=len(state.execution),
            artifact_dir=str(trace.run_dir),
        )
        trace.record(
            "task_finished", agent="Manager Agent", status=state.status.value
        )
        state.trace = trace.events
        trace.write_json("task_state.json", state)
        trace.write_json("result.json", result)
        trace.flush_trace()
        return result
