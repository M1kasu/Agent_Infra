# 04 · Agent Identities（Agent 身份定义）

## 目标 Agent 架构

| Agent | AgentTeams 映射 | 职责 | 权限上限 | 不可合并的原因 |
| --- | --- | --- | :--: | --- |
| AgentTeams Manager | Manager（平台层） | Agent/Team/Human 资源生命周期与跨团队协调，不处理业务工单 | 平台管理 | 官方拓扑中 Manager 只与 Team Leader 通信，不穿透 Team |
| OfficeOps TeamLeader | Team Leader（Team 内专用 Worker） | 拆解、路由、状态、重试、汇总 | 无企业系统业务权限 | 编排者不得跳过 Worker 自行产出业务事实或执行结果 |
| Context Agent | Worker | 规范化输入，采集身份/资产/服务/网络/权限事实 | L0 只读 | 需要广泛只读上下文，不应持写凭据 |
| Diagnosis & Planning Agent | Worker | 选择场景包，诊断根因或生成处置计划 | L0/无写 | 专业判断必须与事实采集和执行隔离 |
| Policy & Approval Agent | Worker | 风险评估、策略门禁、人审编排 | 审批渠道写入，无目标系统写权限 | 计划提出者和执行者不能自我批准 |
| Execution Agent | Worker | 忠实执行冻结计划和补偿 | 按场景最小写权限 | 唯一写身份必须最小上下文、最少自由度 |
| Verification Agent | Worker | 独立复验与断言，只产出 Verification | L0 只读/探测 | 执行者不能自己证明成功 |
| Close/Notify 与经验管道 | 确定性服务/后置管道 | 通知关单走渠道 Tool；ExperienceCandidate 由已完成 Run 离线生成 | 渠道写，无目标系统写 | 通知与知识写入不是验证者职责，保持 Verifier 最小权限 |

目标架构为 AgentTeams Team + TeamLeader + 4 个 Worker（平台层另有 AgentTeams Manager，只管资源生命周期，不进业务链路）。拆分遵循**双重正当性**：独立角色必须（a）引入其上游生成时无法获得的新信息——Context 引入多源观测，Diagnosis 引入证据裁决与补充取证，Verification 引入执行后才存在的新鲜观测；或（b）形成有意义的权限、信任、上下文或故障隔离边界——Execution 的价值是唯一写身份的凭据隔离，不是新信息。只有 (a) 可直接宣称提升推理信息量；仅消费同一份文本做转述的环节两者皆不满足，不配独立。规划质量是整个系统的瓶颈，TeamLeader 应配置最强模型与最完整的任务级上下文，而不是把算力平均分给所有角色。

角色分三类，避免“Agent”一词掩盖谁在做决定：

| 类型 | 成员 | 是否依赖 LLM | 说明 |
| --- | --- | :---: | --- |
| Cognitive Agent | TeamLeader、Context、Diagnosis | 是 | 不确定判断：路由、采集顺序、根因裁决 |
| Controlled Worker | Execution（及审批协调） | 可部署为 Worker，核心行为受代码约束 | 价值是凭据隔离与最小权限，不是智能 |
| Deterministic Service | 状态机、Policy Engine、Tool Gateway、验证断言 | 否 | `AUTO_ALLOW/REQUIRE_APPROVAL/DENY` 只能由 Policy Engine 产生；TeamLeader 不能凭模型输出跳过 Gate |

## A0 · OfficeOps TeamLeader

