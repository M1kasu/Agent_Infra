from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any


class SandboxNotFoundError(KeyError):
    """Raised when a requested sandbox entity does not exist."""


class EnterpriseSandbox:
    """Stateful, in-memory simulation of a small enterprise environment."""

    def __init__(self, *, fake_success: bool = False) -> None:
        self._lock = RLock()
        self.fake_success = fake_success
        self.users: dict[str, dict[str, Any]] = {
            "alice": {
                "username": "alice",
                "display_name": "Alice",
                "employment_status": "active",
                "active": True,
                "locked": True,
            }
        }
        self.permissions: dict[str, list[str]] = {"alice": ["docs"]}
        self.vpn: dict[str, dict[str, Any]] = {"alice": {"enabled": True}}
        self.apps: dict[str, dict[str, Any]] = {
            "docs": {"status": "healthy"}
        }

    def get_user(self, user: str) -> dict[str, Any]:
        with self._lock:
            if user not in self.users:
                raise SandboxNotFoundError(f"unknown user: {user}")
            return deepcopy(self.users[user])

    def get_permissions(self, user: str) -> list[str]:
        self.get_user(user)
        with self._lock:
            return list(self.permissions.get(user, []))

    def unlock_user(self, user: str, *, idempotency_key: str) -> dict[str, Any]:
        del idempotency_key  # The in-memory mutation is naturally idempotent.
        with self._lock:
            if user not in self.users:
                raise SandboxNotFoundError(f"unknown user: {user}")
            if not self.fake_success:
                self.users[user]["locked"] = False
            # Deliberately returns claimed success during fault injection too.
            return {"success": True, "operation": "unlock_account", "user": user}

    def get_vpn(self, user: str) -> dict[str, Any]:
        self.get_user(user)
        with self._lock:
            return deepcopy(self.vpn.get(user, {"enabled": False}))

    def get_app_health(self, app: str) -> dict[str, Any]:
        with self._lock:
            if app not in self.apps:
                raise SandboxNotFoundError(f"unknown app: {app}")
            return deepcopy(self.apps[app])

    def get_app_access(self, app: str, user: str) -> dict[str, Any]:
        identity = self.get_user(user)
        vpn = self.get_vpn(user)
        health = self.get_app_health(app)
        permissions = self.get_permissions(user)
        reasons: list[str] = []
        if not identity["active"]:
            reasons.append("identity_inactive")
        if identity["locked"]:
            reasons.append("account_locked")
        if not vpn["enabled"]:
            reasons.append("vpn_disabled")
        if app not in permissions:
            reasons.append("permission_missing")
        if health["status"] != "healthy":
            reasons.append("service_unhealthy")
        return {"accessible": not reasons, "reasons": reasons}

    def set_fake_success(self, enabled: bool) -> dict[str, bool]:
        with self._lock:
            self.fake_success = enabled
            return {"fake_success": self.fake_success}

    def reset(self) -> dict[str, bool]:
        """Restore the deterministic account-lock demo fixture."""

        with self._lock:
            self.fake_success = False
            self.users["alice"] = {
                "username": "alice",
                "display_name": "Alice",
                "employment_status": "active",
                "active": True,
                "locked": True,
            }
            self.permissions["alice"] = ["docs"]
            self.vpn["alice"] = {"enabled": True}
            self.apps["docs"] = {"status": "healthy"}
            return {"reset": True}
