import assert from "node:assert/strict";
import test from "node:test";

import { createLogicalClock } from "../lib/clock.mjs";
import { GatewayError, MockToolGateway } from "../lib/mock-gateway.mjs";
import { runOfficeOpsDemo } from "../lib/runner.mjs";

test("G01 completes only after fresh state and functional verification", () => {
  const run = runOfficeOpsDemo({ mode: "normal", runId: "g01" });
  assert.equal(run.result.status, "COMPLETED");
  assert.equal(run.result.root_cause, "account_locked");
  assert.equal(run.result.tool_status, "SUCCEEDED");
  assert.equal(run.result.verification_status, "PASS");
  assert.deepEqual(run.artifacts.verification.observed, {
    account_locked: false,
    docs_accessible: true
  });
  assert.ok(run.artifacts.diagnosis.evidence_ids.length >= 5);
  assert.ok(run.artifacts.trace.some((event) => event.agent === "verification-agent"));
});

test("G07 rejects fake tool success when business state is unchanged", () => {
  const run = runOfficeOpsDemo({ mode: "fake_success", runId: "g07" });
  assert.equal(run.result.status, "FAILED");
  assert.equal(run.result.tool_status, "SUCCEEDED");
  assert.equal(run.result.execution_status, "SUCCEEDED");
  assert.equal(run.result.verification_status, "FAIL");
  assert.deepEqual(run.artifacts.verification.observed, {
    account_locked: true,
    docs_accessible: false
  });
});

test("context identity cannot call the write operation", () => {
  const gateway = new MockToolGateway({
    runId: "forbidden",
    mode: "normal",
    now: createLogicalClock()
  });
  assert.throws(
    () => gateway.call({ actor: "context-agent", operation: "iam.unlock_account" }),
    (error) => error instanceof GatewayError && error.code === "TOOL_FORBIDDEN"
  );
});

test("write gateway rejects a call without plan-bound authorization", () => {
  const gateway = new MockToolGateway({
    runId: "policy-denied",
    mode: "normal",
    now: createLogicalClock()
  });
  assert.throws(
    () => gateway.call({
      actor: "execution-agent",
      operation: "iam.unlock_account",
      targetRef: "iam://corp/alice"
    }),
    (error) => error instanceof GatewayError && error.code === "POLICY_DENIED"
  );
});

test("write gateway rejects a stale object version", () => {
  const gateway = new MockToolGateway({
    runId: "stale-target",
    mode: "normal",
    now: createLogicalClock()
  });
  assert.throws(
    () => gateway.call({
      actor: "execution-agent",
      operation: "iam.unlock_account",
      targetRef: "iam://corp/alice",
      parameters: { expected_object_version: 6 },
      authorization: {
        policy_decision: "AUTO_ALLOW",
        policy_decision_id: "pd-stale",
        plan_hash: "sha256:stale",
        idempotency_key: "stale-target:unlock"
      }
    }),
    (error) => error instanceof GatewayError && error.code === "STALE_TARGET"
  );
});

test("the user input does not contain a leaked scenario or root cause label", () => {
  const run = runOfficeOpsDemo({ runId: "no-leak" });
  const rawInput = run.artifacts.input.message.toLowerCase();
  assert.equal(rawInput.includes("access-incident"), false);
  assert.equal(rawInput.includes("account_locked"), false);
  assert.equal(run.artifacts.normalized_work_item.scenario_candidates[0].scenario_id, "access-incident");
});
