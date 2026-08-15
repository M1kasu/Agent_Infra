from __future__ import annotations

from app.models import (
    DiagnosisResult,
    EmployeeContext,
    Evidence,
    ExecutionRecord,
    RiskLevel,
    StructuredIncident,
    VerificationResult,
)
from app.skills.base import RiskPolicy, SkillSpec
from app.tools import ApplicationTool, IAMTool, ServiceHealthTool, VPNTool


CONTEXT_AGENT = "Context Agent"
DIAGNOSIS_AGENT = "Diagnosis Agent"
REMEDIATION_AGENT = "Remediation & Verification Agent"


class EmployeeContextSkill:
    spec = SkillSpec(
        name="EmployeeContextSkill",
        description="Collect identity, VPN, permission, service, and access evidence.",
        input_schema={"$ref": "StructuredIncident"},
        output_schema={"$ref": "EmployeeContext"},
        preconditions=["user and application are normalized"],
        postconditions=["all available enterprise evidence is structured"],
        risk_level=RiskLevel.LOW,
        dependencies=["IAMTool", "VPNTool", "ApplicationTool", "ServiceHealthTool"],
        failure_handling="Stop diagnosis when required entities cannot be queried; preserve trace.",
    )

    def __init__(
        self,
        iam: IAMTool,
        vpn: VPNTool,
        application: ApplicationTool,
        health: ServiceHealthTool,
    ) -> None:
        self.iam = iam
        self.vpn = vpn
        self.application = application
        self.health = health

    def run(self, incident: StructuredIncident) -> EmployeeContext:
        skill = self.spec.name
        identity = self.iam.get_user(
            incident.user, agent=CONTEXT_AGENT, skill=skill
        )
        vpn = self.vpn.get_status(
            incident.user, agent=CONTEXT_AGENT, skill=skill
        )
        permissions = self.application.get_permissions(
            incident.user, agent=CONTEXT_AGENT, skill=skill
        )
        service = self.health.get_health(
            incident.application, agent=CONTEXT_AGENT, skill=skill
        )
        access = self.application.check_access(
            incident.application,
            incident.user,
            agent=CONTEXT_AGENT,
            skill=skill,
        )
        evidence = [
            Evidence(source="IAMTool", fact="identity_active", value=identity["active"]),
            Evidence(source="IAMTool", fact="account_locked", value=identity["locked"]),
            Evidence(source="VPNTool", fact="vpn_enabled", value=vpn["enabled"]),
            Evidence(
                source="ApplicationTool",
                fact="permission_exists",
                value=incident.application in permissions,
            ),
            Evidence(
                source="ServiceHealthTool",
                fact="service_status",
                value=service["status"],
            ),
            Evidence(
                source="ApplicationTool",
                fact="access_probe",
                value=access,
            ),
        ]
        return EmployeeContext(
            employee={
                "username": identity["username"],
                "display_name": identity["display_name"],
                "employment_status": identity["employment_status"],
            },
            identity={"active": identity["active"], "locked": identity["locked"]},
            vpn=vpn,
            permissions=permissions,
            services={incident.application: service},
            access=access,
            evidence=evidence,
        )


