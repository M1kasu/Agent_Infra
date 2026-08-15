from __future__ import annotations

from app.models import DiagnosisResult, EmployeeContext, ExecutionRecord, StructuredIncident, VerificationResult
from app.skills import (
    AccessDiagnosisSkill,
    AccessVerificationSkill,
    AccountRemediationSkill,
    EmployeeContextSkill,
)


class ContextAgent:
    def __init__(self, skill: EmployeeContextSkill) -> None:
        self.skill = skill

    def collect(self, incident: StructuredIncident) -> EmployeeContext:
        return self.skill.run(incident)


class DiagnosisAgent:
    def __init__(self, skill: AccessDiagnosisSkill) -> None:
        self.skill = skill

    def diagnose(self, context: EmployeeContext, *, application: str) -> DiagnosisResult:
        return self.skill.run(context, application=application)


class RemediationVerificationAgent:
    def __init__(
        self,
        remediation: AccountRemediationSkill,
        verification: AccessVerificationSkill,
    ) -> None:
        self.remediation = remediation
        self.verification = verification

    def remediate(
        self,
        *,
        user: str,
        diagnosis: DiagnosisResult,
        task_id: str,
        attempt: int,
    ) -> ExecutionRecord:
        return self.remediation.run(
            user=user,
            diagnosis=diagnosis,
            task_id=task_id,
            attempt=attempt,
        )

    def verify(self, *, user: str, application: str) -> VerificationResult:
        return self.verification.run(user=user, application=application)
