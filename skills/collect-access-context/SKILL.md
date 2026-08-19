---
name: collect-access-context
description: Collect minimum read-only identity, VPN, permission, service, and functional-access evidence for an access incident.
version: 0.1.0
---

# Collect Access Context

## Trigger

`WorkItem@1.0` contains an access-incident candidate and a resolvable employee/application pair.

## Input and output

- Input: `WorkItem`, `ContextRequirement[]`, prior `MissingFact[]`
- Output: `ContextSnapshot@1.0`, `Observation[]`, `EvidenceRef[]`, missing facts and conflicts

## Tool dependencies

Read-only IAM subject/account state, VPN state, effective permission, service health, and functional access probe.

## Adaptive behavior

Start from the Scenario Pack minimum facts. Add observations only when an evidence gap or conflict requires them. For example, a locked account requires its lock reason before an automatic action can be considered.

## Failure and safety

- A critical source failure returns `BLOCKED`; non-critical failures are explicit degradations.
- Preserve contradictory observations instead of overwriting them.
- Query only the subject and application in the current WorkItem.
- Never call `iam.unlock_account`.

