# 05 · Agent Workflow（Agent 协作流程）

## 通用生命周期

```text
WorkItem 输入
  ↓
Manager：创建 Run、拆解和路由
  ↓
Context Agent：规范化 + 多源只读采集 + ContextSnapshot
  ↓
Diagnosis & Planning Agent：选择 ScenarioPack + Diagnosis/ActionPlan
  ↓
Policy & Approval Agent：AUTO_ALLOW / REQUIRE_APPROVAL / DENY
  ↓
Execution Agent：按冻结计划和最小权限幂等执行
  ↓
Verification Agent：新鲜观测 + 功能探测 + 用户确认（通知关单与经验沉淀由后置管道处理）
  ↓
Manager：完成/补偿/升级；归档 Evidence、Trace 和 ExperienceCandidate
```

### Incident 与 ServiceRequest 的差异

| 类型 | Context 后的主要产物 | 示例 |
| --- | --- | --- |
| Incident / Alert | 先 Diagnosis，再产生修复 ActionPlan | Docs 不可访问、打印机离线、投屏失败 |
| ServiceRequest / Change | 根据目标直接生成 ActionPlan | VPN 开通、软件安装、设备领用 |
| LifecycleEvent | 发现受影响对象后生成批量 ActionPlan | 入职、转岗、离职、权限到期 |

它们从 Policy、Execution、Verification 开始复用同一安全闭环。

## 混合编排：哪些环节是工作流，哪些是 Agent 决策

| 环节 | 执行路径由谁决定 | 为什么 |
| --- | --- | --- |
| 输入规范化 | Agent（S1） | 自由文本无法穷举为规则；变体输入正是 LLM 价值所在 |
| 初筛（场景候选） | Agent（S1 输出候选，TRIAGING 定最小查询集） | 查哪些工具取决于候选场景；初筛阶段禁止任何写动作 |
| 上下文采集 | Agent（S2，目标态动态） | 下一步查什么取决于已有证据的缺口 |
| 诊断与规划 | Agent（S4） | 多源证据裁决、候选排除、未知识别 |
| 路由/分流 | Agent（TeamLeader，目标态真路由） | G02/G04/G06/G11 的去向取决于内容判断 |
| 策略与审批 | 确定性代码 | 合规流程必须可预测、可审计；LLM 只生成解释 |
| 执行 | 确定性代码 + 冻结计划 | 写操作零自由度 |
| 验证断言 | 场景包预定义 + 独立执行 | “能否完成”的判定权不交给执行者或模型自评 |

一句话：**安全链路是工作流，认知环节是 Agent**——需要判断的地方交给模型，必须可靠的地方交给代码。状态机与 Gate 由确定性服务持有，TeamLeader 不能凭模型输出跳过。Agent 决策环节（路由、采集顺序）均记录进 Trace，可与固定规则基线对比评测（见 10）。

## 当前 Golden Path：Docs 账号锁定

```text
员工 Alice 报障：我的这个文档显示没有权限访问，无法打开
  ↓
OfficeOps Manager（官方基础拓扑直连 Workers；目标态为 TeamLeader）：创建 access incident，委派 Context
  ↓
Context Worker（只读 MCP）：
  ├─ IAM: active=true, locked=true
  ├─ VPN: enabled=true
  ├─ Permission: docs granted=true
  ├─ Service Health: healthy
  └─ Functional Probe: accessible=false
  ↓ EmployeeContext + Evidence
Diagnosis Worker：排除 VPN/权限/服务问题，输出 account_locked
  ↓ Diagnosis + recommended_action=unlock_account
Policy：中风险、前置证据满足，允许受限自动动作
  ↓
Remediation Worker（受限写 MCP）：unlock_account(idempotency_key)
  ↓
Verification：重新读取 IAM + 重新探测 Docs
  ├─ locked=false
  └─ accessible=true
  ↓
Manager：OFFICEOPS_DONE + 报告 + Trace
```

当前原型把 Remediation 与 Verification 放在同一 Worker，但要求使用新的查询和功能探测。目标架构将 Verification 拆为独立只读 Worker；文档不会把当前实现误称为完全独立验证 Agent。

## 详细时序

| # | 交互 | Artifact / 状态 | Gate |
| :-: | --- | --- | --- |
| 1 | Channel → Manager | WorkItem `RECEIVED` | 输入不可变、分配 run_id/trace_id |
| 2 | Manager → Context | `NORMALIZING/TRIAGING` | 规范化输出场景候选与最小事实需求；初筛禁止写动作 |
| 3 | Context → Read Tools | `COLLECTING_CONTEXT/CLASSIFYING` Observation/Evidence | 按候选场景最小需求起步，再按证据缺口追加（目标态动态采集）；场景由证据确认，而非预设 |
| 4 | Context → Manager | ContextSnapshot | 缺关键事实则 BLOCKED |
| 5 | Manager → Diagnosis/Planning | ContextRef + Scenario candidates | Worker 真实返回，不允许 Manager 代答 |
| 6 | Diagnosis/Planning → Manager | Diagnosis + ActionPlan | 结论引用 Evidence，步骤有前后置条件 |
| 7 | Manager → Policy/Approval | PlanRef + plan_hash | 风险决定由确定性策略产生 |
| 8 | Policy → Human（按需） | Approval | 高风险缺审批不能进入执行 |
| 9 | Manager → Execution | Frozen Plan + token | Gateway 二次校验角色、参数、风险、哈希 |
| 10 | Execution → Manager | Execution + receipts | Tool Success 不是终态 |
| 11 | Manager → Verification | DesiredOutcome + ExecutionRef | 必须获取执行后新鲜观测 |
| 12 | Verification → Manager | PASS/FAIL/INCONCLUSIVE | PASS 才能完成；FAIL 补偿/升级 |
| 13 | Manager → Channel | 结果说明和报告 | 按场景决定是否等待用户确认 |
| 14 | 后置经验管道 | ExperienceCandidate | 由已完成 Run 离线生成；评测和人工审核后才进入正式知识 |

