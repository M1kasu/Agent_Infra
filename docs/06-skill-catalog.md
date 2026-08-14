# 06 · Skill Catalog（Skill 清单）

> Skill = 任务能力抽象层。推导顺序：Agent 职责 → 需要哪些能力 → 抽象成 Skill → Skill 需要哪些 Tool。初赛做到清单级即可（Gate 之后才细化）。
> 状态：⬜ 未开始 · 负责人：待认领 · [← 返回 README](../README.md)

## Skill 清单

| Skill | 所属 Agent | 做什么 | 依赖 Tool（→07） | 真实/Mock | 优先级 |
| :-- | :-- | :-- | :-- | :--: | :--: |
| | | | | | |

> 数量参考：全项目 5~8 个 Skill 为宜，宁少而通，不多而杂。

## 单个 Skill 定义模板

```text
Skill 名称：
触发条件：什么情况下被调用
输入：参数与类型
输出：产物与格式（含 Evidence）
前置条件：依赖的数据 / 权限
失败处理：重试策略 / 降级路径
```

## Skill 与比赛要求的对应

| Skill | 体现的比赛概念 | 说明 |
| :-- | :-- | :-- |
| | 例：RAG / MCP 调用 / 任务拆解 | 为什么这里需要它，而不是为了用而用 |

## 相关文档

- 上游：[04 Agent 身份](04-agent-identities.md) · [05 协作流程](05-agent-workflow.md)
- 下游：[07 Tool & MCP 契约](07-tool-mcp-contract.md)
