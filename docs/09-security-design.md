# 09 · Security Design（安全、审批与审计）

## 安全目标

1. 一个被恶意或错误输入影响的 Agent 不能越过自身角色和 Tool allowlist。
2. 任何写操作都能关联到原始 WorkItem、ActionPlan、策略/审批和执行者。
3. 高风险动作不能被 Manager、LLM 或 Tool Adapter 绕过审批。
4. Tool 回执、状态观测和用户体验相互矛盾时，系统 fail closed。
5. 敏感身份、拓扑、日志和凭据只在完成当前 Task 所需范围内流动。
6. 错误操作可补偿；不可补偿或状态未知时及时停止并人工介入。

## 风险等级

| 等级 | 定义 | 示例 | 默认处置 |
| :--: | --- | --- | --- |
| L0 | 只读、无副作用 | 查询账号/设备/服务健康、检索知识、功能探针 | 自动，留 Evidence |
| L1 | 低影响、范围明确、可逆或易恢复 | 普通账号解锁、生成报告、更新工单备注 | 策略自动或单人确认；执行后验证 |
| L2 | 影响共享服务、配置或访问范围 | VPN/应用权限开通、重启共享打印机、修改会议设备/网络配置 | 指定 Human Approval 后执行 |
| L3 | 高价值、广范围、管理权限或不可逆 | 管理员权限、通配网段/全端口、生产关键服务、批量离职操作 | 双人审批、变更窗口；MVP 默认禁止 |

风险由“动作 + 对象敏感度 + 影响范围 + 环境 + 时间 + 主体”共同决定，同一动作可因企业策略处于不同等级。

## 场景示例

| 场景动作 | 建议风险 | 额外条件 |
| --- | :--: | --- |
| 查询打印机队列/耗材 | L0 | 只读凭据 |
| 重启单用户打印队列 | L1 | 可逆、限定对象、验证测试页 |
| 重启共享会议室设备 | L2 | 会议影响、预约窗口、负责人审批 |
| 解锁已确认锁定的普通员工账号 | L1 | 人员 active、非管理员、`lock_reason=auto_lock`（admin/security 锁定转人工）、幂等、重新验证 |
| 新开 VPN/SSO 资源权限 | L2 | 主管/资源负责人/安全审批、有效期 |
| 管理员/通配资源权限 | L3 | 双人审批或禁止 |
| 重启支撑办公服务的生产容器 | L3 | 变更窗口、回滚、SRE 审批 |

## 职责分离

| 角色 | 允许 | 禁止 |
| --- | --- | --- |
| TeamLeader（编排） | 拆解、路由、状态和汇总 | 企业系统业务读写、代替 Worker 产出事实 |
| Context | 相关对象只读查询 | 任何写入、诊断后直接执行 |
| Diagnosis & Planning | 生成 Diagnosis/Plan | 审批和写工具 |
| Policy & Approval | 确定性策略、发起/读取 Human Decision | 代替人类批准、目标系统写入 |
| Execution | Approved Plan allowlist 内写入 | 修改计划、扩大目标、自我审批、自我验收 |
| Verification | 独立只读、探针、断言、报告 | 修复写入、通知渠道写、未经评审发布知识 |
| Close/Notify（确定性服务） | 更新工单、发送通知 | 越过验证结论改写结果 |

Human Approver 不能与申请人、Execution 身份冲突；场景策略可要求主管、资源负责人、安全人员的任意组合。

## 双层执行门禁

### 第一层：Policy & Approval

- ActionPlan Schema 和依赖有效；
- 每步风险已计算，前置事实已分类（如 `lock_reason`，仅 `auto_lock` 可走 L1 自动路径）；
- Policy Bundle 版本固定；
- 必需审批人角色明确；
- Human Decision 绑定 `plan_hash` 和有效期。

### 第二层：Tool Gateway

每次写调用再次校验：

```text
agent_role is allowed
AND tool/operation in agent allowlist
AND target/parameters exactly match ActionStep
AND plan_hash is current
AND policy decision permits action
AND required approvals are valid
AND approval not expired/revoked
AND idempotency key is present
AND evidence/trace service is writable
```

任一条件不满足，Gateway 返回标准 `POLICY_DENIED`，Adapter 不收到真实凭据。

## 审批设计

| 问题 | 设计 |
| --- | --- |
| 谁审批 | 按场景和风险：直属主管、资源负责人、系统负责人、信息安全、变更负责人 |
| 审批人看到什么 | 原始目的、Subject、对象/依赖、当前与目标差异、每步动作、风险规则、影响、有效期、验证和补偿 |
| 审批绑定什么 | `work_item_id + plan_id + plan_hash + policy_version + expires_at` |
| 审批超时 | 计划进入 EXPIRED，不允许执行；重新提交需新 Approval |
| 计划变化 | 旧 Approval 立即 SUPERSEDED；生成新哈希并重新审批 |
| 审批拒绝 | Run 进入 REJECTED；不产生企业写 ToolCall |
| 渠道不可用 | 进入待审批队列和通知重试；不得降级为自动批准 |
| Mock 是否审批 | 是。Sandbox 写操作遵守同一门禁，保证 Demo 与生产语义一致 |

