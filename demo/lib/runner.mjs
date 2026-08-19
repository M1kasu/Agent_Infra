import { createHash, randomUUID } from "node:crypto";

import policyBundle from "../../scenarios/access-incident/policy.json" with { type: "json" };
import verificationSpec from "../../scenarios/access-incident/verification-spec.json" with { type: "json" };
import { createLogicalClock } from "./clock.mjs";
import { MockToolGateway } from "./mock-gateway.mjs";
import { stableStringify } from "./stable-json.mjs";

export const DEFAULT_MESSAGE = "我的这个文档显示没有权限访问，无法打开。";

function digest(value) {
  return `sha256:${createHash("sha256").update(stableStringify(value)).digest("hex")}`;
}

function artifactRef(runId, name) {
  return `artifact://runs/${runId}/${name}.json`;
}

function normalizeInput({ runId, message, now }) {
  const scenarioScore = /(文档|docs|权限|访问|打开)/i.test(message) ? 0.94 : 0.42;
  return {
    schema_version: "1.0",
    work_item_id: `wi-${runId}`,
    type: "INCIDENT",
    source_channel: "WEB_DEMO",
    requester: { entity_type: "EMPLOYEE", entity_id: "employee:alice" },
    affected_subjects: [{ entity_type: "EMPLOYEE", entity_id: "employee:alice" }],
    title: "Docs access failure",
    description: message,
    impact: "SINGLE_USER",
    urgency: "MEDIUM",
    status: "NORMALIZED",
    scenario_candidates: [
      {
        scenario_id: "access-incident",
        confidence: scenarioScore,
        basis: "User reports a document access symptom; no root cause label is supplied."
      }
    ],
    created_at: now()
  };
}

function evaluatePolicy({ diagnosis, actionPlan, context, now }) {
  const rule = policyBundle.rules[0];
  const conditions = {
    employment_status: context.subject.employment_status,
    account_active: context.account.active,
    is_admin: context.subject.is_admin,
    lock_reason: context.account.lock_reason
  };
  const matches =
    diagnosis.root_cause === "account_locked" &&
    actionPlan.steps[0]?.operation === rule.operation &&
    Object.entries(rule.conditions).every(([key, expected]) => conditions[key] === expected);

  return {
    schema_version: "1.0",
    policy_decision_id: `pd-${actionPlan.run_id}`,
    plan_id: actionPlan.plan_id,
    plan_hash: actionPlan.plan_hash,
    policy_id: policyBundle.policy_id,
    policy_version: policyBundle.version,
    decision: matches ? rule.decision : policyBundle.default_decision,
    risk_level: matches ? rule.risk_level : "L2",
    matched_rules: matches ? [rule.rule_id] : [],
    explanation: matches
      ? "Active non-admin account with an automatic lock may use the bounded L1 unlock path."
      : "The plan does not satisfy the automatic unlock policy.",
    decided_at: now()
  };
}

function verifyOutcome({ runId, gateway, execution, now, trace }) {
  const accountRead = gateway.call({
    actor: "verification-agent",
    operation: "iam.get_account_state",
    targetRef: "iam://corp/alice"
  });
  trace("tool_call", "verification-agent", "VERIFYING", {
    operation: accountRead.operation,
    evidence_id: accountRead.evidence_id
  });

  const accessProbe = gateway.call({
    actor: "verification-agent",
    operation: "docs.probe_access",
    targetRef: "app://docs"
  });
  trace("tool_call", "verification-agent", "VERIFYING", {
    operation: accessProbe.operation,
    evidence_id: accessProbe.evidence_id
  });

  const assertions = verificationSpec.assertions.map((spec) => {
    const actual = spec.fact === "iam.account.locked"
      ? accountRead.data.locked
      : accessProbe.data.accessible;
    return {
      assertion_id: spec.assertion_id,
      fact: spec.fact,
      expected: spec.expected,
      actual,
      passed: actual === spec.expected,
      evidence_ids: spec.fact === "iam.account.locked"
        ? [accountRead.evidence_id]
        : [accessProbe.evidence_id]
    };
  });
  const passed = assertions.every((assertion) => assertion.passed);

  return {
    schema_version: "1.0",
    verification_id: `verify-${runId}`,
    run_id: runId,
    execution_id: execution.execution_id,
    status: passed ? "PASS" : "FAIL",
    fresh_observation_required: true,
    assertions,
    observed: {
      account_locked: accountRead.data.locked,
      docs_accessible: accessProbe.data.accessible
    },
    evidence_ids: [accountRead.evidence_id, accessProbe.evidence_id],
    verified_at: now()
  };
}

