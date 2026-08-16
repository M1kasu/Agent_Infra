# 07 · Tool & MCP Contract（工具接入契约）

## 接入原则

1. Agent 不直接调用厂商 SDK、数据库或页面；统一经过 Tool Adapter/Gateway。
2. Tool 暴露业务能力，不暴露任意 shell、任意 URL 或任意 SQL。
3. 读写能力分离；不同 Agent 使用不同身份和 allowlist。
4. 写操作必须携带 `task_id`、`plan_hash`、风险令牌、审批引用和幂等键。
5. Tool 回执只代表调用结果，业务完成由 Verification 决定。
6. 没有 MCP 时仍提供等价契约，未来迁移只替换协议适配。

## 能力域目录

| Tool Domain | 典型能力 | 主要调用 Agent | MVP 状态 |
| --- | --- | --- | --- |
| Channel / Workflow | 读工单、追问、发审批、通知、更新状态 | Context、Policy、Close | Mock/设计 |
| Directory / Identity | 查询人员、账号、组、锁定状态 | Context、Verifier | Sandbox 已有 |
| Asset / CMDB | 查询设备、位置、所有者、关系 | Context | Mock/设计 |
| Device | 打印机/会议室/终端状态和受控动作 | Context、Executor、Verifier | 后续 Adapter |
| SaaS / Application | 权限、健康、功能访问探测 | Context、Executor、Verifier | Docs Sandbox 已有 |
| VPN / SSO | 账号、认证、资源和权限 | Context、Executor、Verifier | 部分 Sandbox/候选 |
| Network | DNS、连通性、Wi-Fi/端口探针 | Context、Verifier | Mock/设计 |
| Monitoring / Infra | 服务、云实例、容器、工作负载状态与受控动作 | Context、Executor | 后续 Adapter |
| Knowledge / Evidence | 检索、Artifact、Trace、报告 | Diagnosis、Verification | 轻量本地设计 |

## 真实与 Mock 分界

| 类别 | 初赛/复赛策略 | 原因 |
| --- | --- | --- |
| AgentTeams 协作、Agent Identity、Skill、状态、Trace | 真实运行 | 比赛核心和可验证工程能力 |
| Docs/IAM/VPN/Application Tool | 有状态 Sandbox + MCP | 无企业凭据也能验证状态变化、权限隔离和 Fake Success |
| 钉钉/OA/ITSM | 本地 Channel/Approval Adapter；有授权再换真实接口 | 不让外部连接阻塞主闭环 |
| 打印机/会议室/云/K8s | 先定义契约和样例，不实现写入 | 防止场景扩张稀释 MVP |
| RAG/数据库/消息队列 | 有明确需求再实现 | 推荐组件不按数量得分 |

## 通用 ToolCall Envelope

```json
{
  "schema_version": "1.0",
  "tool_call_id": "tc-...",
  "run_id": "run-...",
  "task_id": "task-...",
  "trace_id": "trace-...",
  "agent_id": "execution-agent",
  "skill": "ExecuteControlledAction@1.0.0",
  "tool": "identity-access",
  "operation": "unlock_account",
  "target_ref": "account://alice",
  "parameters": {"reason_code": "account_locked"},
  "idempotency_key": "run:plan:step",
  "plan_hash": "sha256:...",
  "authorization": {
    "policy_decision_id": "pd-...",
    "approval_ids": []
  },
  "requested_at": "..."
}
```

响应：

```json
{
  "tool_call_id": "tc-...",
  "status": "SUCCEEDED|FAILED|UNKNOWN",
  "data": {},
  "external_receipt": "provider-ref",
  "observed_at": "...",
  "retryable": false,
  "retry_after_ms": null,
  "error": {"code": null, "message": null},
  "evidence_id": "ev-..."
}
```

`UNKNOWN` 表示请求是否生效无法确定，执行器必须先查询真实状态，不能直接重放。

回执 `status` 只描述调用层结果。完成判定使用三态独立语义：`tool_status`（本回执）≠ `execution_status`（步骤汇总）≠ `verification_status`（独立新鲜观测，见 03）；三者冲突时以最新鲜观测为准，任务不得 COMPLETED。

## Tool Capability 描述

每个操作必须定义：

```text
capability_id / operation / version
purpose
input_schema / output_schema
read_or_write
risk_level
required_agent_role / auth_scope
required_plan_fields / approval_policy
idempotency_behavior
preconditions / postconditions
error_codes / retry_advice
audit_fields / redaction
degradation / manual_fallback
```

## MVP Tool 契约

### T1 · Directory / IAM Read

| 操作 | 输入 | 输出 | 风险 | 角色 |
| --- | --- | --- | :--: | --- |
| `get_subject` | subject_id | active、employment、account refs | L0 | Context |
| `get_account_state` | provider、account_id | active、locked、lock_reason、groups、version | L0 | Context/Verifier |

