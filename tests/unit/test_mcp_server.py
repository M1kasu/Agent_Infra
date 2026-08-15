import asyncio

from sandbox.mcp_server import build_server


def tool_names(profile: str) -> set[str]:
    server = build_server(profile, port=0)  # type: ignore[arg-type]
    return {tool.name for tool in asyncio.run(server.list_tools())}


def test_readonly_profile_excludes_mutation() -> None:
    names = tool_names("readonly")
    assert "get_employee_identity" in names
    assert "check_application_access" in names
    assert "unlock_account" not in names


def test_remediation_profile_has_minimal_mutation_and_verification_tools() -> None:
    assert tool_names("remediation") == {
        "unlock_account",
        "get_employee_identity",
        "check_application_access",
    }
