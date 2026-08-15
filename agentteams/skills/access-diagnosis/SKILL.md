---
name: access-diagnosis
description: Diagnose an enterprise SaaS access failure from structured identity, VPN, permission, service, and access evidence. Use only after employee-context has completed; never select an action from ticket keywords alone.
---

# Access Diagnosis

Infer a root cause from observed state and fail closed when evidence is insufficient.

## Contract

| Field | Value |
|---|---|
| name | `AccessDiagnosisSkill` |
| description | Produce an evidence-backed root cause and safe recommended action. |
| input_schema | `EmployeeContext` |
| output_schema | `DiagnosisResult {root_cause, confidence, evidence, recommended_action}` |
| preconditions | Context collection completed successfully. |
| postconditions | Root cause and recommended action are explicit and traceable to evidence. |
| risk_level | `low` |
| dependencies | `EmployeeContextSkill`, enterprise safety policy |
| failure_handling | Return `unknown_root_cause` with no action rather than guessing. |

## Decision order

1. Check service health and identity activation.
2. Check account lock, VPN, then application permission.
3. Recommend `unlock_account` only when the account is observed locked.
4. Treat permission grants as approval-requiring work.
5. Return `unknown_root_cause` when all known prerequisites look healthy but access still fails.
