# 初赛要求映射

状态只使用 `DONE`、`PARTIAL`、`NOT IMPLEMENTED`，以当前仓库和实际运行证据为准。

| 比赛要求 | OfficeOps 对应方案 | 当前状态 | 证据 |
|---|---|---|---|
| >=3 Agent | Manager + Context + Diagnosis + Remediation & Verification，共 4 个职能角色 | DONE | `app/agents/`、`docs/AGENT_IDENTITIES.md` |
| AgentTeams | 官方 v1.2.2 Controller、Manager、3 standalone Worker、Matrix、MinIO、Higress 已运行；真实三阶段 Matrix 工单和协议审计通过 | DONE | `agentteams/UPSTREAM.md`、`docs/AGENTTEAMS_MAPPING.md`、`artifacts/agentteams/agentteams-account-lock-20260815-074611/` |
| Agent Identity | 输入、输出、权限、上下游、风险与失败策略清单 | DONE | `app/agents/identities.py`、`docs/AGENT_IDENTITIES.md` |
| Skill | EmployeeContext、AccessDiagnosis、AccountRemediation、AccessVerification 四个可执行/可分发 Skill | DONE | `app/skills/`、`agentteams/skills/` |
| Tool | IAM/VPN/Application/ServiceHealth Tool，支持 InMemory、HTTP 和两组角色隔离 MCP SSE | DONE | `app/tools/enterprise.py`、`sandbox/mcp_server.py` |
| Enterprise Sandbox | FastAPI + 有状态 Python 服务，包含要求的 6 个业务接口和故障注入接口 | DONE | `sandbox/enterprise.py`、`sandbox/api.py` |
| Context | StructuredIncident、EmployeeContext、Evidence、TaskState | DONE | `app/models/domain.py`、运行 `context.json` |
| Shared State | 完整状态机与结构化 TaskState | DONE | `app/workflows/manager.py`、运行 `task_state.json` |
| Root Cause Diagnosis | 多源状态驱动 account_locked / service / identity / VPN / permission / unknown 分支 | DONE | `app/skills/access.py`、`test_account_locked`、`test_unknown_root_cause` |
| Remediation | 风险策略约束、幂等账号解锁、真实 Sandbox 状态变化 | DONE | `AccountRemediationSkill`、`test_successful_unlock` |
| Result Verification | 重新读取 IAM + 功能访问探测，不信任 Tool acknowledgement | DONE | `AccessVerificationSkill`、`test_verification_after_unlock` |
| Fake Success | Tool 返回成功但状态不变；验证失败、一次重试后 FAILED | DONE | `demo-fake-success` artifacts、`test_fake_success_detection` |
| Observability | task_id/trace_id、Agent/Skill/Tool/状态/验证事件、Matrix transcript、协议审计及必需 artifact | DONE | `app/observability/`、`artifacts/runs/`、`artifacts/agentteams/agentteams-account-lock-20260815-074611/` |
| Safety | LOW/MEDIUM 自动、HIGH/CRITICAL 代码级阻断；真实审批/回滚尚未实现 | PARTIAL | `app/skills/base.py`、`docs/SECURITY.md` |
| Automated Tests | 13 个 pytest 单元/场景/API/MCP 权限测试 | DONE | `tests/`；实跑 `13 passed` |
| README / Quick Start | 3 分钟导览、Demo、测试、状态与路线 | DONE | `README.md` |
| 500 字作品简介 | 覆盖名称、问题、方案、创新、差异、开放价值、进展 | DONE | `competition/preliminary/作品简介.md` |
| 12 页 PPT 文案 | 场景、架构、协作、Skill/Tool、验证、异常、安全、计划 | DONE | `competition/preliminary/PPT_CONTENT.md` |
| RAG / Agent Memory | 初赛不使用；以 Shared State + Trace 满足上下文增强至少两项 | NOT IMPLEMENTED | 设计取舍见 README |
| Human Approval / Rollback | 仅有风险门禁，未实现人审交互和通用回滚 | NOT IMPLEMENTED | `docs/SECURITY.md` |
| 官方推荐工具链 | 已逐项记录 AgentTeams、云 Skills、Nacos、Higress、PolarDB、UnifiedModel、RocketMQ 和官方可观测工具的真实状态与取舍 | DONE | `docs/OFFICIAL_TOOLCHAIN_MAPPING.md` |
