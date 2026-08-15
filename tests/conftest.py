from __future__ import annotations

from pathlib import Path

import pytest

from app.models import StructuredIncident
from app.tools import InMemorySandboxClient
from app.workflows import LocalRuntimeFactory, OfficeOpsManager
from sandbox import EnterpriseSandbox


@pytest.fixture
def incident() -> StructuredIncident:
    return StructuredIncident(
        user="alice",
        application="docs",
        statement="我突然打不开公司 Docs 了，昨天还能用。",
    )


def build_manager(
    artifacts_root: Path, *, fake_success: bool = False
) -> tuple[EnterpriseSandbox, OfficeOpsManager]:
    sandbox = EnterpriseSandbox(fake_success=fake_success)
    manager = OfficeOpsManager(
        LocalRuntimeFactory(InMemorySandboxClient(sandbox)),
        artifacts_root=artifacts_root,
    )
    return sandbox, manager
