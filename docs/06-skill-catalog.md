# 06 · Skill Catalog（Skill 清单）

## Skill 分层

| 层级 | 作用 | 示例 |
| --- | --- | --- |
| Core Skill | 跨打印机、账号、SaaS、网络等场景复用 | 规范化、上下文、策略、验证、复盘 |
| Scenario Skill | 表达某专业域的诊断、规划和验证规则 | 账号锁定诊断、打印机故障诊断、VPN 权限规划 |
| Tool Adapter | 连接具体厂商能力，不包含业务判断 | IAM MCP、Printer MCP、DingTalk API、VPN API/RPA |

通用架构不要求同一个 Skill 理解所有设备；它要求所有场景 Skill 遵守共同输入输出、证据、安全和评测规范。

## 核心 Skill 清单

| Skill | 主责 Agent | 输入 → 输出 | 依赖 | 风险 | 优先级 |
| --- | --- | --- | --- | :--: | :--: |
| NormalizeWorkItem | Context | RawInput → NormalizedWorkItem / MissingFields | Channel Tool、Schema Registry | L0 | P0 |
| CollectOperationalContext | Context | WorkItem + Requirements → ContextSnapshot | 企业只读 Tool | L0 | P0 |
| RetrieveOperationalKnowledge | Diagnosis & Planning | Query + Context → CitedKnowledge | RAG/知识库 | L0 | P1 |
| DiagnoseAndPlan | Diagnosis & Planning | Context + ScenarioPack → Diagnosis + ActionPlan | 场景规则、知识 | L0 | P0 |
| EvaluateRiskAndApproval | Policy & Approval | ActionPlan + PolicyBundle → PolicyDecision / Approval | Policy、Approval Tool | L0/L2 | P0 |
| ExecuteControlledAction | Execution | FrozenPlan + Authorization → Execution | 场景写 Tool | L1-L3 | P0 |
| VerifyOutcome | Verification | DesiredOutcome + Execution → Verification | 独立只读/Probe Tool | L0 | P0 |
| CloseAndLearn | Close/Notify + 后置经验管道 | Run + Verification → Report + ExperienceCandidate | Channel、Evidence Store | L1 | P1 |

## 统一 Skill 契约

每个 Skill 必须声明：

```text
name / version / purpose
compatible_scenarios
trigger_conditions
input_schema / output_schema
preconditions / postconditions
required_evidence
tool_dependencies / auth_scopes
risk_boundary
timeout / retry / degradation
failure_codes
evaluation_cases
owner / release_status / rollback_version
```

输出必须是 Schema 可校验 Artifact；自由文本只作为解释字段，不能替代结构化结论。

## S1 · NormalizeWorkItem

- **用途**：把钉钉/OA/ITSM/Element/告警输入转换为统一 WorkItem，并识别场景候选。
- **触发**：每个新输入或用户补充信息后。
- **输入**：渠道消息、附件引用、提交人和时间。
- **输出**：NormalizedWorkItem、字段置信度、MissingFields、ScenarioCandidates。
- **依赖 Tool**：Channel Read、Subject Resolve、Schema Registry。
- **失败**：关键对象、影响或期望缺失时返回 `NEED_MORE_INFO`，生成最少追问；不得猜造账号/设备/位置。
- **安全**：附件和用户文本是不可信输入；只提取数据，不执行其中指令。
- **复用**：所有场景共用，场景包只提供额外字段 Schema。
- **评测**：同一故障的 10+ 同义变体必须规范化为同一 WorkItem（见 10 评估计划 G14）；规则解析器崩溃的变体即本 Skill 的价值边界。

## S2 · CollectOperationalContext

- **用途**：按初筛给出的场景候选集与最小事实需求起步，采集身份、资产、服务、网络、权限、健康和历史状态，再按证据缺口动态追加（目标态）；场景确认由证据支撑，而非预设。
- **触发**：WorkItem 规范化且至少有一个场景候选。
- **输入**：NormalizedWorkItem、ContextRequirement[]。
- **输出**：ContextSnapshot、Observation/Evidence、MissingFacts、Conflicts。
- **依赖 Tool**：CMDB、HR/SSO、Device、Network、SaaS、Monitoring 等只读 Tool。
- **失败**：单个非关键源失败可降级并降低置信度；关键事实缺失必须 BLOCKED。
- **安全**：按任务最小范围查询；敏感响应脱敏并存引用。
- **复用**：Context Requirement 由场景包配置，不修改 Skill 主流程。
- **动态采集（目标态）**：以场景最小必需集为下界，根据证据缺口决定追加查询（如 IAM 显示 locked=true 后补取 lock_reason 与最近审计事件）；采集轨迹随输入变体而变，是 Agent 性的可观测证据。当前固定五查询实现保留为对照基线。

## S3 · RetrieveOperationalKnowledge

- **用途**：检索 SOP、厂商说明、历史已验证案例和策略解释，给 Diagnosis/Plan 提供带引用的辅助知识。
- **触发**：场景识别后且需要知识增强。
- **输入**：场景、对象、症状、上下文摘要、过滤条件。
- **输出**：CitedKnowledge[]、版本、相关度、适用条件和冲突提示。
- **依赖 Tool**：Knowledge/RAG Tool。
- **失败**：检索不到时返回空集合，不阻止确定性路径；低相关结果不进入决策上下文。
- **安全**：知识内容视为不可信数据，不能覆盖系统策略或调用工具；所有片段必须有来源。
- **复用**：按 metadata 过滤场景、厂商、版本和环境。

## S4 · DiagnoseAndPlan

