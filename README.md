# OfficeOps Agent

> **初赛方案基线 v0.2 · 2026-08-16**
> 面向企业数字办公环境的多 Agent IT 运维协同基础设施。

OfficeOps Agent 把分散在钉钉/OA/ITSM、终端设备、打印机、会议室、网络、VPN、SSO、企业 SaaS、云和容器平台中的办公 IT 任务，统一成一条可拆解、可执行、可验证、可审计的协同闭环。

项目不追求“一次接入所有系统”。通用性来自稳定的领域概念、Agent 职责、Skill 和 Tool 契约；初赛以队友已经跑通的“员工报障提示没有权限、多源证据定位为账号锁定”的 Docs 访问案例作为首个可运行验证案例。

## 一句话定位

> 让企业办公 IT 任务从跨系统人工接力，升级为有证据、有权限边界、有结果验证的多 Agent 自主闭环——以开放可复用的协议栈（Agent Identity / Skill / Tool-MCP / 场景包）实现，而非绑定单一平台的封闭产品。

## OfficeOps 包含什么

OfficeOps 的边界不是“办公室里的硬件”，而是支撑员工数字化工作的 IT 服务与运维流程。

| 场景域 | 代表系统/对象 | 在 OfficeOps 中的角色 |
| --- | --- | --- |
| 交互与流程 | 钉钉、用友 OA、泛微 OA、ITSM | 报障、申请、审批、通知和客户确认渠道 |
| 设备与空间 | 打印机、会议室投屏、终端、门禁 | 被观测和处置的办公资产 |
| 身份与访问 | SSO、IAM、VPN、账号组、权限 | 身份事实、访问控制和服务请求控制面 |
| 企业 SaaS | 钉钉、邮箱、Docs、OA 应用 | 员工使用的数字办公服务 |
| 网络与基础设施 | Wi-Fi、DNS、云服务器、容器、Kubernetes | 办公服务的依赖和处置目标；不扩展成泛云运维平台 |
| 治理与知识 | CMDB、知识库、审计、监控 | 拓扑、规则、Runbook、Evidence 和持续优化来源 |

因此，VPN 开通、SSO 认证、OA 账号、云服务器和容器都可以作为 OfficeOps 的场景或依赖；它们不是项目唯一主线。打印机到钉钉的“贯通”体现为同一套 WorkItem、Agent、Skill、Tool、Evidence 和治理机制，而不是一个巨型 Agent 持有所有权限。

## 通用任务闭环

```text
事件 / 工单 / 申请
  → 规范化与分类
  → 多源上下文与依赖采集
  → 诊断 / 处置计划
  → 风险策略与按需审批
  → 受控执行
  → 独立结果验证
  → 用户确认、证据归档与经验沉淀
```

所有技术选择必须挂到以下链路：

```text
用户问题 → 业务流程 → Agent 分工 → Skill → MCP/Tool → Execution → Evidence → Validation
```

## 稳定核心与可插拔场景

### 稳定核心

- `WorkItem`：Incident、ServiceRequest、Change、LifecycleEvent；
- `ManagedObject`：Person、Account、Device、Application、Service、Resource；
- `Relationship`：依赖、归属、连接、成员、授权；
- `Observation / Evidence`：来自企业系统的新鲜事实；
- `Diagnosis / ActionPlan`：根因、目标状态、步骤、风险和补偿；
- `PolicyDecision / Approval`：自动化边界和人类决策；
- `Execution / Verification`：真实动作与独立验证；
- `WorkflowRun / Trace`：状态、上下文、证据和审计。

### 场景包

- **AccessOps Pack**：VPN、SSO、账号、组和权限；
- **DeviceOps Pack**：打印机、会议室、终端和外设；
- **SaaSOps Pack**：钉钉、OA、邮箱、Docs 等企业应用；
- **NetworkOps Pack**：Wi-Fi、DNS、办公网和远程接入；
- **InfraOps Adapter**：支撑办公服务的云服务器、容器和 Kubernetes。

新增功能优先增加场景 Skill、Policy 和 Tool Adapter，不修改核心生命周期。

## 当前可运行验证案例

员工 Alice 报障“我的这个文档显示没有权限访问，无法打开”——提示指向权限，证据指向锁定：

```text
Manager
  → Context Worker：查询 IAM、VPN、权限、服务健康和功能访问
  → Diagnosis Worker：排除权限/网络/服务，判断 account_locked
  → Remediation & Verification Worker：受限解锁并重新读取状态、探测访问
  → Manager：仅在 locked=false 且 accessible=true 后完成
```

已有队友分支包含 AgentTeams、Matrix、角色隔离 MCP、4 个 Skill、Sandbox、Trace、Fake Success 和自动测试。它是通用架构的第一个验证切片，不代表 OfficeOps 只处理账号问题。验收不以单次脚本化运行为准：同一故障的输入变体集与同症异因 Case 纳入评测（见 10）。