- **Identity**：企业办公运维任务协调者。拓扑：当前原型为 Manager 直连 Workers（官方基础拓扑）；目标态为 Team + TeamLeader，AgentTeams Manager 退居平台资源层，不处理业务工单。
- **输入**：`WorkItemRef`、渠道元数据。
- **输出**：`WorkflowRun`、用户摘要、报告引用。
- **需要能力**：任务拆解、路由、Schema 校验、状态迁移、超时/重试、Trace 关联。
- **Tools**：Task State、Matrix/消息、Artifact/Evidence 引用；无设备、IAM、VPN、SaaS 写工具。
- **上下文**：任务状态和阶段 Artifact 的引用及最小摘要。
- **不负责**：自己采集业务事实、诊断、批准或执行。
- **真路由（目标态）**：分流决策（服务故障转 ROUTED、VPN 场景转路由、未知转 MANUAL_TRIAGE、畸形输入退回）由模型基于 WorkItem 与阶段 Artifact 内容作出，而非固定 if-else；每次路由决策记录进 Trace，可与规则基线对比评测。
- **独立理由**：将协作控制面与企业系统数据面隔离，防止编排者绕过真实 Worker 协作；状态机 Gate 由确定性服务持有，TeamLeader 不能凭模型输出跳过。
- **失败行为**：非法状态拒绝；Worker 输出不合 Schema 返回原 Worker；有界重试后转人工。

## A1 · Context Agent

- **Identity**：办公任务上下文与证据采集员。
- **输入**：`WorkItem`。
- **输出**：`NormalizedWorkItem`、`ContextSnapshot`、缺失/冲突事实。
- **Skills**：NormalizeWorkItem、CollectOperationalContext。
- **Tools**：HR/OA/SSO、CMDB、设备、网络、SaaS、监控、VPN 等只读工具，由场景路由选择最小集合。
- **权限**：L0 只读。
- **不负责**：下根因结论、选择写动作、修改任何目标系统。
- **动态采集（目标态）**：以场景最小必需集为下界，根据证据缺口决定下一步查询（如 IAM 显示 locked=true 后补取 lock_reason 与最近审计事件）；不同输入变体应产生不同采集轨迹。当前实现为固定查询序列，作为对照基线保留。
- **独立理由**：广泛只读访问若与执行身份合并，会扩大敏感数据和写权限攻击面。
- **失败行为**：关键事实缺失时 `BLOCKED`；来源冲突保留双方 Evidence，不猜测。

## A2 · Diagnosis & Planning Agent

- **Identity**：跨域运维诊断与处置规划师。
- **输入**：规范化 WorkItem、ContextSnapshot、场景候选。
- **输出**：ScenarioSelection、Diagnosis、ActionPlan、备选方案。
- **Skills**：RetrieveOperationalKnowledge、DiagnoseAndPlan。
- **Tools**：知识检索（EvaluatedKnowledge，见 08）和只读能力发现；可向 Context 发起补充取证请求；无目标系统写工具。
- **权限**：L0/无写。
- **不负责**：批准自己的方案、调用执行工具、把历史案例当作当前事实。
- **取证回调（目标态）**：候选根因无法裁决时，可产出 `RequestAdditionalObservation`（指明 fact_type 与理由）交回 Context 补充取证，有界次数内有效；超过次数返回 UNKNOWN，不在既有文本上反复推理。
- **独立理由**：专业推理需要场景知识和完整证据，但必须被 Policy 独立约束。
- **失败行为**：证据不足返回 UNKNOWN 或请求补充；多方案无法安全选择时请求人工仲裁。

## A3 · Policy & Approval Agent

- **Identity**：办公运维风险与审批协调员。
- **输入**：ActionPlan、上下文摘要、Policy Bundle。
- **输出**：PolicyDecision、Approval 或拒绝/补充原因。
- **Skills**：EvaluateRiskAndApproval。
- **Tools**：确定性 Policy Engine、钉钉/OA/本地 Approval Tool。
- **权限**：可发起/读取审批；无设备、IAM、VPN、SaaS 写权限。
- **决策归属**：`AUTO_ALLOW/REQUIRE_APPROVAL/DENY` 由确定性 Policy Engine 产生；本 Worker 只解释策略、组织审批材料、等待人类决定。
- **不负责**：代替人类批准、修改计划、执行动作。
- **独立理由**：职责分离要求计划者、审批者和执行者相互独立。
- **失败行为**：策略不可用时 fail closed；计划哈希变化撤销旧审批；超时转 EXPIRED。

