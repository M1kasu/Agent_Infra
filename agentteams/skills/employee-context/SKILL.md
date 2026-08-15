---
name: employee-context
description: Collect structured identity, VPN, application permission, service health, and functional access evidence for an enterprise SaaS access incident. Use before diagnosis whenever an employee reports that an application is unavailable.
---

# Employee Context

Collect evidence; do not infer a root cause or mutate enterprise state.

## Contract

| Field | Value |
|---|---|
| name | `EmployeeContextSkill` |
| description | Collect multi-source employee access context. |
| input_schema | `StructuredIncident {user, application, statement}` |
| output_schema | `EmployeeContext {employee, identity, vpn, permissions, services, access, evidence}` |
| preconditions | User and application are normalized. |
| postconditions | Every available fact identifies its source tool. |
| risk_level | `low` |
| dependencies | `IAMTool`, `VPNTool`, `ApplicationTool`, `ServiceHealthTool` |
| failure_handling | Stop diagnosis when a required entity cannot be queried; preserve the error in the trace. |

## Workflow

1. Query the employee and identity record with `IAMTool`.
2. Query VPN state with `VPNTool`.
3. Query application permissions and current access with `ApplicationTool`.
4. Query service status with `ServiceHealthTool`.
5. Return structured facts and source-labelled evidence. Never recommend a mutation.

## AgentTeams MCP mapping

Call the assigned `officeops-readonly` server through `mcporter`:

- `officeops-readonly.get_employee_identity` with `user`
- `officeops-readonly.get_vpn_status` with `user`
- `officeops-readonly.get_application_permissions` with `user` and `application`
- `officeops-readonly.get_service_health` with `application`
- `officeops-readonly.check_application_access` with `user` and `application`

Use the returned `data` fields as observations and preserve each response's
`metadata.tool` as the evidence source.