审批记录包含真实身份、角色、渠道外部引用、决定、时间、评论、签名和 Evidence ID。LLM 只能生成审批摘要，不能生成批准签名。

## 输入、Prompt 与知识安全

用户消息、附件、日志、网页、知识文档和 Tool 响应均视为不可信数据：

- 与系统指令分区，禁止将内容中的“忽略规则/调用工具”当成命令；
- Normalize Skill 只提取 Schema 字段；
- RAG 片段必须带来源、版本和适用范围；
- 知识不能覆盖 Policy、Tool allowlist 或 Agent Identity；
- 对可疑 URL、脚本、命令和附件只做引用/分析，不自动执行；
- Tool 参数必须通过类型、枚举、长度、网段、路径和对象范围校验。

## 数据安全

| 数据类型 | 处理 |
| --- | --- |
| 普通工单字段 | 按任务和租户隔离 |
| 员工身份/组织 | 最小字段传递；报告脱敏 |
| IP、域名、拓扑、日志 | SENSITIVE；原文存受控 Artifact，消息传引用 |
| 审批与审计 | 限定审计/安全角色访问，按制度留存 |
| 密钥、token、cookie | SECRET；只在 Secret Manager/运行环境；永不进入 Prompt、Evidence、日志和截图 |
| 模型输入输出 | 记录脱敏摘要、版本、哈希和必要 Trace，不默认保存全部原文 |

租户、环境和场景凭据隔离；生产与 Sandbox 不共享 token；Context/Verifier 使用只读身份；Execution 的凭据按能力和对象范围限制。

## 幂等、失败与补偿

- 写幂等键：`run_id + plan_hash + step_id`；
- 执行前保存必要 Before Snapshot；
- Tool 超时/连接中断后先查询实际状态；
- 可补偿动作显式声明 Compensation Step，按已成功步骤逆序执行；
- 共享对象默认不删除，只撤销本 Run 创建且无外部依赖的对象；
- 无法确定状态、补偿失败或越权观测触发 `MANUAL_INTERVENTION`/安全事件；
- Verification 失败不得自动循环写入超过场景最大尝试次数。

## 验证安全

- Verifier 使用不同于 Executor 的只读身份和数据路径；
- 必须重新查询状态，而非复用执行前 Context；
- DesiredOutcome 包含正向和必要的负向断言；
- 用户确认是补充证据，不覆盖明确的安全失败；
- 探针不可用时返回 INCONCLUSIVE；
- Fake Success、部分生效、错对象、超范围权限均视为失败。

## 审计与防篡改

所有 ToolCall、状态迁移、审批、Artifact 和验证关联 `run_id/task_id/trace_id`。Evidence 记录内容哈希，可选 `previous_hash` 形成哈希链；生产演进可写入 WORM/不可变存储。审计报告必须能回答：

- 谁提交、谁受影响、谁批准；
- 哪个 Agent/Skill/Tool/Adapter/模型版本参与；
- 使用了哪些事实和知识；
- 实际对哪个对象执行了什么参数；
- 外部回执和执行前后状态是什么；
- 为什么完成、失败、补偿或升级。

## 密钥管理

- 仓库只提供 `.env.example`；真实密钥不得提交、写文档或进入截图。
- 本地 Demo 使用独立 Sandbox 凭据。
- 生产使用 Secret Manager/AgentTeams/Higress 可控凭据机制，短期 token 优先。
- Adapter 不向 Agent 暴露原始密钥；凭据轮换不改变 Tool Contract。
- 启动时扫描缺失/弱默认密钥；日志统一 Redaction Filter。

## 当前原型差距

| 能力 | 当前 | 复赛优先级 |
| --- | --- | :--: |
| Context/Remediation Tool 角色隔离 | 已有原型证据 | 保持 P0 |
| 中风险动作策略门禁 | 已有设计/代码 | P0 校验 |
| Human Approval 交互和签名 | 未完整实现 | P0 |
| 独立 Verification Worker | 当前与 Remediation 同 Worker | P0 |
| Tool Gateway 二次门禁 | 部分依赖角色 MCP | P0 |
| 通用补偿/回滚 | 未完整实现 | P1 |
| 不可变审计/脱敏 | 轻量 Trace | P1 |
| 真实企业 RBAC/Secret | Sandbox | P1/决赛 |

## 相关文档

- 上游：[05 协作流程](05-agent-workflow.md) · [07 Tool 契约](07-tool-mcp-contract.md)
- 下游：[10 评估计划](10-evaluation-plan.md) · [11 Demo 剧本](11-demo-script.md)