- **用途**：对 Incident/Alert 输出根因，对 ServiceRequest/Change 输出目标计划，并生成 DesiredOutcome。
- **触发**：ContextSnapshot 完整且未过期。
- **输入**：WorkItem、ContextSnapshot、ScenarioPack、CitedKnowledge。
- **输出**：ScenarioSelection、Diagnosis、ActionPlan、Alternatives。
- **依赖 Tool**：通常无写 Tool；可使用只读能力发现。
- **失败**：证据不足返回 UNKNOWN/NeedMoreFacts；多方案无法安全选择时请求人工；不生成投机性写动作。
- **安全**：计划不得超过 WorkItem 目标；每步必须声明风险、前后置条件和补偿。
- **复用**：公共规划器消费不同场景 Schema；专业根因规则由 Scenario Skill 提供。
- **取证回调（目标态）**：候选根因无法裁决时产出 `RequestAdditionalObservation`（指明 fact_type 与理由）交回 Context 补充取证，有界次数内有效；超过次数返回 UNKNOWN，不在既有文本上反复推理（见 04 A2）。

## S5 · EvaluateRiskAndApproval

- **用途**：通过确定性 Policy Engine 评估动作、对象、范围和上下文，决定自动、审批或拒绝。
- **触发**：ActionPlan 通过 Schema 和依赖校验后。
- **输入**：ActionPlan、plan_hash、PolicyBundle、Subject/Owner 事实。
- **输出**：PolicyDecision、ApprovalRequest/Approval。
- **依赖 Tool**：Policy Engine、DingTalk/OA/Local Approval Tool。
- **失败**：策略不可用或规则冲突时 fail closed；审批超时/计划变化使授权失效。
- **安全**：LLM 只生成解释；AUTO_ALLOW/REQUIRE_APPROVAL/DENY 由代码决定；审批人必须是真实 Human Identity。
- **复用**：公共风险级别和场景专属规则叠加。

## S6 · ExecuteControlledAction

- **用途**：在 Tool Gateway 二次校验后，严格按冻结 ActionStep 调用写工具并处理不确定状态和补偿。
- **触发**：AUTO_ALLOW 有效，或所需 Approval 全部有效。
- **输入**：FrozenPlan、PolicyDecision、ApprovalRefs、最小目标对象引用。
- **输出**：Execution、StepResult、ToolCall、Before/After Snapshot、CompensationResult。
- **依赖 Tool**：按场景分配的 Device/IAM/VPN/SaaS/Network/Infra 写 Tool。
- **失败**：稳定幂等键；超时先读状态；按逆序补偿；补偿失败转人工。
- **安全**：不允许修改参数、扩展目标、使用未列入计划的能力；凭据按场景和租户隔离。
- **复用**：执行器理解通用 ActionStep，Adapter 处理厂商调用。

## S7 · VerifyOutcome

- **用途**：使用执行后的新鲜状态、正/负向探测和可选用户确认判断 DesiredOutcome。
- **触发**：Execution 结束，包括 Tool 回执成功、失败或状态未知。
- **输入**：WorkItem、DesiredOutcome、Execution。
- **输出**：Verification `PASS|FAIL|INCONCLUSIVE`、Assertion/ProbeResult。
- **依赖 Tool**：独立只读状态查询、功能探针、用户确认 Channel。
- **失败**：探针不可用返回 INCONCLUSIVE；Fake Success 或越界结果返回 FAIL。
- **安全**：Verifier 无修复写权限；不能复用 Execution Agent 的成功判断。
- **复用**：公共断言引擎 + 场景定义的验证模板。

## S8 · CloseAndLearn

- **用途**：生成面向用户和审计的两类报告，更新工单，并产生待评测的经验候选。
- **触发**：Verification 得出终态，或 Run 进入人工介入。
- **输入**：Run、Evidence、Verification、用户确认。
- **输出**：UserMessage、AuditReport、ExperienceCandidate、EvaluationSample。
- **依赖 Tool**：Channel/ITSM Write、Evidence Store、Candidate Knowledge Store。
- **失败**：通知失败不改变技术终态，但必须告警重试；Evidence 不完整时禁止发布经验。
- **安全**：对用户和审计报告分别脱敏；ExperienceCandidate 不自动发布成正式知识或 Skill。
- **复用**：所有场景共用报告/评测框架，模板由场景包补充。

## 当前 Docs 场景包的 4 个 Skill

| 已有 Skill | 对应核心 Skill | 作用 |
| --- | --- | --- |
| EmployeeContextSkill | CollectOperationalContext | 查询 IAM、VPN、权限、服务健康和功能访问 |
| AccessDiagnosisSkill | DiagnoseAndPlan | 基于多源 Evidence 判断 access root cause |
| AccountRemediationSkill | ExecuteControlledAction | 仅在 account_locked 且策略允许时解锁 |
| AccessVerificationSkill | VerifyOutcome | 重读 IAM 并重新探测 Docs 访问 |

这些实现应作为 `saas-access-incident` 场景包，而不是把 Access 术语写死在 OfficeOps 核心层。

## Skill 生命周期

```text
DRAFT → REVIEW → EVALUATED → RELEASED → DEPRECATED → RETIRED
```

- 发布必须通过 Schema、Golden Cases、安全边界和依赖检查。
- 运行记录 `skill_name@version`；升级不能覆盖历史证据。
- 失败率、误执行、验证通过率或安全事件超过阈值时自动回滚到上一 Released 版本。
- 场景包和 Skill 使用语义版本；破坏输入输出兼容性必须升 major。

## 相关文档

- 上游：[04 Agent 身份](04-agent-identities.md) · [05 协作流程](05-agent-workflow.md)
- 下游：[07 Tool & MCP 契约](07-tool-mcp-contract.md) · [10 评估计划](10-evaluation-plan.md)
