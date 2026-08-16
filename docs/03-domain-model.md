# 03 · Domain Model（领域建模）

## 有界上下文

OfficeOps 负责“企业数字办公任务的协同处置生命周期”，不成为 HR、CMDB、ITSM、设备平台或云平台的主数据系统。

```text
Channel/ITSM ── WorkItem ── OfficeOps Workflow
HR/CMDB/SSO/Monitoring ── Observation / ManagedObject
Device/SaaS/VPN/Cloud/K8s ── Tool Adapter / Execution
Knowledge/Audit ── Evidence / Trace / Evaluated Experience
```

## 通用语言

| 概念 | 定义 |
| --- | --- |
| WorkItem | 待处理的 Incident、ServiceRequest、Change、Alert 或 LifecycleEvent。 |
| Subject | 报告人、申请人、受影响人、服务账号或审批人。 |
| ManagedObject | 被管理或被依赖的对象，如账号、打印机、会议设备、应用、服务、网络端点、资源。 |
| Relationship | 对象间的依赖、归属、连接、成员、授权或部署关系。 |
| Observation | 某数据源在某时刻观测到的事实，可能过期或与其他来源冲突。 |
| Evidence | 被固化、可校验并被结论引用的 Observation、工具结果、审批或报告。 |
| Diagnosis | 根因候选、置信度、证据和排除项。 |
| ActionPlan | 目标状态、步骤、风险、前后置条件和补偿方案。 |
| DesiredOutcome | 场景完成条件；决定验证什么，而非只看工具回执。 |
| ScenarioPack | 某专业场景的 Schema、Skill、策略、工具需求、验证规则和评测案例。 |
| Adapter | 把稳定 Tool 能力映射到厂商 API、CLI、RPA 或 Sandbox 的实现。 |

## 核心实体总览

| 实体 | 作用 |
| --- | --- | :--: |
| WorkItem | 统一任务输入 |
| Subject | 人员/账号参与者快照 |
| ManagedObject / Relationship | 资产、服务、账号与依赖图 |
| Observation / Evidence | 事实和证据链 |
| ContextSnapshot | 一次判断使用的版本化上下文 |
| Diagnosis | Incident/Alert 的根因判断 |
| ActionPlan / ActionStep | 处置或服务请求计划 |
| DesiredOutcome | 可机器判断的完成条件 |
| PolicyDecision / Approval | 风险和人审 |
| Execution | 动作、回执和补偿 |
| Verification | 新鲜观测与业务验证 |
| AgentIdentity / SkillSpec | 多 Agent 职责和能力 |
| ToolDefinition / ToolCall | 外部能力和调用轨迹 |
| WorkflowRun / Task | 状态机和协作单元 |
| Trace / Memory / KnowledgeDocument | 观测与经验演进 |

## 字段级定义

### WorkItem

```text
WorkItem
├── work_item_id: string
├── type: INCIDENT|SERVICE_REQUEST|CHANGE|ALERT|LIFECYCLE_EVENT
├── source_channel: DINGTALK|OA|ITSM|ELEMENT|MONITORING|API
├── source_record_id: string
├── requester: SubjectRef
├── affected_subjects: SubjectRef[]
├── title: string
├── description: string
├── reported_objects: ManagedObjectRef[]
├── location: string?
├── impact: SINGLE_USER|TEAM|SITE|ENTERPRISE
├── urgency: LOW|MEDIUM|HIGH|CRITICAL
├── requested_window: TimeWindow?
├── attachments: EvidenceRef[]
├── status: WorkItemStatus
├── scenario_hint: string?
├── schema_version: string
└── created_at/updated_at: datetime
```

原始输入不可覆盖；规范化结果以新版本保存。缺失关键字段时进入 `NEED_MORE_INFO`，不得由模型猜测。

### Subject

```text
Subject
├── subject_id: string
├── type: EMPLOYEE|CONTRACTOR|SERVICE_ACCOUNT|GROUP|APPROVER
├── display_name: string
├── organization/position/manager_id: string?
├── employment_status: ACTIVE|SUSPENDED|TERMINATED|UNKNOWN
├── account_refs: {provider, external_id, status}[]
├── attributes: object
├── observed_at: datetime
└── evidence_ids: string[]
```

Subject 是 Run 内快照，不回写 HR/OA 主数据。Subject 与 ManagedObject 在 Person/Account/Group 上存在重叠：实现前统一为 EntityRef 引用机制（entity_type + entity_id + source_system + tenant_id + external_ref），关系两端均为 EntityRef——复赛收敛（见 00 复赛演进 W4），当前文档保持两套名称。

### ManagedObject

