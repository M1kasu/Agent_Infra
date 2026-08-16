# 11 · Demo Script（Demo 剧本）

## 一句话 Demo

> 员工 Alice 报障：“我的这个文档显示没有权限访问，无法打开。”——屏幕提示指向权限，多源证据却定位为账号锁定。OfficeOps 通过 AgentTeams 协调 Context、Diagnosis、Remediation/Verification Worker，查询 IAM、VPN、权限和服务证据，排除权限/网络/服务后确认账号锁定并受限解锁；只有重新观测到账号未锁定且功能访问恢复才完成，Tool 伪报成功时则拒绝关单。

## 展示目标

在 6 分钟内让评委清楚看到：

1. 这是企业办公 IT 的真实任务，不是三个聊天机器人；
2. Agent 有职责、上下文和工具权限差异；
3. AgentTeams 完成真实委派和结构化交接；
4. Skill 负责能力，MCP/Tool 负责连接；
5. 系统执行了真实 Sandbox 状态变化；
6. Tool Success 不等于 Task Success；
7. Trace/Evidence 可回放，且高风险动作存在审批边界；
8. 当前 Case 可以扩展成打印机、会议室、VPN、钉钉等场景包。

## Demo 前置状态

```text
input.message: “我的这个文档显示没有权限访问，无法打开。”
subject: alice
employment_status: active
identity.active: true
identity.locked: true
vpn.enabled: true
docs.permission: granted
docs.service_health: healthy
docs.accessible: false
docs.access_reasons: account_locked（当前 Sandbox 直接暴露根因；目标态收紧为粗粒度 auth_failure——account_locked 必须由 Diagnosis 从 IAM 证据推导，见 07 T3）
```

Agent/Tool 边界：

- Manager：无企业业务 Tool；
- Context Worker：只看到 IAM/VPN/Permission/Health/Access 只读 Tool；
- Diagnosis Worker：只读取 Context/Evidence，无写 Tool；
- Remediation/Verification Worker：仅看到受限 unlock 与复验 Tool；
- 高风险 permission grant 不在 allowlist，必须审批且 MVP 默认不执行。

## 分镜表

| # | 环节 | 屏幕/操作 | 讲解重点 | 得分点 | 时长 |
| :-: | --- | --- | --- | --- | ---: |
| 1 | 场景与价值 | 展示 Alice 报障原文（“我的这个文档显示没有权限访问，无法打开”）和传统人工跨后台流程 | 一句“没有权限”的提示可能来自身份、权限、应用或网络任一层——报障人只见症状 | 场景价值 | 30s |
| 2 | 通用架构 | 一页 OfficeOps Core + Scenario Pack + Adapter 图 | Docs 是第一个验证切片；打印机、VPN、钉钉通过场景包扩展 | 行业复制性 | 30s |
| 3 | 任务进入 AgentTeams | 在 Element/Matrix 发结构化工单；显示 Manager 和 Worker | Manager 必须依次委派，不能代替 Worker 推断 | AgentTeams、任务拆解 | 30s |
| 4 | Context 采集 | 展示 Context Worker 的 5 次只读 MCP 调用和 JSON | 多源事实、来源、时间、角色只读权限 | MCP、Context、Evidence | 50s |
| 5 | Diagnosis | 展示完整 Context 交接和 Diagnosis Worker 输出 | 屏幕提示指向权限，证据排除权限/VPN/服务后支持 account_locked——提示是症状不是根因；无写权限。可选加映：换一种说法的报障（规范化为同一 WorkItem——同义变体轨迹可以相同，以正确为准）或同症异因 Case（应当走出不同轨迹） | Multi-Agent、Skill | 40s |
| 6 | 策略与执行 | 展示风险决定、unlock ToolCall、幂等键和 Sandbox 前后状态 | 仅普通账号锁定允许受限动作；permission grant 会进入审批/被阻断 | 安全、工具调用 | 40s |
| 7 | 独立语义验证 | 展示 fresh IAM read 和 Docs access probe | 接口 success 不是完成；后置条件必须同时满足 | Validation | 40s |
| 8 | Fake Success | 切换已录制/快速运行：Tool success 但状态不变 | Verification 失败、有界重试后 FAILED，不误关单 | 异常、可靠性 | 45s |
| 9 | Trace 与证据 | 打开 result、tool_calls、verification、trace/transcript | 谁、何时、用哪个 Skill/Tool、为什么完成都可回放 | 可观测、审计 | 30s |
| 10 | 扩展与结尾 | 展示场景映射表 | 同一 Core 支持打印机/会议室/VPN/钉钉，但复赛先补闭环再扩 | 开源、演进 | 25s |

