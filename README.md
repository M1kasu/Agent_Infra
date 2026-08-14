# Agent_Infra

> **🚧 初赛阶段 · P0 项目定义 · 截止 2026-08-16**
> 当前仓库以方案文档为主，代码目录（agents/ skills/ 等）复赛再建。

**一句话定位**（占位，P0 定稿后更新）：
选定一个具体企业任务，用 3~4 个协作 Agent 跑通一条原本依赖人工协作的完整流程，并留下全过程证据。

---

## 设计主线

所有讨论先判断挂在主线的哪一环，顺序不可颠倒；挂不上的技术，先不做：

```text
用户问题 → 业务流程 → Agent 分工 → Skill 能力 → MCP/Tool → 真实执行 → Evidence → Validation
```

| 层级 | 核心问题 | 对应文档 |
| --- | --- | --- |
| 产品层 | 为什么做 | 00 · 01 · 02 |
| Agent 层 | AI 怎么完成 | 04 · 05 · 11 |
| 工程层 | 系统怎么实现 | 03 · 06 · 07 · 08 · 09 · 10 |

## 文档导航

> 初赛要求：每份至少完成 v0.1（一页即可，不求全）。
> 状态：⬜ 未开始 / 🚧 进行中 / ✅ 定稿

| 编号 | 文档 | 回答什么 | 完善时点 | 状态 | 负责人 |
| :-- | :-- | :-- | :--: | :--: | :-- |
| 00 | [Product Proposal](docs/00-product-proposal.md) | 做什么、给谁、为什么、MVP 边界 | P0 | ⬜ | 待认领 |
| 01 | [Market Research](docs/01-market-research.md) | 现状与同类方案、为何 Multi-Agent | P0 | ⬜ | 待认领 |
| 02 | [User Stories](docs/02-user-stories.md) | 5~8 条核心用户故事 | P0 | ⬜ | 待认领 |
| 03 | [Domain Model](docs/03-domain-model.md) | 核心实体与字段、状态机 | P1 | ⬜ | 待认领 |
| 04 | [Agent Identities](docs/04-agent-identities.md) | 3~4 个 Agent 的身份与不可合并理由 | P2 | ⬜ | 待认领 |
| 05 | [Agent Workflow](docs/05-agent-workflow.md) | 唯一主流程与任务流转 | P2 | ⬜ | 待认领 |
| 06 | [Skill Catalog](docs/06-skill-catalog.md) | Skill 清单与能力边界 | P3 | ⬜ | 待认领 |
| 07 | [Tool & MCP Contract](docs/07-tool-mcp-contract.md) | 工具契约：真实 / Mock 分界 | P3 | ⬜ | 待认领 |
| 08 | [System Design](docs/08-system-design.md) | AgentTeams 映射、DB、RAG、Trace | P4 | ⬜ | 待认领 |
| 09 | [Security Design](docs/09-security-design.md) | 危险操作分级、人工审批、审计 | P4 | ⬜ | 待认领 |
| 10 | [Evaluation Plan](docs/10-evaluation-plan.md) | 验收标准、验证方式、失败退路 | P6 | ⬜ | 待认领 |
| 11 | [Demo Script](docs/11-demo-script.md) | 唯一 Demo Case 的分镜剧本 | P0 | ⬜ | 待认领 |

⚠️ "完善时点"指该文档打磨到位的阶段；但 **00–11 全部需在初赛前给出 v0.1**。

## 阶段与 Gate

| 阶段 | 核心工作 | 对应文档 | Gate（不过不放行） |
| --- | --- | --- | --- |
| P0 项目定义 | 场景、用户、问题、价值、边界 | 00 01 02 11 | Gate 0：答不出"用户是谁、为什么 Multi-Agent"，不讨论技术选型 |
| P1 领域建模 | 实体、状态、关系 | 03 | Gate 2：核心对象未定义，不建表 |
| P2 Agent 设计 | Agent 身份、任务拆解、上下文 | 04 05 | Gate 1：画不出主流程图，不写 Agent 代码 |
| P3 Skill/Tool 设计 | Skill、MCP、API、权限 | 06 07 | — |
| P4 系统设计 | AgentTeams、DB、RAG、Trace | 08 09 | Gate 3：Manager/Worker 映射未明确，不进入正式开发 |
| P5 MVP 开发 | 跑通唯一主场景 | 代码（复赛） | — |
| P6 验证优化 | 异常、审批、回滚、评估 | 10 | Gate 4：Golden Path 未跑通，不开第二场景 |
| P7 参赛包装 | PPT、视频、README、证据 | Releases | — |

## 仓库约定

- **分支**：main 常驻所有内容；写某份文档时开临时分支 `docs/<编号>-<名称>`（如 `docs/00-product-proposal`），PR 合入后删除。分支是工作方式，不是存放位置。
- **提交信息**：Conventional Commits —— `docs:` 文档、`feat:` 功能、`fix:` 修复、`chore:` 杂务。
- **Issue 驱动**：每份文档一个 Issue，PR 描述写 `Closes #N` 自动关联关闭。
- **版本冻结**：初赛定稿打 tag（`preliminary-v1`）并发布 GitHub Release，此后仓库继续演进，提交版本永远可回溯。

## 里程碑

| 日期 | 事件 |
| --- | --- |
| 2026-08-16 | 初赛提交（00–11 文档 v0.1 全集 + 方案 PPT） |
| 待定 | 复赛：按 P3–P6 推进 MVP 开发 |
