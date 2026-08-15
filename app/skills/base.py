from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.models import RiskLevel


class SkillSpec(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    preconditions: list[str]
    postconditions: list[str]
    risk_level: RiskLevel
    dependencies: list[str]
    failure_handling: str


class RiskDecision(BaseModel):
    allowed: bool
    approval_required: bool
    reason: str


class RiskPolicy:
    """Deterministic enterprise safety policy; never delegated to an LLM."""

    def evaluate(self, risk_level: RiskLevel) -> RiskDecision:
        if risk_level in {RiskLevel.LOW, RiskLevel.MEDIUM}:
            return RiskDecision(
                allowed=True,
                approval_required=False,
                reason=f"{risk_level.value} risk is eligible for automatic execution",
            )
        return RiskDecision(
            allowed=False,
            approval_required=True,
            reason=f"{risk_level.value} risk requires human approval",
        )
