---
name: verify-access-outcome
description: Independently verify account and functional access state after an OfficeOps execution.
version: 0.1.0
---

# Verify Access Outcome

## Trigger

Run after an Execution result, including tool success, failure, or unknown status.

## Input and output

- Input: DesiredOutcome, Execution reference, target references
- Output: `Verification@1.0` with `PASS|FAIL|INCONCLUSIVE`, fresh observations, assertions, and evidence IDs

## Assertions for the demo

1. A fresh IAM read reports `locked=false`.
2. A fresh Docs functional probe reports `accessible=true`.

## Safety

- Use a read-only identity different from the executor.
- Do not reuse the executor's success claim or the pre-action ContextSnapshot.
- Do not repair a failed assertion.
- Return `INCONCLUSIVE`, never PASS, if fresh verification is unavailable.

