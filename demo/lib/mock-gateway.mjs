import { createHash } from "node:crypto";

import fixture from "../../scenarios/access-incident/fixture.json" with { type: "json" };

const READ_OPERATIONS = new Set([
  "iam.get_subject",
  "iam.get_account_state",
  "vpn.get_state",
  "docs.get_effective_permissions",
  "docs.get_service_health",
  "docs.probe_access"
]);

const ROLE_ALLOWLIST = {
  "context-agent": READ_OPERATIONS,
  "verification-agent": new Set([
    "iam.get_account_state",
    "docs.get_effective_permissions",
    "docs.get_service_health",
    "docs.probe_access"
  ]),
  "execution-agent": new Set(["iam.unlock_account"]),
  "test-harness": new Set(["sandbox.reset"])
};

function clone(value) {
  return structuredClone(value);
}

function evidenceHash(value) {
  return `sha256:${createHash("sha256").update(JSON.stringify(value)).digest("hex")}`;
}

export class GatewayError extends Error {
  constructor(code, message, statusCode = 400) {
    super(message);
    this.name = "GatewayError";
    this.code = code;
    this.statusCode = statusCode;
  }
}

export class MockToolGateway {
  constructor({ runId, mode = "normal", now }) {
    this.runId = runId;
    this.mode = mode;
    this.now = now;
    this.state = clone(fixture);
    this.toolCalls = [];
    this.evidence = [];
    this.idempotency = new Map();
    this.sequence = 0;
  }

  snapshot() {
    return clone(this.state);
  }

  #recordEvidence({ actor, operation, result, observedAt }) {
    this.sequence += 1;
    const evidence = {
      evidence_id: `ev-${this.runId}-${String(this.sequence).padStart(3, "0")}`,
      run_id: this.runId,
      type: operation === "iam.unlock_account" ? "TOOL_RESULT" : "OBSERVATION",
      source: `mock://${operation}`,
      observed_at: observedAt,
      collected_by: actor,
      content_hash: evidenceHash(result),
      sensitivity: "INTERNAL"
    };
    this.evidence.push(evidence);
    return evidence;
  }

  #isAccessible() {
    return Boolean(
      this.state.subject.employment_status === "ACTIVE" &&
        this.state.account.active &&
        !this.state.account.locked &&
        this.state.vpn.enabled &&
        this.state.permission.granted &&
        this.state.service.status === "HEALTHY"
    );
  }

  #authorize(actor, operation) {
    const allowed = ROLE_ALLOWLIST[actor];
    if (!allowed || !allowed.has(operation)) {
      throw new GatewayError(
        "TOOL_FORBIDDEN",
        `${actor} is not allowed to call ${operation}`,
        403
      );
    }
  }

  call({ actor, operation, targetRef = null, parameters = {}, authorization = {} }) {
    this.#authorize(actor, operation);
    const requestedAt = this.now();
    const toolCallId = `tc-${this.runId}-${String(this.toolCalls.length + 1).padStart(3, "0")}`;

    let result;
    if (operation === "iam.get_subject") {
      result = clone(this.state.subject);
    } else if (operation === "iam.get_account_state") {
      result = clone(this.state.account);
    } else if (operation === "vpn.get_state") {
      result = clone(this.state.vpn);
    } else if (operation === "docs.get_effective_permissions") {
      result = clone(this.state.permission);
    } else if (operation === "docs.get_service_health") {
      result = clone(this.state.service);
    } else if (operation === "docs.probe_access") {
      const accessible = this.#isAccessible();
      result = {
        subject_ref: this.state.subject.subject_id,
        application_ref: this.state.service.application_ref,
        accessible,
        reason_category: accessible ? "ok" : "auth_failure",
        probe_id: `probe-${this.runId}-${this.toolCalls.length + 1}`
      };
    } else if (operation === "iam.unlock_account") {
      if (!authorization.plan_hash || authorization.policy_decision !== "AUTO_ALLOW") {
        throw new GatewayError(
          "POLICY_DENIED",
          "unlock requires an AUTO_ALLOW decision bound to a plan hash",
          403
        );
      }
      if (!authorization.idempotency_key) {
        throw new GatewayError("IDEMPOTENCY_REQUIRED", "write call requires an idempotency key");
      }
      if (targetRef !== this.state.account.account_ref) {
        throw new GatewayError("TARGET_MISMATCH", "write target does not match the frozen plan", 403);
      }
      if (parameters.expected_object_version !== this.state.account.version) {
        throw new GatewayError(
          "STALE_TARGET",
          "account version changed after planning; collect fresh evidence and create a new plan",
          409
        );
      }
      if (this.idempotency.has(authorization.idempotency_key)) {
        return clone(this.idempotency.get(authorization.idempotency_key));
      }

      if (this.mode !== "fake_success") {
        this.state.account.locked = false;
        this.state.account.version += 1;
      }
      result = {
        accepted: true,
        external_receipt: `iam-receipt-${this.runId}`,
        message: this.mode === "fake_success"
          ? "Provider accepted the request, but the sandbox intentionally kept the state unchanged."
          : "Account unlock accepted."
      };
    } else {
      throw new GatewayError("TOOL_NOT_FOUND", `unknown operation ${operation}`, 404);
    }

    const observedAt = this.now();
    const evidence = this.#recordEvidence({ actor, operation, result, observedAt });
    const response = {
      schema_version: "1.0",
      tool_call_id: toolCallId,
      run_id: this.runId,
      actor,
      operation,
      target_ref: targetRef,
      parameters_redacted: clone(parameters),
      authorization: {
        policy_decision_id: authorization.policy_decision_id ?? null,
        plan_hash: authorization.plan_hash ?? null,
        idempotency_key: authorization.idempotency_key ?? null
      },
      status: "SUCCEEDED",
      requested_at: requestedAt,
      observed_at: observedAt,
      data: clone(result),
      evidence_id: evidence.evidence_id
    };

    this.toolCalls.push(response);
    if (operation === "iam.unlock_account") {
      this.idempotency.set(authorization.idempotency_key, response);
    }
    return clone(response);
  }
}