总时长约 6 分钟。

## 推荐讲解词主线

### 开场

“OfficeOps 解决的不是某一台打印机或某一个账号，而是企业办公 IT 任务长期依赖人工跨系统接力的问题。我们用一个已经跑通的 Docs 访问故障证明通用协同底座。”

### 多 Agent

“Context Worker 能读取多个系统但不能写；Diagnosis Worker 只能从证据判断；修复 Worker 只持有受限动作。拆分来自职责和凭据隔离，不是为了凑三个角色。验证与执行分离——不能让做手术的人宣布手术成功。”

### 核心亮点

“OfficeOps 不以回答问题为完成标准，以问题恢复为完成标准。解锁接口返回成功，只能说明工具接收了请求。OfficeOps 会重新读取 IAM 状态并重新探测 Docs。只有 `locked=false` 且 `accessible=true` 才算解决用户问题。”

### 通用性

“打印机、会议室、VPN 和钉钉不会被塞进同一个 Prompt。它们以 Scenario Pack 声明对象、上下文、Skill、策略和验证，并通过 Adapter 接入；Manager、状态、审批、执行门禁和 Evidence 不需要重写。”

## 屏幕证据顺序

1. WorkItem/input；
2. AgentTeams Manager/Worker 资源状态；
3. Worker Skill 和 MCP Tool allowlist；
4. Context JSON 与 Evidence；
5. Diagnosis JSON；
6. Sandbox `locked: true → false`；
7. Tool receipt 与 Verification 的对照；
8. Fake Success 的 FAILED 结果；
9. Matrix transcript、Trace 时间线和最终报告；
10. 通用场景包映射。

## 安全审批展示

当前账号解锁按策略是 L1，可自动但必须验证。为展示审批边界，可以在同一界面输入/展示一个 `permission_missing` 计划：

```text
recommended_action: grant_docs_permission
risk: L2
policy: REQUIRE_APPROVAL
execution_tool_calls: 0
```

这只是安全分支证据，不在现场真的授予权限。复赛实现 Human Approval 后，再展示“申请 → 人批准 → 执行”的完整 L2 分支。

## Fake Success 剧本

1. 打开故障注入 `fake_success=true`；
2. Tool 返回 `success=true`，但不改变 `locked`；
3. Verifier 重新读取到 `locked=true` 且 Docs 不可访问；
4. Manager 进入有界重试；
5. 第二次仍失败，终态 `FAILED`；
6. 报告明确“工具成功，业务状态未恢复，事件未关闭”。

## 风险预案

| 风险 | 预案 |
| --- | --- |
| AgentTeams/容器启动失败 | 提前保持已部署环境；准备同一 commit 的完整录屏和 Evidence 包 |
| LLM 响应慢或格式漂移 | 使用固定输入、Schema 重试；准备本地确定性 Orchestrator 作为工程对照，不冒充 AgentTeams 结果 |
| 企业系统无法连接 | 明确 Sandbox 是契约一致的有状态测试环境，展示真实状态变化和 MCP 边界 |
| Fake Success 运行耗时 | 使用提前生成的同版本 Artifact/Trace，保留现场一键脚本 |
| 变体/同症异因演示不稳定 | 回放提前录制的同版本变体 Trace；主叙事不受影响 |
| 评委质疑场景太窄 | 立即展示核心/场景/Adapter 三层和 VPN/打印机场景映射，不切换到未实现 Demo |
| 评委质疑审批 | 展示 L2 Policy 分支、Gateway 拒绝证据和复赛人审实现计划 |
| 页面不可用 | 关键 Evidence 生成静态报告/截图；讲解仍按相同 run_id 串联 |

## Demo 通过标准

- 三个 Worker 有真实回传且顺序正确；
- Context/Diagnosis 无写工具；
- Sandbox 状态真实变化；
- Verification 使用执行后的新鲜读取/探针；
- 正常 Case 完成，Fake Success Case 不完成；
- 每个关键结论和调用可追溯到 Evidence；
- 6 分钟内完成主叙事；
- 不宣称未实现的真实钉钉、打印机、VPN、审批或官方观测接入。

## 相关文档

- 上游：[05 协作流程](05-agent-workflow.md) · [09 安全设计](09-security-design.md) · [10 评估计划](10-evaluation-plan.md)