## 任务拆解与并行

- **可并行**：HR/SSO、设备、网络、应用健康、CMDB 等只读采集；每项独立留证。
- **必须串行**：Plan → Policy/Approval → Execution → Verification。
- **路由依据**：WorkItem 类型、ManagedObject subtype、依赖图、风险、场景包版本和 Tool 可用性。
- **任务粒度**：每个 Task 产生一个可 Schema 校验的 Artifact；禁止只返回“已处理”。

## 上下文传递

| 交接 | 传递 | 不传递 |
| --- | --- | --- |
| Context → Diagnosis | ContextSnapshot、Evidence 引用、缺失/冲突 | 与任务无关的人员隐私、全量日志 |
| Diagnosis → Policy | ActionPlan、风险摘要、plan_hash、证据 | 模型内部思维过程、无关历史对话 |
| Policy → Execution | 冻结步骤、审批/策略令牌、最小对象引用 | 原始自由文本、无关身份信息 |
| Execution → Verification | DesiredOutcome、回执和执行前后引用 | 执行者的成功结论、旧 Context 缓存 |
| Verification → Manager | 新鲜观测、断言、报告、失败原因 | 未脱敏工具响应 |

大对象存 Evidence/Artifact Store；Matrix 只传 `artifact_ref + hash + schema_version`。短 Demo 可内联 JSON，但仍保留同一 Schema。

## 冲突仲裁

优先级：**安全不变量 > 确定性策略 > 权威数据源 > 新鲜观测 > Agent 结论 > 历史经验**。

| 冲突 | 处理 |
| --- | --- |
| 数据源事实冲突 | 按企业权威源和新鲜度选择；无规则则 BLOCKED |
| 两个场景包都匹配 | 输出候选、影响和需要补充的信息；不盲选写动作 |
| Plan 与 Policy 冲突 | Policy 优先；Planner 根据违规项重规划并生成新哈希 |
| Tool 回执与状态冲突 | Verification 新鲜观测优先，任务不得完成 |
| Worker 输出不合 Schema | Manager 退回原 Worker，不能自行补业务字段 |
| 用户否认恢复 | 转人工或重新收集上下文，不覆盖用户证据 |

## 风险与审批

| 风险 | 例子 | 流程 |
| --- | --- | --- |
| L0 | 查询设备、账号、日志、健康 | 自动执行并留痕 |
| L1 | 已确认普通账号解锁、生成报告 | 策略自动或单人确认，必须验证 |
| L2 | VPN/应用权限开通、重启共享设备、改网络配置 | 人工审批后执行 |
| L3 | 管理员权限、通配资源、生产关键服务、批量账号 | 双人审批或默认禁止 |

当前 Golden Path 只自动执行被策略限定的 L1 账号解锁；若诊断为 `permission_missing`，系统只能生成 L2 计划和审批请求，不能自动授权。

## 异常分支

| 异常 | 行为 | 结果 |
| --- | --- | --- |
| 输入缺少对象/位置/账号 | 返回结构化追问 | NEED_MORE_INFO |
| Tool 超时/429 | 有界退避；写超时先查状态 | RETRYING/UNKNOWN |
| 未知根因 | 不猜写动作，附 Evidence 升级 | MANUAL_TRIAGE |
| 审批拒绝/超时 | 终止计划，无写 ToolCall | REJECTED/EXPIRED |
| 执行部分失败 | 逆序补偿或人工介入 | COMPENSATING |
| Tool 伪报成功 | Verification 判 FAIL；不得关单 | FAILED |
| 验证环境不可用 | 返回 INCONCLUSIVE，不伪造 PASS | RETRY_VERIFYING |
| Agent 结论相互矛盾 | Policy/权威事实仲裁或人工评审 | BLOCKED |
| Evidence/Trace 无法保存 | 对后续写操作 fail closed | FAILED |

## As-Is / To-Be

| 环节 | 传统人工 | OfficeOps |
| --- | --- | --- |
| 输入 | 群聊、电话、OA 字段不一致 | 统一 WorkItem，按场景追问缺项 |
| 采集 | 人工登录多个后台 | 只读 Agent 并行采集并留 Evidence |
| 判断 | 依赖个人经验 | 场景 Skill + 证据化 Diagnosis/Plan |
| 审批 | 审批人难看清实际动作 | 审批冻结计划、风险、验证与补偿 |
| 执行 | 手工点击或散落脚本 | 最小权限 Tool、幂等和状态记录 |
| 验证 | 看到接口成功就回复 | 新鲜状态、功能探针和用户确认 |
| 复盘 | 聊天记录/工单备注 | Trace、报告、评测样本和经验候选 |

## 一次 Run 的 Evidence

- 原始及规范化 WorkItem；
- 身份、资产、网络、应用、权限和健康 Observation；
- ContextSnapshot 与内容哈希；
- Diagnosis、备选根因和 ActionPlan；
- PolicyDecision、Approval 和计划哈希；
- ToolCall、幂等键、回执、执行前后快照；
- Verification 正/负向断言和用户确认；
- 补偿、通知、最终报告、Trace 和 ExperienceCandidate。

## 相关文档

- 上游：[03 领域模型](03-domain-model.md) · [04 Agent 身份](04-agent-identities.md)
- 下游：[06 Skill 清单](06-skill-catalog.md) · [09 安全设计](09-security-design.md) · [11 Demo 剧本](11-demo-script.md)
