from __future__ import annotations

from typing import Protocol

from app.agents import ContextAgent, DiagnosisAgent, RemediationVerificationAgent
from app.models import DiagnosisResult, EmployeeContext, ExecutionRecord, StructuredIncident, VerificationResult
from app.observability import TraceRecorder
from app.skills import (
    AccessDiagnosisSkill,
    AccessVerificationSkill,
    AccountRemediationSkill,
    EmployeeContextSkill,
)
from app.tools import ApplicationTool, IAMTool, ServiceHealthTool, VPNTool
from app.tools.enterprise import SandboxClient


class AgentRuntime(Protocol):
    """Coordination port implemented locally now and by AgentTeams transport later."""

    def collect_context(self, incident: StructuredIncident) -> EmployeeContext: ...

    def diagnose(self, context: EmployeeContext, *, application: str) -> DiagnosisResult: ...

    def remediate(
        self,
        *,
        user: str,
        diagnosis: DiagnosisResult,
        task_id: str,
        attempt: int,
    ) -> ExecutionRecord: ...

    def verify(self, *, user: str, application: str) -> VerificationResult: ...


class LocalAgentRuntime:
    def __init__(
        self,
        context_agent: ContextAgent,
        diagnosis_agent: DiagnosisAgent,
        remediation_agent: RemediationVerificationAgent,
    ) -> None:
        self.context_agent = context_agent
        self.diagnosis_agent = diagnosis_agent
        self.remediation_agent = remediation_agent

    def collect_context(self, incident: StructuredIncident) -> EmployeeContext:
        return self.context_agent.collect(incident)

    def diagnose(self, context: EmployeeContext, *, application: str) -> DiagnosisResult:
        return self.diagnosis_agent.diagnose(context, application=application)

    def remediate(
        self,
        *,
        user: str,
        diagnosis: DiagnosisResult,
        task_id: str,
        attempt: int,
    ) -> ExecutionRecord:
        return self.remediation_agent.remediate(
            user=user, diagnosis=diagnosis, task_id=task_id, attempt=attempt
        )

    def verify(self, *, user: str, application: str) -> VerificationResult:
        return self.remediation_agent.verify(user=user, application=application)


class LocalRuntimeFactory:
    def __init__(self, client: SandboxClient) -> None:
        self.client = client

    def build(self, trace: TraceRecorder) -> LocalAgentRuntime:
        iam = IAMTool(self.client, trace)
        vpn = VPNTool(self.client, trace)
        application = ApplicationTool(self.client, trace)
        health = ServiceHealthTool(self.client, trace)
        context_skill = EmployeeContextSkill(iam, vpn, application, health)
        diagnosis_skill = AccessDiagnosisSkill()
        remediation_skill = AccountRemediationSkill(iam)
        verification_skill = AccessVerificationSkill(iam, application)
        return LocalAgentRuntime(
            ContextAgent(context_skill),
            DiagnosisAgent(diagnosis_skill),
            RemediationVerificationAgent(remediation_skill, verification_skill),
        )