export function runOfficeOpsDemo({
  message = DEFAULT_MESSAGE,
  mode = "normal",
  runId = `run-${randomUUID().slice(0, 8)}`,
  clockStart
} = {}) {
  if (!new Set(["normal", "fake_success"]).has(mode)) {
    throw new TypeError(`unsupported demo mode: ${mode}`);
  }
  if (typeof message !== "string" || !message.trim()) {
    throw new TypeError("message must be a non-empty string");
  }

  const now = createLogicalClock(clockStart);
  const traceEvents = [];
  let traceSequence = 0;
  const trace = (eventType, agent, stage, detail = {}) => {
    traceSequence += 1;
    traceEvents.push({
      sequence: traceSequence,
      trace_id: `trace-${runId}`,
      run_id: runId,
      event_type: eventType,
      agent,
      stage,
      occurred_at: now(),
      detail
    });
  };

  const gateway = new MockToolGateway({ runId, mode, now });
  const startedAt = now();
  trace("run_started", "officeops-team-leader", "RECEIVED", { mode });

  const workItem = normalizeInput({ runId, message: message.trim(), now });
  trace("artifact_created", "officeops-team-leader", "NORMALIZING", {
    artifact_ref: artifactRef(runId, "normalized_work_item"),
    scenario_candidates: workItem.scenario_candidates
  });
  trace("task_delegated", "officeops-team-leader", "COLLECTING_CONTEXT", {
    recipient: "context-agent",
    required_response_schema: "ContextSnapshot@1.0"
  });

  const subjectRead = gateway.call({ actor: "context-agent", operation: "iam.get_subject" });
  const accountRead = gateway.call({ actor: "context-agent", operation: "iam.get_account_state" });
  const dynamicReason = accountRead.data.locked
    ? "Account is locked; collect permission, service, VPN and functional evidence before deciding causality."
    : "Account is not locked; collect downstream access evidence."
  const vpnRead = gateway.call({ actor: "context-agent", operation: "vpn.get_state" });
  const permissionRead = gateway.call({
    actor: "context-agent",
    operation: "docs.get_effective_permissions"
  });
  const healthRead = gateway.call({
    actor: "context-agent",
    operation: "docs.get_service_health"
  });
  const initialProbe = gateway.call({ actor: "context-agent", operation: "docs.probe_access" });
  for (const call of gateway.toolCalls) {
    trace("tool_call", "context-agent", "COLLECTING_CONTEXT", {
      operation: call.operation,
      evidence_id: call.evidence_id,
      status: call.status
    });
  }

  const context = {
    schema_version: "1.0",
    context_id: `ctx-${runId}-1`,
    run_id: runId,
    revision: 1,
    subject: subjectRead.data,
    account: accountRead.data,
    vpn: vpnRead.data,
    permission: permissionRead.data,
    service: healthRead.data,
    access_probe: initialProbe.data,
    acquisition_strategy: {
      type: "evidence_gap_driven",
      reason: dynamicReason
    },
    evidence_ids: [
      subjectRead.evidence_id,
      accountRead.evidence_id,
      vpnRead.evidence_id,
      permissionRead.evidence_id,
      healthRead.evidence_id,
      initialProbe.evidence_id
    ],
    missing_facts: [],
    conflicts: [],
    collected_at: now()
  };
  trace("artifact_created", "context-agent", "CONTEXT_READY", {
    artifact_ref: artifactRef(runId, "context"),
    evidence_count: context.evidence_ids.length
  });
  trace("task_delegated", "officeops-team-leader", "DIAGNOSING", {
    recipient: "diagnosis-planning-agent",
    context_ref: artifactRef(runId, "context")
  });

  const rootCauseSupported =
    context.subject.employment_status === "ACTIVE" &&
    context.account.active &&
    context.account.locked &&
    context.account.lock_reason === "auto_lock" &&
    context.vpn.enabled &&
    context.permission.granted &&
    context.service.status === "HEALTHY" &&
    !context.access_probe.accessible;
  const diagnosis = {
    schema_version: "1.0",
    diagnosis_id: `diag-${runId}-1`,
    run_id: runId,
    scenario_id: "access-incident",
    scenario_version: "0.1.0",
    status: rootCauseSupported ? "CONFIRMED" : "UNKNOWN",
    root_cause: rootCauseSupported ? "account_locked" : "unknown",
    confidence: rootCauseSupported ? 0.97 : 0.35,
    causal_summary: rootCauseSupported
      ? "The active account is automatically locked while VPN, effective permission and service health are valid; the functional probe reports an authentication failure."
      : "Available evidence does not support a bounded automatic action.",
    rejected_hypotheses: rootCauseSupported
      ? ["permission_missing", "vpn_disabled", "service_unhealthy"]
      : [],
    evidence_ids: context.evidence_ids,
    created_at: now()
  };

  const planDraft = {
    schema_version: "1.0",
    plan_id: `plan-${runId}-1`,
    run_id: runId,
    revision: 1,
    scenario_id: "access-incident",
    context_ref: artifactRef(runId, "context"),
    diagnosis_ref: artifactRef(runId, "diagnosis"),
    target_state: { account_locked: false, docs_accessible: true },
    steps: rootCauseSupported
      ? [
          {
            step_id: "unlock-account",
            capability: "identity-controlled-write",
            operation: "iam.unlock_account",
            target_ref: context.account.account_ref,
            parameters: {
              reason_code: "account_locked",
              ticket_ref: workItem.work_item_id,
              expected_object_version: context.account.version
            },
            risk_level: "L1",
            preconditions: ["employment active", "lock_reason auto_lock", "non-admin account"]
          }
        ]
      : [],
    desired_outcome_ref: "verification-spec://access-restored@0.1.0",
    created_at: now()
  };
  const actionPlan = { ...planDraft, plan_hash: digest(planDraft), status: "VALIDATED" };
  trace("artifact_created", "diagnosis-planning-agent", "PLAN_READY", {
    diagnosis: diagnosis.root_cause,
    plan_hash: actionPlan.plan_hash,
    evidence_ids: diagnosis.evidence_ids
  });

  const policyDecision = evaluatePolicy({ diagnosis, actionPlan, context, now });
  trace("policy_evaluated", "policy-engine", "POLICY_CHECK", {
    decision: policyDecision.decision,
    matched_rules: policyDecision.matched_rules,
    plan_hash: policyDecision.plan_hash
  });

  let execution;
  if (policyDecision.decision === "AUTO_ALLOW") {
    trace("task_delegated", "officeops-team-leader", "EXECUTING", {
      recipient: "execution-agent",
      plan_hash: actionPlan.plan_hash
    });
    const before = gateway.snapshot().account;
    const toolResult = gateway.call({
      actor: "execution-agent",
      operation: "iam.unlock_account",
      targetRef: actionPlan.steps[0].target_ref,
      parameters: actionPlan.steps[0].parameters,
      authorization: {
        policy_decision: policyDecision.decision,
        policy_decision_id: policyDecision.policy_decision_id,
        plan_hash: actionPlan.plan_hash,
        idempotency_key: `${runId}:${actionPlan.plan_hash}:unlock-account`
      }
    });
    trace("tool_call", "execution-agent", "EXECUTING", {
      operation: toolResult.operation,
      status: toolResult.status,
      evidence_id: toolResult.evidence_id
    });
    execution = {
      schema_version: "1.0",
      execution_id: `exec-${runId}`,
      run_id: runId,
      plan_id: actionPlan.plan_id,
      plan_hash: actionPlan.plan_hash,
      status: toolResult.status === "SUCCEEDED" ? "SUCCEEDED" : "FAILED",
      tool_status: toolResult.status,
      before_snapshot: before,
      provider_receipt: toolResult.data.external_receipt,
      evidence_ids: [toolResult.evidence_id],
      finished_at: now()
    };
  } else {
    execution = {
      schema_version: "1.0",
      execution_id: `exec-${runId}`,
      run_id: runId,
      plan_id: actionPlan.plan_id,
      plan_hash: actionPlan.plan_hash,
      status: "DENIED",
      tool_status: "NOT_CALLED",
      evidence_ids: [],
      finished_at: now()
    };
  }

  trace("task_delegated", "officeops-team-leader", "VERIFYING", {
    recipient: "verification-agent",
    execution_ref: artifactRef(runId, "execution"),
    note: "The verifier receives the receipt but not the executor's completion opinion."
  });
  const verification = verifyOutcome({ runId, gateway, execution, now, trace });
  const status = verification.status === "PASS" ? "COMPLETED" : "FAILED";
  trace("verification_completed", "verification-agent", "VERIFYING", {
    status: verification.status,
    assertions: verification.assertions
  });
  trace("run_finished", "officeops-team-leader", status, {
    technical_status: status,
    tool_status: execution.tool_status,
    verification_status: verification.status
  });

  const completedAt = now();
  const result = {
    schema_version: "1.0",
    run_id: runId,
    trace_id: `trace-${runId}`,
    mode,
    status,
    root_cause: diagnosis.root_cause,
    tool_status: execution.tool_status,
    execution_status: execution.status,
    verification_status: verification.status,
    message: status === "COMPLETED"
      ? "账号已受限解锁，并通过新鲜 IAM 状态和 Docs 功能探针确认访问恢复。"
      : "工具回执成功，但账号状态或 Docs 功能访问未恢复；事件未关闭。",
    started_at: startedAt,
    completed_at: completedAt
  };

  return {
    result,
    artifacts: {
      input: { message: message.trim(), mode },
      normalized_work_item: workItem,
      context,
      diagnosis,
      action_plan: actionPlan,
      policy_decision: policyDecision,
      execution,
      verification,
      tool_calls: gateway.toolCalls,
      evidence: gateway.evidence,
      trace: traceEvents
    }
  };
}
