# OfficeOps Agent 初赛方案 PPT 文案（12 页）

## 第 1 页｜OfficeOps Agent

**面向企业数字办公环境的零人工 IT 运维多 Agent 系统**

一句话定位：让企业 SaaS 访问故障从“人工跨后台排查”变为可诊断、可执行、可验证、可审计的自动闭环。

核心主张：**Diagnose → Act → Verify**。

初赛聚焦：Alice 无法访问 Docs 的 `account_lock` 单场景最小可运行原型。

---

## 第 2 页｜真实问题：一次“打不开”背后是多系统协作

员工只看到：“我突然打不开公司 Docs 了，昨天还能用。”

IT 人员却要依次完成：识别员工与应用 → 查 IAM → 查 VPN → 查应用权限 → 查服务健康 → 判断根因 → 登录后台修复 → 再次确认。

可能根因包括账号锁定、身份停用、VPN 关闭、权限丢失、Docs 故障和未知策略。人工流程慢、上下文分散、操作证据不连续，还容易把“接口返回成功”误当成“员工已经恢复”。

价值目标：缩短常见事件恢复时间，减少重复操作，并把每次诊断、执行和验证沉淀为复用资产。

---

## 第 3 页｜为什么普通 Chatbot / 单 Agent 不够

普通方案常见链路：工单关键词 → 固定脚本。例如看到“打不开 Docs”就调用 `unlock_account()`，既可能修错，也缺少权限边界。

单 Agent 同时拥有信息收集、决策和写权限，会造成：

- 上下文与结论混在自由文本中，难追踪证据；
- 决策者同时执行，职责与权限无法隔离；
- Tool 返回 `success=true` 后容易直接关闭工单；
- 失败时难判断该重试、升级还是停止；
- 能力写死在 Docs 场景，难迁移到其他 SaaS。

OfficeOps 用不同身份和权限的 Agent 承担“采集、诊断、执行/验证”，由 Manager 维护结构化共享状态。

---

## 第 4 页｜整体方案：Diagnose → Act → Verify

输入层：用户请求转为 `StructuredIncident {user, application, statement}`，Demo 明确 user=alice、application=docs；流程不依赖关键词选择修复动作。

业务闭环：

```text
Incident
  → Collect Context (IAM + VPN + Permission + Health + Access)
  → Diagnose Root Cause
  → Risk Check
  → Execute Tool
  → Re-observe State
  → Functional Access Probe
  → Complete / Retry / Fail Closed
```

基础设施分层：Agent → Skill → Tool → Mini Enterprise Sandbox。任何 Agent 都不能绕过 Tool 直接访问企业系统。

---

## 第 5 页｜4 Agent 架构与真实分工

**Manager Agent**：接收结构化事件、拆解串行依赖、分配角色、维护状态、控制一次重试、汇总结果；不具备企业写权限。

**Context Agent**：只读 IAM/VPN/权限/服务/访问状态，输出 `EmployeeContext + Evidence`；不诊断、不修复。

**Diagnosis Agent**：只读取 Context，以环境状态判断根因，输出置信度、证据和建议动作；未知情况不猜测。

**Remediation & Verification Agent**：仅执行风险策略允许的账号解锁，随后重新读取 IAM 并执行 Docs 功能访问探测；工具确认与验证结论分离。

初赛合并 Remediation 与 Verification，避免为满足形式增加空壳 Agent；复赛随动作类型增多再拆分。

---

## 第 6 页｜AgentTeams v1.2.2 协作设计

已核对官方最新稳定版 v1.2.2 与 `agentteams.io/v1beta1` 契约。

映射：OfficeOps Manager → AgentTeams `Manager`；三个职能 Agent → 三个 standalone `Worker`。初赛不引入额外 Team Leader，Manager 可直接协调 standalone Worker；扩展成多个 IT 工作域时再引入 `Team`。

传递契约：Human 在 Matrix DM 发工单，Manager 在现有 Worker 房间串行委派；每个阶段返回结构化 JSON，Manager 将完整 Context 内联给 Diagnosis，再将完整 Diagnosis 与幂等 `task_id` 内联给 Remediation。runner 审计本轮发送者、顺序、内容和最终状态。MinIO 用于配置、Skill 与文件同步基础设施，后续大对象再切换为版本化引用。

真实状态：官方 v1.2.2 源码已固定拉取；Controller、Manager、3 个 Worker、Matrix、MinIO 与 Higress 已运行；4 个 Skill 已同步，角色隔离 MCP 已由 Worker 实际发现并调用。工单 `agentteams-account-lock-20260815-074611` 的四项协议审计全部通过，状态为 **DONE**。

---

## 第 7 页｜Skill + Tool：能力与连接解耦

四个可复用 Skill：

1. `EmployeeContextSkill`：Incident → EmployeeContext；依赖 IAM/VPN/Application/Health Tool；LOW。
2. `AccessDiagnosisSkill`：Context → DiagnosisResult；证据不足返回 unknown；LOW。
3. `AccountRemediationSkill`：Diagnosis → ExecutionRecord；仅 account_locked；MEDIUM。
4. `AccessVerificationSkill`：重新读取状态 + 功能探测 → VerificationResult；LOW。