```text
ManagedObject
├── object_id: string
├── kind: PERSON|ACCOUNT|DEVICE|APPLICATION|SERVICE|NETWORK|RESOURCE|GROUP
├── subtype: string                  # printer/vpn_account/meeting_display/docs_app/...
├── canonical_name: string
├── provider: string
├── external_ref: string?
├── environment_class: OFFICE            # 业务场景维度（办公侧/生产侧）
├── deployment_env: DEV|TEST|PROD|UNKNOWN  # 部署环境维度，两者不混用
├── location: string?
├── owner_ref: SubjectRef?
├── lifecycle_state: string
├── sensitivity: PUBLIC|INTERNAL|SENSITIVE|CRITICAL
├── attributes: object               # 由 subtype Schema 校验
├── observed_at: datetime
└── evidence_ids: string[]
```

ManagedObject 是系统记录（IAM/HR/CMDB/MDM）的引用快照，不是 OfficeOps 维护的主数据；OfficeOps 在对象层的增量只有关系、观测与证据。

厂商特有字段只能进入经过版本化 Schema 校验的 `attributes`，不得成为通用 Workflow 的硬编码条件。

### Relationship

```text
Relationship
├── relationship_id: string
├── type: DEPENDS_ON|OWNED_BY|LOCATED_IN|CONNECTED_TO|MEMBER_OF|GRANTS|RUNS_ON
├── from_object_id/to_object_id: string
├── attributes: object
├── valid_from/valid_until: datetime?
├── source: string
├── observed_at: datetime
└── evidence_id: string
```

关系图允许回答：Docs 依赖哪个身份系统、某会议室使用哪个网络、某 VPN 账号属于哪个账号组、某办公服务运行在哪个容器。

### Observation / Evidence

```text
Observation
├── observation_id: string
├── subject_ref/object_ref: string?
├── fact_type: string
├── value: any
├── source: string
├── source_ref: string?
├── observed_at: datetime
├── expires_at: datetime?
├── confidence: number
└── sensitivity: PUBLIC|INTERNAL|SENSITIVE|SECRET

Evidence
├── evidence_id: string
├── run_id/task_id: string
├── type: INPUT|OBSERVATION|KNOWLEDGE|PLAN|POLICY|APPROVAL|TOOL_RESULT|VERIFICATION|REPORT
├── source: string
├── content_ref: string
├── content_hash: string
├── observed_at: datetime
├── collected_by: string
├── sensitivity: string
├── retention_until: datetime
└── previous_hash: string?
```

Observation 可以冲突；Evidence 是供决策引用的固化事实。每个关键结论必须引用 Evidence ID。

### ContextSnapshot

```text
ContextSnapshot
├── context_id/run_id: string
├── work_item_ref: string
├── subjects: Subject[]
├── objects: ManagedObject[]
├── relationships: Relationship[]
├── observations: Observation[]
├── source_versions: {source, version, observed_at}[]
├── missing_facts/conflicts: string[]
├── freshness_deadline: datetime
├── evidence_ids: string[]
├── content_hash: string
└── created_at: datetime
```

### Diagnosis

```text
Diagnosis
├── diagnosis_id: string
├── scenario_id/version: string
├── root_cause: string
├── confidence: number
├── alternatives: {cause, confidence, evidence_ids}[]
├── supporting_evidence_ids: string[]
├── excluded_causes: {cause, evidence_ids}[]
├── recommended_action: string?
├── need_more_facts: string[]
├── status: CONFIRMED|PROBABLE|UNKNOWN
└── created_at: datetime
```

工具结果若直接携带原因，也只能作为证据之一；ScenarioPack 决定最小证据集，避免 Diagnosis Agent 仅复述单个字段。

### ActionPlan / ActionStep / DesiredOutcome

```text
ActionPlan
├── plan_id/run_id: string
├── scenario_id/version: string
├── context_id/diagnosis_id: string?
├── target_state: object
├── steps: ActionStep[]
├── alternatives: PlanAlternative[]
├── risk_summary: string
├── verification_spec: DesiredOutcome
├── status: DRAFT|VALIDATED|PENDING_APPROVAL|APPROVED|SUPERSEDED|EXECUTED
├── plan_hash: string
└── created_at: datetime

ActionStep
├── step_id: string
├── capability/operation: string
├── target_ref: string
├── parameters: object
├── depends_on: string[]
├── preconditions/postconditions: Assertion[]
├── compensation: ActionStep?
├── risk_level: L0|L1|L2|L3
└── idempotency_key_template: string

DesiredOutcome
├── assertions: Assertion[]
├── positive_probes: ProbeSpec[]
├── negative_probes: ProbeSpec[]
├── user_confirmation_required: boolean
├── evidence_requirements: string[]
└── timeout/retry_policy: object
```

