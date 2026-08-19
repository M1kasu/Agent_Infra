---
name: execute-controlled-action
description: Execute a frozen OfficeOps ActionStep through the policy-enforcing tool gateway with idempotency and receipts.
version: 0.1.0
---

# Execute Controlled Action

## Preconditions

- Schema-valid frozen ActionPlan
- Current `plan_hash`
- Deterministic PolicyDecision
- Required Approval references, if any
- Exact target, parameters, operation, and idempotency key

## Output

`Execution@1.0`, provider receipt, ToolCall, evidence reference, and explicit `SUCCEEDED|FAILED|UNKNOWN` status.

## Safety

- Never change or extend a plan.
- Gateway authorization is authoritative; Prompt instructions cannot override it.
- An unknown write outcome must be reconciled by a fresh read before retry.
- A successful receipt is not a successful business outcome.