每个 Skill 明确定义 name、description、input/output schema、pre/postconditions、risk、dependencies 和 failure handling。

Tool 层提供 IAMTool、VPNTool、ApplicationTool、ServiceHealthTool；底层可切换 InMemory、HTTP Client 或 MCP。Context Worker 的 MCP 仅暴露 5 个只读查询，Remediation Worker 的 MCP 仅暴露 unlock、身份重读和访问复验。

官方推荐组件取舍：初赛不把自研 Skill 冒充云 Skills，也不引入 Nacos、PolarDB、UnifiedModel、RocketMQ；Higress 已随 AgentTeams 部署，但 OfficeOps MCP 目前仍是角色隔离直连，下一步迁入 Consumer；现有轻量 Trace 不冒充 LoongSuite、AgentScope Studio 或 AgentLoop。逐项状态见官方工具链映射表。

---

## 第 8 页｜核心闭环：Tool Success ≠ Task Success

传统闭环在 `unlock_account() → {success: true}` 后结束。OfficeOps 把执行确认与业务验证拆开：

```text
Execute: IAMTool 返回 success=true
Observe: 重新 GET /users/alice
Verify: locked=false AND GET /apps/docs/access/alice.accessible=true
Decision: COMPLETED / RETRYING / FAILED
```

验证使用新的读取与功能探测，不能复用执行响应或旧 Context。成功要求账号状态和真实访问同时恢复。所有状态迁移、Skill、Tool 调用和验证结论进入同一 trace。

---

## 第 9 页｜Demo：Alice Docs 访问恢复

初始 Sandbox：Docs healthy；VPN enabled；Docs permission exists；Alice locked=true。

官方 AgentTeams 实际运行：Manager 接收 Matrix 工单 → Context Worker 调用 5 次只读 MCP Tool → Diagnosis Worker 输出 `account_locked`、confidence=1.0、`unlock_account` → Remediation Worker 以 task_id 为幂等键执行解锁 → 重新读取账号并探测 Docs access → `locked=false` 且 `accessible=true` → Manager 输出 `OFFICEOPS_DONE`。

实际结果：1 次执行；三位 Worker 的实际回传、先后顺序、Sandbox 前后状态和 Manager 终态均保存到 `artifacts/agentteams/agentteams-account-lock-20260815-074611/`。本地确定性路径另生成 input/context/diagnosis/tool_calls/verification/trace/result 等证据文件。

最终反馈：“检测到账号因连续认证失败被锁定，已完成解锁并重新验证 Docs 访问，当前访问已恢复。”

---

## 第 10 页｜异常 Demo：Fake Success 被抓住

故障注入 `fake_success=true` 后，Sandbox 的 unlock 接口仍返回 `success=true`，但故意不修改 `alice.locked`。

实际运行结果：第一次 Tool 成功 → Verification 读取 locked=true、access=false → Manager 进入 `RETRYING` → 第二次 Tool 仍成功 → Verification 仍失败 → `FAILED`，事件不关闭。

这证明系统判断的不是“API 有没有报错”，而是“目标状态是否达到”。一次有界重试避免无限循环；完整 trace 可区分 Tool acknowledgement 与 observed state。

---

## 第 11 页｜创新点、差异化与复制性

**创新 1：多源上下文驱动根因诊断。** Ticket + Identity + VPN + Permission + Health + Access 共同支撑结论，避免关键词脚本。

**创新 2：执行—观察—验证闭环。** 将 Tool Success 与 Task Success 解耦，并通过 Fake Success 形成可演示、可测试的反例。

**创新 3：企业 IT Skill Infra。** Skill 定义业务能力，Tool 定义系统契约，AgentTeams 定义协作；替换 Docs 为 Wiki、Jira、GitLab、CRM 或 OA 时复用诊断、风险和验证框架。

差异化：不以“大模型说得像”作为完成证据，而以结构化状态、真实环境变更、功能探测和 trace 判断闭环。

---

## 第 12 页｜开放计划与演进路线

当前开放资产：Apache-2.0 代码；4 Agent Identity；4 个 AgentTeams Skill 包；IAM/VPN/Application/Health Tool 与 MCP 契约；Mini Enterprise Sandbox；Fake Success 测试；共享状态与 artifacts 规范；AgentTeams v1.2.2 资源清单、真实 transcript 与审计证据。

初赛已完成：本地 account_lock 正常/异常闭环、官方 AgentTeams 真实三 Worker 闭环、13 项自动测试、比赛映射、作品简介和 PPT 文案。

复赛最优先：

1. 将已运行的角色隔离 MCP 经 Higress Consumer 统一鉴权、限流和审计；
2. 拆分 Verification Agent，并实现 High/Critical 人工审批；
3. 增加 VPN/权限/服务异常三类根因与补偿策略；
4. 接入官方观测后端并建立准确率、闭环率、误执行率、恢复步数与成本实验。

原则：先把一个闭环做真，再扩场景与生产设施。