class AccessDiagnosisSkill:
    spec = SkillSpec(
        name="AccessDiagnosisSkill",
        description="Infer the most likely root cause from multi-source context.",
        input_schema={"$ref": "EmployeeContext"},
        output_schema={"$ref": "DiagnosisResult"},
        preconditions=["context collection completed"],
        postconditions=["root cause and safe recommended action are explicit"],
        risk_level=RiskLevel.LOW,
        dependencies=["EmployeeContextSkill", "enterprise safety policy"],
        failure_handling="Return unknown_root_cause without executing a speculative action.",
    )

    def run(self, context: EmployeeContext, *, application: str) -> DiagnosisResult:
        facts = {evidence.fact: evidence for evidence in context.evidence}

        def select(names: list[str]) -> list[Evidence]:
            return [facts[name] for name in names if name in facts]

        service = context.services.get(application, {})
        if service.get("status") != "healthy":
            return DiagnosisResult(
                root_cause="service_unhealthy",
                confidence=0.98,
                evidence=select(["service_status", "access_probe"]),
                recommended_action=None,
            )
        if not context.identity.get("active", False):
            return DiagnosisResult(
                root_cause="identity_inactive",
                confidence=0.98,
                evidence=select(["identity_active", "access_probe"]),
                recommended_action=None,
            )
        if context.identity.get("locked", False):
            return DiagnosisResult(
                root_cause="account_locked",
                confidence=0.96,
                evidence=select(
                    [
                        "account_locked",
                        "vpn_enabled",
                        "permission_exists",
                        "service_status",
                    ]
                ),
                recommended_action="unlock_account",
            )
        if not context.vpn.get("enabled", False):
            return DiagnosisResult(
                root_cause="vpn_disabled",
                confidence=0.93,
                evidence=select(["vpn_enabled", "access_probe"]),
                recommended_action=None,
            )
        if application not in context.permissions:
            return DiagnosisResult(
                root_cause="permission_missing",
                confidence=0.95,
                evidence=select(["permission_exists", "access_probe"]),
                recommended_action="request_permission_approval",
            )
        if context.access.get("accessible"):
            return DiagnosisResult(
                root_cause="no_fault_observed",
                confidence=0.85,
                evidence=select(["access_probe"]),
                recommended_action=None,
            )
        return DiagnosisResult(
            root_cause="unknown_root_cause",
            confidence=0.3,
            evidence=context.evidence,
            recommended_action=None,
        )


class AccountRemediationSkill:
    spec = SkillSpec(
        name="AccountRemediationSkill",
        description="Safely unlock an account diagnosed as locked.",
        input_schema={"user": "string", "diagnosis": {"$ref": "DiagnosisResult"}},
        output_schema={"$ref": "ExecutionRecord"},
        preconditions=[
            "root_cause is account_locked",
            "recommended_action is unlock_account",
            "risk policy permits automatic execution",
        ],
        postconditions=["unlock operation has a durable audit record"],
        risk_level=RiskLevel.MEDIUM,
        dependencies=["IAMTool", "RiskPolicy"],
        failure_handling="Do not claim recovery; return failed execution for verification/retry.",
    )

    def __init__(self, iam: IAMTool, risk_policy: RiskPolicy | None = None) -> None:
        self.iam = iam
        self.risk_policy = risk_policy or RiskPolicy()

    def run(
        self,
        *,
        user: str,
        diagnosis: DiagnosisResult,
        task_id: str,
        attempt: int,
    ) -> ExecutionRecord:
        if (
            diagnosis.root_cause != "account_locked"
            or diagnosis.recommended_action != "unlock_account"
        ):
            raise ValueError("account remediation preconditions are not satisfied")
        decision = self.risk_policy.evaluate(self.spec.risk_level)
        if not decision.allowed:
            raise PermissionError(decision.reason)
        response = self.iam.unlock_account(
            user,
            idempotency_key=f"{task_id}:unlock:{attempt}",
            agent=REMEDIATION_AGENT,
            skill=self.spec.name,
        )
        return ExecutionRecord(
            action="unlock_account",
            attempt=attempt,
            tool_success=bool(response.get("success")),
            response=response,
        )


class AccessVerificationSkill:
    spec = SkillSpec(
        name="AccessVerificationSkill",
        description="Re-read identity state and perform a functional application access probe.",
        input_schema={"user": "string", "application": "string"},
        output_schema={"$ref": "VerificationResult"},
        preconditions=["remediation attempt has completed"],
        postconditions=["task success is based on observed state, not tool acknowledgement"],
        risk_level=RiskLevel.LOW,
        dependencies=["IAMTool", "ApplicationTool"],
        failure_handling="Mark verification failed and let Manager retry or fail the task.",
    )

    def __init__(self, iam: IAMTool, application: ApplicationTool) -> None:
        self.iam = iam
        self.application = application

    def run(self, *, user: str, application: str) -> VerificationResult:
        identity = self.iam.get_user(
            user, agent=REMEDIATION_AGENT, skill=self.spec.name
        )
        access = self.application.check_access(
            application,
            user,
            agent=REMEDIATION_AGENT,
            skill=self.spec.name,
        )
        checks = {
            "account_unlocked": not identity["locked"],
            "application_accessible": bool(access["accessible"]),
        }
        success = all(checks.values())
        return VerificationResult(
            success=success,
            checks=checks,
            observed={"identity": identity, "access": access},
            reason=(
                "account state and functional access both recovered"
                if success
                else "tool reported success, but observed enterprise state did not recover"
            ),
        )
