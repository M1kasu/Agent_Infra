from fastapi.testclient import TestClient

from sandbox import EnterpriseSandbox
from sandbox.api import create_app


def test_sandbox_state_changes_after_unlock():
    client = TestClient(create_app(EnterpriseSandbox()))
    assert client.get("/users/alice").json()["locked"] is True
    response = client.post(
        "/users/alice/unlock", json={"idempotency_key": "test-unlock"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert client.get("/users/alice").json()["locked"] is False
    assert client.get("/apps/docs/access/alice").json()["accessible"] is True


def test_sandbox_fake_success_lies_about_mutation():
    client = TestClient(create_app(EnterpriseSandbox(fake_success=True)))
    response = client.post(
        "/users/alice/unlock", json={"idempotency_key": "test-fake"}
    )
    assert response.json()["success"] is True
    assert client.get("/users/alice").json()["locked"] is True


def test_sandbox_reset_restores_account_lock_fixture():
    client = TestClient(create_app(EnterpriseSandbox()))
    client.post("/users/alice/unlock", json={"idempotency_key": "reset-test"})
    assert client.get("/users/alice").json()["locked"] is False

    assert client.post("/admin/reset").json() == {"reset": True}
    assert client.get("/users/alice").json()["locked"] is True
