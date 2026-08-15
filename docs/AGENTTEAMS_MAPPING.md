# OfficeOps × AgentTeams 架构映射

## 核对基线与真实状态

核对日期：2026-08-15。

- 官方入口：[hiclaw.io](https://hiclaw.io/)
- 最新代码仓库：[agentscope-ai/AgentTeams](https://github.com/agentscope-ai/AgentTeams)
- 最新稳定版：[v1.2.2](https://github.com/agentscope-ai/AgentTeams/releases/tag/v1.2.2)
- 官方协作设计：[Kubernetes-native multi-Agent orchestration](https://github.com/agentscope-ai/AgentTeams/blob/main/docs/design/k8s-native-orchestration.md)
- 当前 API：`agentteams.io/v1beta1`，核心资源为 `Manager`、`Worker`、`Team`、`Human`。
- 当前协作基础：Matrix 房间传递可见消息，MinIO 保存共享文件，Higress 以 Consumer token 隔离真实凭据。
- v1.2.2 已提供 Manager 向 Worker 校验、上传、分配自定义 Skill 的能力。

当前接入状态：**DONE**。官方 v1.2.2 源码固定在独立路径 `E:\code\AgentTeams-upstream`；Controller、Manager、3 个 Worker、Matrix、MinIO 与 Higress 均已实际运行。四个 Skill 已同步到对应 Worker，两组 MCP 服务按角色暴露不同 Tool。真实 Matrix 工单 `agentteams-account-lock-20260815-074611` 已完成 Context → Diagnosis → Remediation & Verification 串行协作，协议审计与最终状态审计全部通过。

“必须使用 AgentTeams”不等于复制框架源码。本仓库维护 OfficeOps 的 Worker Identity、Skill、MCP Tool、资源清单和业务契约；官方框架仍作为独立上游 checkout 部署，来源与业务改动可以分别核验。

## 角色映射

| OfficeOps | AgentTeams v1.2.2 | 身份与边界 | 代码/配置证据 |
|---|---|---|---|
| Manager Agent | `Manager` CR / Manager Agent | 拆解任务、派发、状态迁移、一次重试、汇总；无企业写权限 | `app/workflows/manager.py`、`agentteams/officeops-workers.yaml` |
| Context Agent | standalone `Worker` | 只读采集 IAM/VPN/权限/服务/访问证据 | `app/agents/workers.py`、`employee-context` Skill |
| Diagnosis Agent | standalone `Worker` | 只读共享上下文；输出根因，不执行动作 | `app/agents/workers.py`、`access-diagnosis` Skill |
| Remediation & Verification Agent | standalone `Worker` | 仅执行策略允许的账号解锁；重新读取状态和功能验证 | `app/agents/workers.py`、两个执行/验证 Skill |

初赛采用三个 standalone Worker，而不是再增加 Team Leader。AgentTeams 官方模型允许 Manager 直接协调 standalone Worker；对本次只有三个串行职能的 Demo，这比引入第五个调度角色更小、更清晰。复赛扩到 IAM、VPN、SaaS 多工作域后再引入 `Team` 和 Team Leader。

## Task / Context / Message / State / Result

| 对象 | OfficeOps 结构 | Local Orchestrator | AgentTeams 映射 |
|---|---|---|---|
| Task | `StructuredIncident` + `task_id` + `trace_id` | Python 对象 | Human → Manager 的 Matrix 工单；`task_id` 同时作为幂等键 |
| Context | `EmployeeContext` | `TaskState.context` | Context Worker 的结构化 JSON，由 Manager 完整内联给 Diagnosis Worker |
| Message | `AgentTeamsEnvelope` | 同进程方法调用 | Manager/Worker Matrix 房间消息，保留 sender、timestamp 与完整 payload |
| State | `TaskState` | 结构化 Pydantic 状态 | 本地路径写 JSON/JSONL；AgentTeams 路径以 Matrix 事件和最终 Sandbox 观测组成事实状态 |
| Result | `DiagnosisResult`、`ExecutionRecord`、`VerificationResult`、`TaskResult` | 写入 run artifacts | Worker 在 Matrix 回传结构化结果，runner 汇集 transcript、协议检查与最终观测 |

## 协作时序

```text
Human → Manager: StructuredIncident + task_id
Manager → Context Worker: incident
Context Worker → Manager: EmployeeContext + evidence
Manager → Diagnosis Worker: complete context JSON inline
Diagnosis Worker → Manager: DiagnosisResult
Manager → Remediation Worker: complete diagnosis JSON + task_id inline
Remediation Worker → Tool: unlock_account(idempotency_key)
Remediation Worker → Tool: re-read IAM + functional access probe
Remediation Worker → Manager: ExecutionRecord + VerificationResult
Manager → Human: OFFICEOPS_DONE only after all Worker and state checks pass
```

本次固定三阶段 Demo 刻意使用 Matrix 内联结构化 JSON，不依赖 taskflow 或共享任务文件：它既验证真实消息传递，也避免引用缺失时 Manager 自行补全结论。MinIO 在当前部署中负责 AgentTeams 配置、Skill 分发与文件同步基础设施；后续大对象场景才启用版本化 `shared_state_ref`。runner 只接受本轮事件，并审计三个 Worker 的真实回传与顺序。

## Adapter 边界

`app/workflows/runtime.py` 定义业务层所需的协调端口；Local Runtime 直接调用三个职能 Agent。官方运行路径由 AgentTeams Manager 经 Matrix 编排 Worker，Worker 通过 MCP 调用同一 Sandbox。`agentteams/adapter.py` 保留了未来大对象走 Matrix/MinIO 引用时的版本化 envelope；两种运行路径不改变领域模型、诊断策略和验证条件。

## 声明式资源与 Skill

`agentteams/officeops-workers.yaml` 提供 1 个 Manager 和 3 个 Worker 的 `v1beta1` 声明。`agentteams/skills/*/SKILL.md` 提供四个可分发 Skill。已完成：

1. 启动 Docker Desktop 并安装官方 v1.2.2；
2. 创建 OfficeOps Manager 和三个 `Running` Worker；
3. 将四个 Skill 同步至角色工作区；
4. 将只读 MCP 绑定 Context，将受限写入 MCP 绑定 Remediation；
5. 以 Matrix 消息跑通 account_lock；
6. 保存本轮房间 transcript、资源快照、协议检查与 Sandbox 前后状态。

证据：`artifacts/agentteams/agentteams-account-lock-20260815-074611/evidence.json` 与同目录 `transcript.md`。

## 仍未声称完成

- OfficeOps MCP 当前按 Worker 配置直接连接两个 SSE 端点，尚未经过 Higress Consumer；
- MinIO 已用于框架配置和 Skill 同步，但本次短消息链未把业务 Context 写成共享任务文件；
- 未录制 AgentTeams UI Demo。
