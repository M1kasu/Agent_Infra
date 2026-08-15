from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    RECEIVED = "RECEIVED"
    COLLECTING_CONTEXT = "COLLECTING_CONTEXT"
    DIAGNOSING = "DIAGNOSING"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StructuredIncident(BaseModel):
    user: str
    application: str
    statement: str


class Evidence(BaseModel):
    source: str
    fact: str
    value: Any


class EmployeeContext(BaseModel):
    employee: dict[str, Any]
    identity: dict[str, Any]
    vpn: dict[str, Any]
    permissions: list[str]
    services: dict[str, dict[str, Any]]
    access: dict[str, Any]
    evidence: list[Evidence] = Field(default_factory=list)


class DiagnosisResult(BaseModel):
    root_cause: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[Evidence] = Field(default_factory=list)
    recommended_action: str | None = None


class ExecutionRecord(BaseModel):
    action: str
    attempt: int
    tool_success: bool
    response: dict[str, Any]


class VerificationResult(BaseModel):
    success: bool
    checks: dict[str, bool]
    observed: dict[str, Any]
    reason: str


class TaskState(BaseModel):
    task_id: str
    trace_id: str
    status: TaskStatus
    input: StructuredIncident
    context: EmployeeContext | None = None
    diagnosis: DiagnosisResult | None = None
    plan: list[str] = Field(default_factory=list)
    execution: list[ExecutionRecord] = Field(default_factory=list)
    verification: VerificationResult | None = None
    trace: list[dict[str, Any]] = Field(default_factory=list)


class TaskResult(BaseModel):
    task_id: str
    trace_id: str
    status: TaskStatus
    root_cause: str
    message: str
    attempts: int
    artifact_dir: str
