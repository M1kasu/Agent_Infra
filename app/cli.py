from __future__ import annotations

import argparse
import json

from app.models import StructuredIncident
from app.tools import InMemorySandboxClient
from app.workflows import LocalRuntimeFactory, OfficeOpsManager
from sandbox import EnterpriseSandbox


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the OfficeOps preliminary demo")
    parser.add_argument(
        "--statement", default="我突然打不开公司 Docs 了，昨天还能用。"
    )
    parser.add_argument("--user", default="alice")
    parser.add_argument("--app", default="docs")
    parser.add_argument("--fake-success", action="store_true")
    parser.add_argument("--task-id")
    parser.add_argument("--artifacts-root", default="artifacts/runs")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    sandbox = EnterpriseSandbox(fake_success=args.fake_success)
    factory = LocalRuntimeFactory(InMemorySandboxClient(sandbox))
    manager = OfficeOpsManager(factory, artifacts_root=args.artifacts_root)
    result = manager.run(
        StructuredIncident(
            user=args.user, application=args.app, statement=args.statement
        ),
        task_id=args.task_id,
    )
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0 if result.status == "COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
