from app.models import EmployeeContext, Evidence
from app.observability import TraceRecorder
from app.skills import AccessDiagnosisSkill, EmployeeContextSkill
from app.tools import ApplicationTool, IAMTool, InMemorySandboxClient, ServiceHealthTool, VPNTool
from sandbox import EnterpriseSandbox


def collect_context(tmp_path, incident):
    sandbox = EnterpriseSandbox()
    trace = TraceRecorder("unit-context", "trace-unit", artifacts_root=tmp_path)
    client = InMemorySandboxClient(sandbox)
    skill = EmployeeContextSkill(
        IAMTool(client, trace),
        VPNTool(client, trace),
        ApplicationTool(client, trace),
        ServiceHealthTool(client, trace),
    )
    return skill.run(incident)


def test_account_locked(tmp_path, incident):
    context = collect_context(tmp_path, incident)
    diagnosis = AccessDiagnosisSkill().run(context, application="docs")
    assert diagnosis.root_cause == "account_locked"
    assert diagnosis.recommended_action == "unlock_account"
    assert diagnosis.confidence == 0.96


def test_permission_ok(tmp_path, incident):
    context = collect_context(tmp_path, incident)
    assert "docs" in context.permissions
    assert next(e.value for e in context.evidence if e.fact == "permission_exists") is True


def test_docs_healthy(tmp_path, incident):
    context = collect_context(tmp_path, incident)
    assert context.services["docs"]["status"] == "healthy"


def test_unknown_root_cause():
    context = EmployeeContext(
        employee={"username": "alice", "employment_status": "active"},
        identity={"active": True, "locked": False},
        vpn={"enabled": True},
        permissions=["docs"],
        services={"docs": {"status": "healthy"}},
        access={"accessible": False, "reasons": ["unclassified_policy"]},
        evidence=[
            Evidence(
                source="ApplicationTool",
                fact="access_probe",
                value={"accessible": False, "reasons": ["unclassified_policy"]},
            )
        ],
    )
    diagnosis = AccessDiagnosisSkill().run(context, application="docs")
    assert diagnosis.root_cause == "unknown_root_cause"
    assert diagnosis.recommended_action is None
