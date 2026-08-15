---
name: account-remediation
description: Execute a policy-gated enterprise account unlock after an evidence-backed account_locked diagnosis. Use only for medium-risk remediation explicitly assigned by the Manager; never use for permission, VPN, or service failures.
---

# Account Remediation

Perform one idempotent mutation and report the tool acknowledgement without claiming recovery.

## Contract

| Field | Value |
|---|---|
| name | `AccountRemediationSkill` |
| description | Unlock a diagnosed locked account with policy and audit controls. |
| input_schema | `{user, diagnosis, task_id, attempt}` |
| output_schema | `ExecutionRecord {action, attempt, tool_success, response}` |
| preconditions | Root cause is `account_locked`; action is `unlock_account`; risk policy allows execution. |
| postconditions | The mutation and idempotency key are recorded in the task trace. |
| risk_level | `medium` |
| dependencies | `IAMTool`, `RiskPolicy` |
| failure_handling | Report the execution failure or acknowledgement; defer success judgment to access-verification. |

## Workflow

1. Validate diagnosis and recommended action exactly.
2. Evaluate deterministic risk policy.
3. Call `IAMTool.unlock_account` with a task-scoped idempotency key.
4. Return the raw acknowledgement. Do not close the task.

## AgentTeams MCP mapping

Call `officeops-remediation.unlock_account` through `mcporter` with the exact
`user` and a task-scoped `idempotency_key`. This Worker is the only role given
that server. Report `data.success` as an acknowledgement only; verification is
still mandatory.
