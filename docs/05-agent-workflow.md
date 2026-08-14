# 05 · Agent Workflow（Agent 协作流程）

> 画出唯一主流程（Golden Path）。Gate 1：没有这张图，不允许开始写 Agent 代码。
> 状态：⬜ 未开始 · 负责人：待认领 · [← 返回 README](../README.md)

## 主流程（Golden Path，必须定稿）

```text
（待定义。参考骨架：）

输入
 ↓
Coordinator Agent（任务拆解）
 ├── 分析类 Agent ── Skill ── Tool/MCP
 ├── 诊断类 Agent ── Skill ── RAG / 历史库
 └── ...
 ↓
综合判断（附 Evidence）
 ↓
人工审批（L2 危险操作，→09）
 ↓
执行 Agent
 ↓
结果验证
 ↓
复盘沉淀（报告 + Trace 归档）
```

## 关键设计问题

| 问题 | 答案 |
| :-- | :-- |
| 任务如何拆解与分发？（粒度、依据） | |
| 上下文（Context）如何在 Agent 间传递？传什么、不传什么？ | |
| Agent 间结论冲突怎么处理？ | |
| 哪一步必须人工审批？ | |
| 某环节失败怎么办？（重试 / 上报 / 回滚） | |
| 一次完整 Run 产生哪些 Evidence？ | |

## 异常分支（初赛至少列出，复赛实现）

- [ ] 工具调用失败 / 超时
- [ ] Agent 结论相互矛盾
- [ ] 审批被拒绝后的流程
- [ ] 输入数据缺失或不可信

## As-Is / To-Be 对照

| 步骤 | 现状（人工） | 有系统后 |
| :-- | :-- | :-- |
| | | |

## 相关文档

- 上游：[04 Agent 身份](04-agent-identities.md)
- 下游：[06 Skill 清单](06-skill-catalog.md) · [09 安全设计](09-security-design.md) · [11 Demo 剧本](11-demo-script.md)
