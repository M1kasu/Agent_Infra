from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sandbox.enterprise import EnterpriseSandbox, SandboxNotFoundError


class UnlockRequest(BaseModel):
    idempotency_key: str


class FaultRequest(BaseModel):
    enabled: bool


def create_app(enterprise: EnterpriseSandbox | None = None) -> FastAPI:
    sandbox = enterprise or EnterpriseSandbox()
    api = FastAPI(title="OfficeOps Mini Enterprise Sandbox", version="0.1.0")
    api.state.enterprise = sandbox

    def safe(call):
        try:
            return call()
        except SandboxNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @api.get("/users/{user}")
    def get_user(user: str):
        return safe(lambda: sandbox.get_user(user))

    @api.get("/users/{user}/permissions")
    def get_permissions(user: str):
        return {"permissions": safe(lambda: sandbox.get_permissions(user))}

    @api.post("/users/{user}/unlock")
    def unlock_user(user: str, request: UnlockRequest):
        return safe(
            lambda: sandbox.unlock_user(user, idempotency_key=request.idempotency_key)
        )

    @api.get("/vpn/{user}")
    def get_vpn(user: str):
        return safe(lambda: sandbox.get_vpn(user))

    @api.get("/apps/{app}/health")
    def get_app_health(app: str):
        return safe(lambda: sandbox.get_app_health(app))

    @api.get("/apps/{app}/access/{user}")
    def get_app_access(app: str, user: str):
        return safe(lambda: sandbox.get_app_access(app, user))

    @api.post("/admin/faults/fake-success")
    def configure_fake_success(request: FaultRequest):
        return sandbox.set_fake_success(request.enabled)

    @api.post("/admin/reset")
    def reset_demo_fixture():
        return sandbox.reset()

    return api


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("sandbox.api:app", host="0.0.0.0", port=18100, reload=False)
