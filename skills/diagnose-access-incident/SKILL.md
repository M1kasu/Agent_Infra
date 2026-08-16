---
name: diagnose-access-incident
description: Diagnose an access incident from cited evidence and produce a bounded, unapproved action plan.
version: 0.1.0
---

# Diagnose Access Incident

## Input

`WorkItem@1.0`, current `ContextSnapshot`, Scenario Pack version, and optional evaluated knowledge references.

## Output

`Diagnosis@1.0`, rejected hypotheses, `ActionPlan@1.0`, desired outcome, and evidence IDs.

## Decision discipline

For the demo, `account_locked` requires an active employee/account, `locked=true`, `lock_reason=auto_lock`, valid permission, enabled VPN, healthy service, and a failed access probe. A single UI phrase or single observation is insufficient.

## Failure and safety

- Return `RequestAdditionalObservation` when a named fact can resolve uncertainty.
- Return `UNKNOWN` when the bounded acquisition loop is exhausted.
- Do not call write tools, approve the plan, or treat historical knowledge as current fact.