Incident 可以先产生 Diagnosis 再产生 ActionPlan；ServiceRequest 可从规范化需求直接产生 ActionPlan。二者在 Policy 之后复用同一执行与验证生命周期。

### PolicyDecision / Approval

```text
PolicyDecision
├── decision_id/plan_id/plan_hash: string
├── result: AUTO_ALLOW|REQUIRE_APPROVAL|DENY|NEED_MORE_CONTEXT
├── risk_level: L0|L1|L2|L3
├── matched_rules: {rule_id, version, outcome}[]
├── required_approver_roles: string[]
├── explanation: string
├── policy_bundle_version: string
└── evidence_ids: string[]

Approval
├── approval_id/plan_id/plan_hash: string
├── approver_id/role: string
├── decision: PENDING|APPROVED|REJECTED|EXPIRED|REVOKED
├── channel/external_ref: string
├── comment: string?
├── decided_at/expires_at: datetime
├── signature: string
└── evidence_id: string
```

策略结果由确定性代码产生；LLM 可解释规则，但不能覆盖结果。审批必须绑定计划哈希。

### Execution / Verification

```text
Execution
├── execution_id/run_id/plan_id/plan_hash: string
├── approval_ids: string[]
├── status: PENDING|RUNNING|PARTIAL|SUCCEEDED|FAILED|COMPENSATING|COMPENSATED
├── before_snapshot_ref: string
├── step_results: {step_id, tool_call_id, status, receipt}[]
├── compensation_results: object[]
├── started_at/finished_at: datetime
└── evidence_ids: string[]

Verification
├── verification_id/run_id/execution_id: string
├── observed_state: object
├── assertion_results: AssertionResult[]
├── probe_results: ProbeResult[]
├── user_confirmation: object?
├── result: PASS|FAIL|INCONCLUSIVE
├── freshness: {observed_at, sources}
├── reason: string
└── evidence_ids: string[]
```

Verification 必须使用执行后的新鲜 Observation，不得复用 Execution Agent 的“成功”判断。

完成采用三态独立语义：`tool_status`（单次 ToolCall 回执）、`execution_status`（Execution 步骤汇总）、`verification_status`（独立新鲜观测判定）互不推导；`task_status` 仅由 `verification_status=PASS` 且 DesiredOutcome 全满足决定。三者不一致时以最新鲜观测为准，任务不得 COMPLETED。

### AgentIdentity / SkillSpec

```text
AgentIdentity
├── agent_id/role/mission: string
├── input_schemas/output_schemas: string[]
├── skill_allowlist/tool_allowlist: string[]
├── data_scope: string[]
├── risk_ceiling: L0|L1|L2|L3
├── forbidden_actions: string[]
├── failure_policy: string
└── identity_version: string

SkillSpec
├── skill_id/name/version/purpose: string
├── scenario_compatibility: string[]
├── trigger_conditions: string[]
├── input_schema/output_schema: object
├── preconditions/postconditions: Assertion[]
├── tool_dependencies: string[]
├── failure_policy/risk_boundary: object
├── evaluation_cases: string[]
└── artifact_uri: string
```

### ToolDefinition / ToolCall

```text
ToolDefinition
├── tool_name/version/protocol/provider: string
├── capabilities: OperationSpec[]
├── auth_scopes: string[]
├── risk_by_operation: object
├── idempotency/audit support: boolean
└── availability/degradation policy: object

ToolCall
├── tool_call_id/run_id/task_id/trace_id: string
├── agent_id/skill_id/tool_name/operation: string
├── target_ref: string?
├── input_redacted/input_hash: object|string
├── idempotency_key/plan_hash/approval_id: string?
├── status: REQUESTED|SUCCEEDED|FAILED|UNKNOWN
├── output_redacted/external_receipt: object|string?
├── retryable: boolean
├── started_at/finished_at: datetime
└── evidence_id: string
```

### WorkflowRun / Task

```text
WorkflowRun
├── run_id/work_item_id/trace_id: string
├── scenario_id/scenario_version: string?
├── status/current_stage: string
├── task_ids/artifact_refs/evidence_ids: string[]
├── context_id/diagnosis_id/plan_id: string?
├── approval_ids/execution_id/verification_id: string[]|string?
├── result_summary/failure_code: string?
├── version: integer
└── created_at/updated_at/completed_at: datetime

Task
├── task_id/run_id/type/status: string
├── assigned_agent: AgentIdentityRef
├── input_ref/output_ref: ArtifactRef
├── parent_task_id: string?
├── attempt/deadline: integer|datetime
└── created_at/updated_at: datetime
```

## 实体关系

