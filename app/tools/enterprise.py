from __future__ import annotations

from typing import Any, Protocol

import httpx

from app.observability import TraceRecorder
from sandbox import EnterpriseSandbox


class SandboxClient(Protocol):
    def get_user(self, user: str) -> dict[str, Any]: ...

    def get_permissions(self, user: str) -> list[str]: ...

    def unlock_user(self, user: str, *, idempotency_key: str) -> dict[str, Any]: ...

    def get_vpn(self, user: str) -> dict[str, Any]: ...

    def get_app_health(self, app: str) -> dict[str, Any]: ...

    def get_app_access(self, app: str, user: str) -> dict[str, Any]: ...


class InMemorySandboxClient:
    """Local adapter used by tests and the zero-configuration demo."""

    def __init__(self, sandbox: EnterpriseSandbox) -> None:
        self.sandbox = sandbox

    def get_user(self, user: str) -> dict[str, Any]:
        return self.sandbox.get_user(user)

    def get_permissions(self, user: str) -> list[str]:
        return self.sandbox.get_permissions(user)

    def unlock_user(self, user: str, *, idempotency_key: str) -> dict[str, Any]:
        return self.sandbox.unlock_user(user, idempotency_key=idempotency_key)

    def get_vpn(self, user: str) -> dict[str, Any]:
        return self.sandbox.get_vpn(user)

    def get_app_health(self, app: str) -> dict[str, Any]:
        return self.sandbox.get_app_health(app)

    def get_app_access(self, app: str, user: str) -> dict[str, Any]:
        return self.sandbox.get_app_access(app, user)


class HttpSandboxClient:
    """HTTP adapter proving Tools are independent from sandbox implementation."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.client = httpx.Client(base_url=base_url, timeout=5.0)

    def get_user(self, user: str) -> dict[str, Any]:
        response = self.client.get(f"/users/{user}")
        response.raise_for_status()
        return response.json()

    def get_permissions(self, user: str) -> list[str]:
        response = self.client.get(f"/users/{user}/permissions")
        response.raise_for_status()
        return response.json()["permissions"]

    def unlock_user(self, user: str, *, idempotency_key: str) -> dict[str, Any]:
        response = self.client.post(
            f"/users/{user}/unlock", json={"idempotency_key": idempotency_key}
        )
        response.raise_for_status()
        return response.json()

    def get_vpn(self, user: str) -> dict[str, Any]:
        response = self.client.get(f"/vpn/{user}")
        response.raise_for_status()
        return response.json()

    def get_app_health(self, app: str) -> dict[str, Any]:
        response = self.client.get(f"/apps/{app}/health")
        response.raise_for_status()
        return response.json()

    def get_app_access(self, app: str, user: str) -> dict[str, Any]:
        response = self.client.get(f"/apps/{app}/access/{user}")
        response.raise_for_status()
        return response.json()


class AuditedTool:
    name = "Tool"

    def __init__(self, client: SandboxClient, trace: TraceRecorder) -> None:
        self.client = client
        self.trace = trace

    def _audit(
        self,
        *,
        agent: str,
        skill: str,
        operation: str,
        request: dict[str, Any],
        response: dict[str, Any],
    ) -> dict[str, Any]:
        self.trace.record_tool_call(
            agent=agent,
            skill=skill,
            tool=self.name,
            operation=operation,
            request=request,
            response=response,
        )
        return response


class IAMTool(AuditedTool):
    name = "IAMTool"

    def get_user(self, user: str, *, agent: str, skill: str) -> dict[str, Any]:
        return self._audit(
            agent=agent,
            skill=skill,
            operation="get_user",
            request={"user": user},
            response=self.client.get_user(user),
        )

    def unlock_account(
        self,
        user: str,
        *,
        idempotency_key: str,
        agent: str,
        skill: str,
    ) -> dict[str, Any]:
        return self._audit(
            agent=agent,
            skill=skill,
            operation="unlock_account",
            request={"user": user, "idempotency_key": idempotency_key},
            response=self.client.unlock_user(user, idempotency_key=idempotency_key),
        )


class VPNTool(AuditedTool):
    name = "VPNTool"

    def get_status(self, user: str, *, agent: str, skill: str) -> dict[str, Any]:
        return self._audit(
            agent=agent,
            skill=skill,
            operation="get_vpn_status",
            request={"user": user},
            response=self.client.get_vpn(user),
        )


class ApplicationTool(AuditedTool):
    name = "ApplicationTool"

    def get_permissions(
        self, user: str, *, agent: str, skill: str
    ) -> list[str]:
        permissions = self.client.get_permissions(user)
        self._audit(
            agent=agent,
            skill=skill,
            operation="get_permissions",
            request={"user": user},
            response={"permissions": permissions},
        )
        return permissions

    def check_access(
        self, app: str, user: str, *, agent: str, skill: str
    ) -> dict[str, Any]:
        return self._audit(
            agent=agent,
            skill=skill,
            operation="check_access",
            request={"app": app, "user": user},
            response=self.client.get_app_access(app, user),
        )


class ServiceHealthTool(AuditedTool):
    name = "ServiceHealthTool"

    def get_health(self, app: str, *, agent: str, skill: str) -> dict[str, Any]:
        return self._audit(
            agent=agent,
            skill=skill,
            operation="get_app_health",
            request={"app": app},
            response=self.client.get_app_health(app),
        )
