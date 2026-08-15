---
name: access-verification
description: Independently verify enterprise SaaS recovery after remediation by re-reading account state and probing functional application access. Use after every mutation, including when the remediation tool reports success.
---

# Access Verification

Enforce the rule: Tool Success does not equal Task Success.

## Contract

| Field | Value |
|---|---|
| name | `AccessVerificationSkill` |
| description | Observe post-action identity state and functional application access. |
| input_schema | `{user, application}` |
| output_schema | `VerificationResult {success, checks, observed, reason}` |
| preconditions | A remediation attempt completed. |
| postconditions | Success requires both an unlocked account and successful access probe. |
| risk_level | `low` |
| dependencies | `IAMTool`, `ApplicationTool` |
| failure_handling | Return failed verification so the Manager can retry once or fail closed. |

## Workflow

1. Re-read identity state from `IAMTool`; do not trust cached context.
2. Run `ApplicationTool.check_access`; do not trust the mutation response.
3. Mark success only if `locked=false` and `accessible=true`.
4. Return observed state and failed checks for retry/audit.

## AgentTeams MCP mapping

After every unlock attempt, call both selectors through `mcporter` using fresh
requests:

- `officeops-remediation.get_employee_identity` with `user`
- `officeops-remediation.check_application_access` with `user` and `application`

Only return `success=true` when `data.locked=false` and
`data.accessible=true` in those new observations.
