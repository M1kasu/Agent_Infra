from __future__ import annotations

import argparse
from typing import Any, Literal

import httpx
from mcp.server.fastmcp import FastMCP


Profile = Literal["readonly", "remediation"]


def _result(tool: str, risk_level: str, data: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "data": data,
        "metadata": {
            "tool": tool,
            "risk_level": risk_level,
            "source": "officeops-enterprise-sandbox",
        },
    }


def build_server(
    profile: Profile,
    *,
    base_url: str = "http://127.0.0.1:18100",
    host: str = "0.0.0.0",
    port: int = 18101,
) -> FastMCP:
    """Build a role-scoped MCP facade over the shared enterprise sandbox."""

    mcp = FastMCP(
        f"OfficeOps {profile.title()} Tools",
        instructions=(
            "Use observed enterprise state as evidence. Tool acknowledgement is not "
            "proof of task completion; verify independently after every mutation."
        ),
        host=host,
        port=port,
    )
    normalized_base_url = base_url.rstrip("/")

    def normalized_identifier(value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("identifier must not be empty")
        return normalized

    def request(method: str, path: str, **kwargs: Any) -> Any:
        with httpx.Client(base_url=normalized_base_url, timeout=15.0) as client:
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()

    if profile == "readonly":

        @mcp.tool()
        def get_employee_identity(user: str) -> dict[str, Any]:
            """Read employee identity and lock state. Risk: low/read-only."""

            user = normalized_identifier(user)
            return _result(
                "get_employee_identity", "low", request("GET", f"/users/{user}")
            )

        @mcp.tool()
        def get_vpn_status(user: str) -> dict[str, Any]:
            """Read the employee VPN state. Risk: low/read-only."""

            user = normalized_identifier(user)
            return _result("get_vpn_status", "low", request("GET", f"/vpn/{user}"))

        @mcp.tool()
        def get_application_permissions(
            user: str, application: str
        ) -> dict[str, Any]:
            """Read permissions and report whether the requested app is granted."""

            user = normalized_identifier(user)
            application = normalized_identifier(application)
            data = request("GET", f"/users/{user}/permissions")
            data["application"] = application
            data["granted"] = application in data["permissions"]
            return _result("get_application_permissions", "low", data)

        @mcp.tool()
        def get_service_health(application: str) -> dict[str, Any]:
            """Read application service health. Risk: low/read-only."""

            application = normalized_identifier(application)
            return _result(
                "get_service_health",
                "low",
                request("GET", f"/apps/{application}/health"),
            )

        @mcp.tool()
        def check_application_access(
            user: str, application: str
        ) -> dict[str, Any]:
            """Probe functional access without mutating state. Risk: low/read-only."""

            user = normalized_identifier(user)
            application = normalized_identifier(application)
            return _result(
                "check_application_access",
                "low",
                request("GET", f"/apps/{application}/access/{user}"),
            )

    elif profile == "remediation":

        @mcp.tool()
        def unlock_account(user: str, idempotency_key: str) -> dict[str, Any]:
            """Unlock one diagnosed account. Risk: medium; idempotency key required."""

            user = normalized_identifier(user)
            if not idempotency_key.strip():
                raise ValueError("idempotency_key is required")
            return _result(
                "unlock_account",
                "medium",
                request(
                    "POST",
                    f"/users/{user}/unlock",
                    json={"idempotency_key": idempotency_key},
                ),
            )

        @mcp.tool()
        def get_employee_identity(user: str) -> dict[str, Any]:
            """Re-read identity state after remediation. Risk: low/read-only."""

            user = normalized_identifier(user)
            return _result(
                "get_employee_identity", "low", request("GET", f"/users/{user}")
            )

        @mcp.tool()
        def check_application_access(
            user: str, application: str
        ) -> dict[str, Any]:
            """Independently probe functional access after remediation."""

            user = normalized_identifier(user)
            application = normalized_identifier(application)
            return _result(
                "check_application_access",
                "low",
                request("GET", f"/apps/{application}/access/{user}"),
            )

    else:  # pragma: no cover - argparse and the type checker constrain this.
        raise ValueError(f"unsupported profile: {profile}")

    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a role-scoped OfficeOps MCP server")
    parser.add_argument("--profile", choices=("readonly", "remediation"), required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:18100")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    server = build_server(
        args.profile,
        base_url=args.base_url,
        host=args.host,
        port=args.port,
    )
    server.run(transport="sse")


if __name__ == "__main__":
    main()
