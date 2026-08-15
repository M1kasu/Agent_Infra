# Agent Identity 清单

| 字段 | Manager Agent | Context Agent | Diagnosis Agent | Remediation & Verification Agent |
|---|---|---|---|---|
| Identity | OfficeOps 协调者 | 企业证据采集员 | 访问根因分析员 | 策略约束的修复与独立验证员 |
| Responsibility | 编排、状态、重试、结果 | 采集 IAM/VPN/权限/健康/访问 | 依据结构化上下文诊断 | 解锁、重读状态、功能探测 |
| Inputs | StructuredIncident | StructuredIncident | EmployeeContext | Incident + DiagnosisResult |
| Outputs | TaskState、TaskResult | EmployeeContext | DiagnosisResult | ExecutionRecord、VerificationResult |
| Skills | 无直接业务 Skill | EmployeeContextSkill | AccessDiagnosisSkill | AccountRemediationSkill、AccessVerificationSkill |
| Tools | 无 | IAM/VPN/Application/ServiceHealth | 无 | IAM/Application |
| Permissions | 派发、共享状态、Trace | 只读企业状态 | 只读共享状态 | `unlock_account` + 只读验证 |
| Context / Memory | 当前完整 TaskState | 原始事件 | Context 与 Evidence | 已批准计划、诊断、尝试次数 |
| Risk Boundary | 不直接操作企业系统 | 禁止写操作 | 禁止执行动作 | 仅 LOW/MEDIUM 自动；HIGH/CRITICAL 人审 |
| Upstream | Human | Manager | Manager / Context | Manager / Diagnosis |
| Downstream | 三个 Worker / Human | Diagnosis | Manager | Manager |
| Failure Strategy | 一次有界重试后 fail closed | 缺证即停止 | 未知根因不猜测 | 工具成功也必须验证；验证失败上报 |

可执行身份定义位于 `app/agents/identities.py`，AgentTeams `soul` 位于 `agentteams/officeops-workers.yaml`。