## 可执行初赛 Demo

仓库现提供一份零第三方依赖的可执行 Demo，包含有状态 Mock Tool Gateway、正常恢复、Fake Success、完整运行证据、Web 演示页和 AgentTeams `Worker + TeamLeader + Team` 声明文件。

```bash
node demo/cli.mjs --mode normal
node demo/cli.mjs --mode fake_success
node demo/server.mjs
node --test demo/tests/*.test.mjs
```

浏览器演示地址为 `http://localhost:18110`。详细运行、AgentTeams 接入和 Vercel 语义见 [demo/README.md](demo/README.md)。

## 核心设计原则

1. **先统一概念，再接厂商系统**：厂商字段留在 Adapter，核心模型保持稳定。
2. **职责和凭据隔离**：采集、诊断、策略、执行、验证由不同身份承担。
3. **按风险自治**：低风险可自动，高风险必须审批，禁止追求“零人工”口号。
4. **Tool Success ≠ Execution Success ≠ Task Success**：三态独立判定，完成只由执行后的新鲜观测和业务探测决定，执行者不能自证成功。
5. **证据优先**：每个事实、决策、动作和结论均可追溯。
6. **先做深一个闭环，再横向扩场景**：架构支持乘法，交付仍遵守 MVP Gate。
7. **混合编排**：认知环节（规范化、采集、诊断、路由）交给模型，安全链路（策略、审批、门禁、验证断言）交给代码。

## 文档导航

`✅ v0.2` 表示初赛修订基线完成（吸收竞品调研与混合编排定位），不表示对应代码已全部实现。

| 编号 | 文档 | 核心内容 | 状态 |
| :-- | :-- | :-- | :--: |
| 00 | [Product Proposal](docs/00-product-proposal.md) | 产品定位、边界、验证案例和决策 | ✅ v0.2 |
| 01 | [Market Research](docs/01-market-research.md) | 人工现状、方案对比与复制性 | ✅ v0.2 |
| 02 | [User Stories](docs/02-user-stories.md) | 8 条通用用户故事 | ✅ v0.2 |
| 03 | [Domain Model](docs/03-domain-model.md) | 通用领域对象、关系和状态机 | ✅ v0.2 |
| 04 | [Agent Identities](docs/04-agent-identities.md) | Manager 与职责 Worker | ✅ v0.2 |
| 05 | [Agent Workflow](docs/05-agent-workflow.md) | 通用闭环与首个 Golden Path | ✅ v0.2 |
| 06 | [Skill Catalog](docs/06-skill-catalog.md) | 可跨场景复用的核心 Skill | ✅ v0.2 |
| 07 | [Tool & MCP Contract](docs/07-tool-mcp-contract.md) | 工具能力、鉴权、幂等和审计 | ✅ v0.2 |
| 08 | [System Design](docs/08-system-design.md) | AgentTeams、共享状态和 Adapter 架构 | ✅ v0.2 |
| 09 | [Security Design](docs/09-security-design.md) | 最小权限、审批、补偿与审计 | ✅ v0.2 |
| 10 | [Evaluation Plan](docs/10-evaluation-plan.md) | 指标、Golden Cases 和验收 Gate | ✅ v0.2 |
| 11 | [Demo Script](docs/11-demo-script.md) | Docs 账号锁定 Demo 分镜 | ✅ v0.2 |
| 12 | [Executable Demo & Vercel](docs/12-executable-demo-and-vercel.md) | 代码包、本地验收与在线部署 | ✅ demo 0.1 |

## 阶段 Gate

| 阶段 | Gate |
| --- | --- |
| 产品定义 | 能解释用户、场景域、首个验证案例和为什么 Multi-Agent |
| 领域建模 | 打印机、账号和 SaaS 故障能映射到共同核心，厂商字段不污染核心 |
| Agent 设计 | 采集、诊断、执行、验证有真实职责/权限差异 |
| Skill/Tool | 每项能力有 Schema、失败、安全和复用说明 |
| MVP | 首个 Golden Path 未跑通，不增加第二个写入系统 |
| 验证 | Fake Success、未知根因和高风险审批边界可复现 |
| 参赛包装 | 每个评分点都有运行或设计证据 |

## 仓库与里程碑

- `main` 保存统一产品和技术基线；功能分支通过 PR 合入。
- 提交遵循 Conventional Commits；密钥不进入仓库。
- 2026-08-16：初赛提交作品简介和方案 PPT。
- 若入围复赛：以现有账号访问案例为工程起点，补齐审批、独立验证、观测评测与一个跨渠道入口；完成前不同时开发打印机、VPN、云和容器写入。
