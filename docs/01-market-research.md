# 01 · Market Research（轻量市场调研）

## 核心判断

企业办公 IT 的工具体系高度分散：ITSM、IAM、设备管理、监控和自动化平台分别掌握流程、身份、资产、状态和动作能力。2026 年起，ServiceNow（Autonomous Service Operations）、Atomicwork（AI Coworker）、Atera（Autonomous IT）、Freshservice（Freddy AI Agent）已把“从回答问题转向完成任务”的 Agentic IT 带入市场，验证了方向的真实性；但它们的能力普遍围绕各自平台和商业生态构建。

OfficeOps 不再造 ITSM/CMDB，也不做万能 Agent，而是基于比赛指定的 AgentTeams 探索开放的多 Agent 协同基础设施：把 Agent Identity、Skill、Tool/MCP、Context、Evidence、Policy、Approval 与 Verification 定义为可替换协议，以最小权限、可审计的方式把既有企业系统组合进任务闭环，并用办公 IT 黄金案例完成工程验证。

## 六个问题

| 调研对象 | 结论 |
| :-- | :-- |
| 当前人工流程 | 员工在群聊/电话/OA 报障；服务台补问；运维跨后台查账号、设备、网络、日志和权限；依赖个人经验处理；手工回复与记录。 |
| 现有软件 | ITSM/OA 擅长流转，监控/CMDB 擅长数据，RPA/脚本擅长固定动作，各厂商控制台擅长本域管理，但上下文和完成标准分散。 |
| 单 Agent | 一个 Agent 若同时读取全域数据、制定方案、审批、持有写权限和验证，会形成过大攻击面，且难区分事实、建议和执行结果。 |
| Multi-Agent | 按职能隔离上下文和凭据；支持并行采集、专业判断、策略仲裁、受控执行、独立验证和分段审计。 |
| 类似方案 | Agentic IT 方向已被商业验证（Atomicwork/ServiceNow/Atera/Freshservice）；开源方法论同源（OpenSRE/HolmesGPT/Ongrid，域为基础设施而非办公 IT）。差异位：开放协议 + 办公 IT 域 + 验证纪律。 |
| 企业限制 | 厂商 API 可用性不同；数据敏感；资产关系不完整；写操作需审批、幂等和补偿；结果需用户/探针确认。 |

## 竞品分层（2026 Agentic IT 格局）

| 层次 | 代表 | 已验证能力 | 与 OfficeOps 的关系 |
| --- | --- | --- | --- |
| System of Record | ServiceNow ITSM、Jira SM、GLPI | 工单、资产、CMDB、知识 | 不重建，经 Adapter/MCP 接入 |
| Deterministic Automation | StackStorm、Rundeck、n8n | 工作流、动作、Runbook、审计 | 参照其“Agent 决策与确定执行分离” |
| AI Ops Agent（开源） | OpenSRE、HolmesGPT（CNCF Sandbox）、Ongrid、RunbookHermes | 证据采集、根因分析、受控修复、恢复验证 | 方法论同源；域不同（基础设施 vs 办公 IT） |
| Agentic IT Platform（商业） | Atomicwork、ServiceNow ASO、Atera Robin、Freshservice Freddy | 端到端员工 IT 解决、角色/技能/权限治理 | 方向验证；能力绑定自家平台——OfficeOps 的开放协议差异位 |

各层共同规律：任务定义锚定行业标准（ITIL 工单或告警），不自建任务本体；对象模型引用系统记录（CMDB/IAM/MDM），不自建对象库。差异化集中在完成标准——头部商业产品未把“执行后独立重观测验证”作为公开的一等公民机制，这是 OfficeOps 的差异位。

与 OfficeOps 设计最接近的商业产品是 Atomicwork（Agent 具备 Role、Skill、Access Control 并以“AI Coworker”方式协作治理），这验证了本方案的 Agent Identity 与最小权限方向。

## 为什么不是“万能 Agent”

打印机故障、VPN 开通和 Docs 账号锁定的专业逻辑不同，但共享同一生命周期：

```text
输入 → 规范化 → 上下文 → 判断/计划 → 风险 → 执行 → 验证 → 证据
```

OfficeOps 复用生命周期和基础设施，专业差异由场景包表达。这样既避免为每个系统重写平台，也避免一个 Agent 在没有专业边界的情况下“什么都做”。

## 场景价值矩阵

| 场景 | 频率/感知 | 多源上下文 | 写操作风险 | 验证可见性 | 当前策略 |
| --- | --- | --- | --- | --- | --- |
| Docs/SSO 访问失败 | 高频、员工感知强 | IAM、VPN、权限、健康、探针 | 低到中 | 高 | 首个可运行 Case |
| VPN 权限开通 | 高频、流程繁琐 | HR/OA、账号组、资源、端口 | 中到高 | 高 | 重要候选场景包 |
| 打印机离线 | 高频、直观 | 资产、队列、网络、耗材 | 低到中 | 高 | DeviceOps 候选 |
| 会议室无法投屏 | 高频、演示直观 | 设备、网络、预约、日志 | 低到中 | 高 | DeviceOps 候选 |
| 钉钉/OA 账号异常 | 高频、跨身份 | HR、SSO、应用、策略 | 中 | 高 | SaaSOps 候选 |
| 云/容器故障 | 价值高但范围大 | 监控、日志、拓扑、发布 | 高 | 中到高 | 仅作为办公服务依赖，不先扩展 |

## 行业复制性

### 可直接复用

- WorkItem、ManagedObject、Relationship、Observation、Evidence；
- AgentTeams 协作、状态和 Artifact 交接协议；
- Policy/Approval/Execution/Verification 生命周期；
- Skill/Tool Schema、幂等、审计和失败语义；
- Trace、评测、Fake Success 和场景包规范。

### 企业需替换

- 工单字段、组织和资产主数据；
- 钉钉/OA/ITSM、设备平台、VPN/SSO、云/K8s Adapter；
- 风险规则、审批链、SLA 和可自动动作；
- 资源命名、网络拓扑、数据脱敏和审计留存策略。

## 需要后续实证的数据

- 典型工单的人工处理步骤、耗时和补充信息次数；
- 高频场景及首次解决率；
- 自动动作占比、审批拒绝率和误操作率；
- “工具成功但用户未恢复”的比例；
- 不同场景复用核心 Skill/Tool 契约的比例；
- 同一故障不同表述的输入变体通过率（与无 LLM 规则基线对照）。

初赛只做定性论证；复赛通过 Golden Cases、人工基线和运行 Trace 给出量化结果。

## 主要风险

| 风险 | 应对 |
| --- | --- |
| 场景过多导致 Demo 松散 | 通用架构完整，工程只跑深一个 Case；第二场景先做只读或设计映射 |
| 架构过度抽象 | 所有核心概念必须能映射到当前 Docs Case 和至少两个候选场景 |
| 多 Agent 被认为强行拆分 | 用上下文隔离、工具权限和独立验证证明不可合并；每个 Worker 必须引入上游生成时不具备的新信息 |
| 与商业 Agentic IT 撞车 | 差异位是开放协议 + 办公 IT 域 + 验证纪律，不与商业产品拼接入数量 |
| 厂商 API 不可用 | 提供 MCP 等价契约、有状态 Sandbox 和迁移成本说明 |
| 推荐工具堆叠 | 只在解决明确问题时引入，不按数量宣称成熟度 |

## 相关文档

- 输入：[00 产品提案](00-product-proposal.md)
- 下游：[02 用户故事](02-user-stories.md) · [10 评估计划](10-evaluation-plan.md)