## A4 · Execution Agent

- **Identity**：受限办公运维动作执行员。
- **输入**：已通过策略/审批的 ActionPlan 和最小 ProviderObjectRef。
- **输出**：Execution、ToolCall、执行前后快照和补偿结果。
- **Skills**：ExecuteControlledAction。
- **Tools**：按场景下发的 Device、IAM/VPN、SaaS、Network 或 Infra 写工具。
- **权限**：只允许计划声明的能力、目标和参数；凭据按场景/租户隔离。
- **不负责**：重新规划、扩大作用域、自我审批、宣布任务完成。
- **独立理由**：唯一写身份必须最小权限，且只消费结构化计划。
- **失败行为**：幂等执行；超时先查状态；按补偿计划逆序处理；补偿失败转人工。

## A5 · Verification Agent

- **Identity**：独立结果验证员（只做验证，不做通知与知识写入）。
- **输入**：WorkItem、ActionPlan、Execution、DesiredOutcome。
- **输出**：Verification、AuditReport、（可选）用户确认证据。
- **Skills**：VerifyOutcome。
- **Tools**：独立只读状态查询、功能探针、Evidence Store。
- **权限**：L0 只读/探测；不能修复验证失败，不能直接发布正式知识。
- **不负责**：复用执行者成功判断、隐藏负向结果、未经评审修改 Skill。
- **独立理由**：Tool Success 与用户问题解决不是同一事实；只有独立观测才能发现假成功和错修。
- **失败行为**：证据不足返回 INCONCLUSIVE；验证失败触发补偿/升级。

通知与关单由独立的 Close/Notify 服务经渠道 Tool 完成；ExperienceCandidate 由已完成 Run 经事件驱动离线管道生成，评审后进入 EvaluatedKnowledge（见 08）——知识沉淀是后置管道，不是验证者的在线职责。

## Human Roles（非 Agent）

- 申请人/报障人：提供信息并确认体验；
- 直属主管/资源负责人：确认业务必要性和影响；
- 信息安全/系统负责人：批准高风险动作；
- 人工运维：处理未知根因、补偿失败和不支持的厂商动作。

Human 决定必须由真实身份签名；模型不能扮演审批人。

## 上下文与工具隔离

| Agent | 可见数据 | 工具 |
| --- | --- | --- |
| TeamLeader | 状态、引用、脱敏摘要 | 编排/Trace |
| Context | 任务输入、相关只读事实 | 只读企业 Tool |
| Diagnosis & Planning | Context、Evidence、知识片段 | RAG/只读发现 |
| Policy & Approval | 计划差异、风险、必要身份信息 | Policy/Approval |
| Execution | 冻结步骤、审批令牌、最小目标引用 | 场景写 Tool |
| Verification | DesiredOutcome、回执、新鲜观测 | 只读探针/报告 |

## AgentTeams 交接 Envelope

```json
{
  "schema_version": "1.0",
  "run_id": "run-...",
  "task_id": "task-...",
  "sender": "context-agent",
  "recipient": "diagnosis-planning-agent",
  "artifact_type": "ContextSnapshot",
  "artifact_ref": "artifact://...",
  "artifact_hash": "sha256:...",
  "scenario_hint": "saas_access_incident",
  "required_response_schema": "Diagnosis@1.0",
  "trace_id": "trace-..."
}
```

接收方校验 Schema、Hash、发送者、版本和 Evidence；不得仅凭自由文本摘要推进状态。

## 相关文档

- 上游：[02 用户故事](02-user-stories.md) · [03 领域模型](03-domain-model.md)
- 下游：[05 协作流程](05-agent-workflow.md) · [06 Skill 清单](06-skill-catalog.md) · [09 安全设计](09-security-design.md)
