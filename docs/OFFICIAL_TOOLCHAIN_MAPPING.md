# GOAI 官方工具链选型与真实状态

核对日期：2026-08-15。原则：AgentTeams 是必须的协同设计基点；其余项目是推荐选项，只在能增强核心闭环且有实际证据时接入，不按数量堆栈。

| 技术方向 | 官方项目 / 要求 | 初赛选型 | 当前状态 | 说明与替换边界 |
|---|---|---|---|---|
| 多 Agent 协同 | [AgentTeams / HiClaw](https://hiclaw.io/)；必须 | 必选；Manager + 3 standalone Worker | DONE | 官方 v1.2.2 Controller、Manager、Worker、Matrix、MinIO 与 Higress 已运行；真实 Matrix 工单完成三阶段委派，Skill/MCP 权限隔离和协议顺序均有 transcript 与状态证据。 |
| 云 Skills | [阿里云 Agent Skills 门户](https://skills.aliyun.com/)；推荐 | 初赛使用 4 个自研 OfficeOps Skill | NOT IMPLEMENTED | 自研 Skill 满足业务能力抽象，但不能宣称接入云 Skills 门户。复赛评估发布、鉴权和版本管理。 |
| AI 管理中心 | [Nacos](https://nacos.io/)；推荐 | 初赛不引入 | NOT IMPLEMENTED | 当前只有 4 个静态 Skill 和单机配置，引入注册中心收益有限；复赛多团队/多版本时用于 Skill、MCP、Prompt 和配置治理。 |
| AI 网关 | [Higress](https://higress.io/)；推荐 | 复用 AgentTeams 内置 Higress | PARTIAL | Higress 已随官方栈运行并承载框架基础网关能力；当前 OfficeOps MCP 仍按 Worker 直连两个角色隔离 SSE 端点，尚未迁入 Consumer 鉴权、限流与统一审计。 |
| Agent 数据层 | [PolarDB for PostgreSQL](https://openpolardb.com/home)；推荐 | 初赛使用本地 JSON/JSONL artifacts | NOT IMPLEMENTED | 当前无向量检索和高并发持久化需求；`TaskState`/Trace Schema 与存储实现解耦，可迁移 PostgreSQL。 |
| 数据统一建模 | [UnifiedModel](https://alibaba.github.io/UnifiedModel/)；推荐 | 初赛使用 Pydantic 领域 Schema | NOT IMPLEMENTED | 当前只覆盖 Employee/Identity/VPN/Application；复赛连接多个真实企业系统后再评估统一实体和关系查询。 |
| 消息队列 | [RocketMQ](https://rocketmq.apache.ac.cn/)；推荐 | 初赛使用同步状态机 | NOT IMPLEMENTED | 当前单场景链路是短串行任务，无需消息中间件；复赛长任务、批量事件、可靠通知再引入事件模型与幂等消费。 |
| 可观测 | [LoongSuite](https://alibaba.github.io/loongsuite-go/)、[AgentScope Studio](https://github.com/agentscope-ai/agentscope-studio) 或 [AgentLoop](https://help.aliyun.com/zh/cms/cloudmonitor-2-0/agentloop-overview)；推荐 | 自研轻量 Trace + artifacts | PARTIAL | task/trace/Agent/Skill/Tool/状态/验证已可观测；尚未对接任何官方观测后端，不能宣称使用上述产品。 |

## 为什么初赛不堆叠推荐组件

初赛只有一个 `account_lock` 场景，核心证据是：AgentTeams 真实消息协作、按角色隔离 MCP、上下文驱动诊断、Sandbox 真实状态变化、执行后验证、Fake Success 失败分支和完整 Trace。此时加入 Nacos、PolarDB、RocketMQ 或复杂观测后端会增加部署面，却不提升根因与验证可信度。

## 复赛接入顺序

1. 将已运行的角色隔离 MCP 迁入 AgentTeams 自带 Higress，增加 Consumer 鉴权、路由、限流和审计。
2. 接入 AgentLoop 或 AgentScope Studio，复用现有 `task_id`/`trace_id` 语义。
3. 当 Skill 数量和版本增长后接入 Nacos Registry。
4. 只有出现长任务异步化和跨系统实体查询需求时，再分别评估 RocketMQ、PolarDB 和 UnifiedModel。
