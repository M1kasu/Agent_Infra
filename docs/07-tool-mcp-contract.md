# 07 · Tool & MCP Contract（工具接入契约）

> MCP 是工具连接层。每个工具先写契约再接入：输入、输出、鉴权、危险等级、真实还是 Mock。
> 状态：⬜ 未开始 · 负责人：待认领 · [← 返回 README](../README.md)

## 真实 vs Mock 分界（初赛定稿，控制工作量）

| 类别 | 组件 | 理由 |
| :-- | :-- | :-- |
| 真实 | LLM、AgentTeams、PostgreSQL、RAG、Agent 通信 | 核心学习与评分点 |
| Mock | Monitoring API、Ticket API、CMDB API、Cloud API | 企业系统拿不到，Mock 不影响闭环验证 |

## 工具清单

| Tool | 协议（MCP/API） | 提供方 | 输入 | 输出 | 鉴权 | 危险等级（→09） | 真实/Mock | 状态 |
| :-- | :-- | :-- | :-- | :-- | :-- | :--: | :--: | :--: |
| | | | | | | | | |

> 数量参考：2~3 个外部工具即可讲清楚 MCP 价值。

## 单个工具契约模板

```text
Tool 名称：
用途：被哪个 Skill 调用（→06）
接口：方法 / 路径 / 参数 / 返回结构
鉴权方式：
错误码与重试建议：
调用留痕：产生什么 Evidence（→03）
```

## 为什么用 MCP（而不是直接调 API）

（回答：统一治理、跨 Agent 复用、可被 Agent 动态发现中的哪几条对我们成立）

## 相关文档

- 上游：[06 Skill 清单](06-skill-catalog.md)
- 下游：[08 系统设计](08-system-design.md) · [09 安全设计](09-security-design.md)
