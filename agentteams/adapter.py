from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.models import TaskState


WorkerRole = Literal["context", "diagnosis", "remediation-verification"]


class AgentTeamsEnvelope(BaseModel):
    api_version: str = "officeops.dev/v1alpha1"
    task_id: str
    trace_id: str
    sender: str
    recipient: str
    message_type: Literal["assignment", "result"]
    shared_state_ref: str
    payload: dict


class AgentTeamsAdapter:
    """Map OfficeOps state to future Matrix/MinIO AgentTeams messages.

    This adapter deliberately does not pretend that an AgentTeams runtime is
    connected. It freezes the transport contract used by a later live adapter.
    """

    VERSION = "v1.2.2"
    RECIPIENTS: dict[WorkerRole, str] = {
        "context": "officeops-context",
        "diagnosis": "officeops-diagnosis",
        "remediation-verification": "officeops-remediation-verification",
    }

    def build_assignment(
        self,
        role: WorkerRole,
        state: TaskState,
        payload: dict,
    ) -> AgentTeamsEnvelope:
        return AgentTeamsEnvelope(
            task_id=state.task_id,
            trace_id=state.trace_id,
            sender="officeops-manager",
            recipient=self.RECIPIENTS[role],
            message_type="assignment",
            shared_state_ref=f"shared/tasks/{state.task_id}/task_state.json",
            payload=payload,
        )