```text
WorkItem 1 ── 0..* WorkflowRun ── * Task          # 重开任务创建新 Run，引用旧 Run 证据
WorkflowRun ── * ContextRevision / DiagnosisRevision / ActionPlanRevision
WorkflowRun 只保存 current_*_ref；历史版本由 revision/artifact 关系保存
ContextSnapshot ── * Subject / ManagedObject / Relationship / Observation
WorkflowRun ── 0..1 Diagnosis ── 1 ActionPlan
ActionPlan ── 1 PolicyDecision ── * Approval
ActionPlan ── 0..1 Execution ── 0..1 Verification
所有对象 ── * Evidence
ScenarioPack ── * SkillSpec / Policy / ToolRequirement / GoldenCase
```

五个状态互不混用，各有归属：`WorkItem.status`（外部业务记录状态）、`WorkflowRun.status`（本次自动化处理状态）、`Task.status`（单次 Agent 委派状态）、`Execution.status`（副作用执行状态）、`Verification.status`（业务结果验证状态）。完成判定只由 Verification 驱动，任何一层不得代设其他层状态。

## 状态机

```text
RECEIVED
  → NORMALIZING                    # 规范化输出含 ScenarioCandidates + 最小事实需求
  → TRIAGING                       # 初筛只产生场景候选与最小查询集，禁止任何写动作
  → COLLECTING_CONTEXT             # 按候选场景的最小事实需求取证（目标态：按证据缺口动态追加）
  → CLASSIFYING                    # 场景由证据确认——不知道场景不知查哪些工具、不采集上下文又无法确认场景的循环依赖在此打断
      ├─ NEED_MORE_INFO → BLOCKED → NORMALIZING
      ├─ ROUTED                     # 归属其他场景/团队（如 VPN、服务故障）
      └─ SCENARIO_SELECTED
  → DIAGNOSING_OR_PLANNING
      ├─ UNKNOWN → MANUAL_TRIAGE
      └─ PLAN_READY
  → POLICY_CHECK
      ├─ DENIED
      ├─ AUTO_ALLOWED ────────────┐
      └─ WAITING_APPROVAL         │
            ├─ REJECTED/EXPIRED   │
            └─ APPROVED ──────────┘
  → EXECUTING
      ├─ SECURITY_BLOCKED           # 越权调用被 Gateway 拦截，转安全审计，不补偿不重试
      ├─ FAILED → COMPENSATING → FAILED|MANUAL_INTERVENTION
      └─ EXECUTED
  → VERIFYING
      ├─ PASS → USER_CONFIRMING? → COMPLETED
      ├─ FAIL → COMPENSATING|MANUAL_INTERVENTION
      └─ INCONCLUSIVE → RETRY_VERIFYING|MANUAL_INTERVENTION
  → REVIEW_CANDIDATE
```

## 核心不变量

1. 无有效 ActionPlan 不得执行写操作。
2. 写操作必须匹配 Agent Tool Allowlist、风险上限和计划哈希。
3. L2/L3 动作缺审批时，Tool Gateway 必须再次拒绝。
4. Execution Agent 不得修改计划或自行扩大目标范围。
5. Verification 使用独立只读身份和新鲜 Observation。
6. 只有 DesiredOutcome 全部满足才能 `COMPLETED`。
7. Tool 状态为 UNKNOWN 时先查询真实状态，不盲目重放。
8. 关键结论必须引用 Evidence；缺证据返回 UNKNOWN/INCONCLUSIVE。
9. 未经评测和人工评审的 Run 不得直接写入正式知识或 Skill。
10. 新场景优先扩展 ScenarioPack 和 Adapter；不能自然映射时建立新有界上下文。

## 场景映射验证

| 核心概念 | Docs 访问 | VPN 申请 | 打印机故障 | 会议室投屏 |
| --- | --- | --- | --- | --- |
| ManagedObject | account, docs service | vpn account/group/resource | printer, queue, network | display, source, network |
| Observation | locked(含 lock_reason), permission, health | identity, group, binding | online, queue, toner | signal, firmware, network |
| Diagnosis/Plan | account_locked → unlock | create/bind entitlement | queue/network/device plan | input/network/device plan |
| DesiredOutcome | unlocked + accessible | effective access exact | test page success | display probe/user confirm |
| Tool Adapter | IAM/Application | VPN/HR/OA | Printer/CMDB | Meeting/Network |

## 相关文档

- 上游：[00 产品提案](00-product-proposal.md) · [02 用户故事](02-user-stories.md)
- 下游：[04 Agent 身份](04-agent-identities.md) · [07 Tool 契约](07-tool-mcp-contract.md) · [08 系统设计](08-system-design.md)