- `lock_reason` 枚举：`auto_lock`（超时/策略自动）、`admin_lock`（管理员手动）、`security_lock`（安全策略）；Policy 据此分类，后两类不允许 L1 自动解锁路径。
- 鉴权：只读服务账号；按 subject scope。
- 失败：NOT_FOUND 为业务结果；TIMEOUT 可有界重试。
- Evidence：来源、观测时间、对象版本和脱敏响应哈希。

### T2 · Identity Controlled Write

| 操作 | 输入 | 输出 | 风险 | 角色 |
| --- | --- | --- | :--: | --- |
| `unlock_account` | account_ref、idempotency_key、reason | accepted、receipt | L1（可配置） | Execution |
| `grant_permission` | account/resource/action/window | accepted、receipt | L2/L3 | Execution + Approval |

- `unlock_account` 只允许 Diagnosis=`account_locked`、账号 active、普通用户、`lock_reason=auto_lock`（管理员/安全锁定必须转人工）且策略允许。
- `grant_permission` 必须有匹配 plan_hash 的人审；MVP 不实现自动授权。
- Fake Success 模式允许 Tool 返回 accepted 但不改变状态，用于验证闭环。

### T3 · Application / Service Read & Probe

| 操作 | 输入 | 输出 | 风险 | 角色 |
| --- | --- | --- | :--: | --- |
| `get_service_health` | application_ref | status、version、components | L0 | Context |
| `get_effective_permissions` | subject、application | permissions、version | L0 | Context/Verifier |
| `probe_access` | subject、application | accessible、reason category、probe_id | L0 | Context/Verifier |

Probe 只返回可观测状态与粗粒度原因类（如 `auth_failure`、`network_unreachable`），不得返回最终根因或建议动作——`account_locked` 必须由 Diagnosis 基于多源证据推导，而不是探针直接吐出。

### T4 · Channel / Approval

| 操作 | 输入 | 输出 | 风险 | 角色 |
| --- | --- | --- | :--: | --- |
| `read_work_item` | external_ref | raw input、requester | L0 | Context |
| `request_approval` | plan summary、hash、approver roles | approval_ref | L1 | Policy |
| `get_approval` | approval_ref | signed decision、identity、time | L0 | Policy |
| `notify_result` | recipient、template、report_ref | message_ref | L1 | Close |

审批 Tool 不能提供 `approve_as_user` 能力；Human 必须在真实界面/身份下作出决定。

### T5 · Evidence / Trace

| 操作 | 输入 | 输出 | 风险 |
| --- | --- | --- | :--: |
| `append_evidence` | immutable metadata + content ref/hash | evidence_id | L1 |
| `append_trace_event` | trace event | event_id | L1 |
| `read_artifact` | artifact_ref + allowed purpose | content/version | L0 |

Evidence/Trace 写失败时，后续企业写操作 fail closed。

## Adapter 约定

```text
Stable Tool Contract
        ↓
Adapter
├── provider field mapping
├── auth/session handling
├── API/CLI/RPA invocation
├── provider error normalization
├── provider idempotency/read-after-write
├── redaction and evidence
└── capability discovery
```

Adapter 通过 Contract Test：同一输入语义、标准错误、权限拒绝、幂等、超时状态未知、Fake Success 和脱敏。更换深信服 VPN、其他 VPN、打印机厂商或钉钉接口时不重写上层 Skill。

## 权限分离

| 身份 | 允许 | 禁止 |
| --- | --- | --- |
| context-readonly | 相关对象的查询 | 任何写操作 |
| policy-approval | 发起/读取审批 | 目标系统写操作、代替用户审批 |
| execution-scenario | ActionPlan allowlist 内的写操作 | 任意目标、任意参数、跨场景能力 |
| verification-readonly | 执行后状态和功能探针 | 修复、删除、授权 |
| audit-readonly | 脱敏 Evidence/Trace | 原始密钥和超范围个人数据 |

## 重试、幂等和补偿

- L0 读：只对超时/限流使用指数退避和总时限。
- 写操作：幂等键为 `run_id + plan_hash + step_id`；重复请求返回原回执。
- Tool 超时：先调用只读状态查询；无法确认则 `UNKNOWN` 并人工介入。
- 业务校验失败不重试；修改计划必须创建新 plan_hash。
- 补偿是显式 ActionStep，不以“反向调用同名 API”猜测。

## 为什么推荐 MCP

MCP 适合把能力发现、Schema、角色隔离和跨 Agent 复用统一起来。若厂商只能提供 HTTP、CLI 或 RPA，Adapter 仍以相同 Tool Contract 暴露；未来迁移到 MCP 只替换传输与注册，不重写 Skill 或 Workflow。

## 审计字段

每次 ToolCall 至少记录：Agent/Skill 版本、Tool/Adapter 版本、目标引用、脱敏输入、输入哈希、plan_hash、approval_id、幂等键、开始/结束时间、状态、标准错误、外部回执、Evidence ID。密钥、token 和敏感原文禁止进入 Trace。

## 相关文档

- 上游：[06 Skill 清单](06-skill-catalog.md)
- 下游：[08 系统设计](08-system-design.md) · [09 安全设计](09-security-design.md) · [10 评估计划](10-evaluation-plan.md)
