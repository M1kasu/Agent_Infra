# 08 · System Design（系统设计）

> 架构是 Manager–Worker 多 Agent 骨架（AgentTeams），不是"三个聊天机器人"。Gate 3：Manager/Worker 映射未明确，不进入正式开发。
> 状态：⬜ 未开始 · 负责人：待认领 · [← 返回 README](../README.md)

## 系统架构图（初赛必须出图）

```text
（待绘制。参考骨架：）

        用户 / 企业事件
              │
       Manager Agent（主控/协调）
       ┌──────┼──────┐
       ▼      ▼      ▼
    Worker  Worker  Worker
    (分析)  (诊断)  (执行)
       └──── Shared Context ────┘
              │
           Skills（能力层）
              │
         MCP / API / DB（连接层）
              │
          企业真实系统 / Mock
```

## 关键设计问题

| 问题 | 决策 | 记录为 |
| :-- | :-- | :-- |
| Manager/Worker 如何映射到 AgentTeams？ | | DECISION |
| 上下文存哪里、怎么传？ | | DECISION |
| 数据库选型？（PostgreSQL / PolarDB 路线） | | DECISION |
| RAG 方案？（pgvector / metadata filter 退路） | | DECISION |
| Trace 与日志怎么落、评委怎么看？ | | DECISION |

## 模块划分（复赛出代码时的目录映射）

```text
agents/    # Agent 定义
skills/    # Skill 实现
mcp/       # MCP 连接层
rag/       # 知识库
backend/   # API 与编排
tests/
examples/
```

## 技术栈清单（每项写"为什么"，不许只写名字）

| 组件 | 选型 | 为什么 | 挂在主线哪一环 |
| :-- | :-- | :-- | :-- |
| | | | |

## 相关文档

- 上游：[03 领域模型](03-domain-model.md) · [07 Tool 契约](07-tool-mcp-contract.md)
- 下游：[09 安全设计](09-security-design.md) · [10 评估计划](10-evaluation-plan.md)
