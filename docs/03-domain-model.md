# 03 · Domain Model（领域建模）

> 先定义"东西是什么"，再开始写代码。核心对象没定义清楚前，不建数据库表（Gate 2）。
> 状态：⬜ 未开始 · 负责人：待认领 · [← 返回 README](../README.md)

## 核心实体清单

初赛至少为带 ✅ 的实体给出字段级定义：

- [ ] Task ✅
- [ ] Agent / AgentIdentity ✅
- [ ] Skill ✅
- [ ] Tool / ToolCall ✅
- [ ] Context ✅
- [ ] Evidence ✅
- [ ] Approval ✅
- [ ] Execution
- [ ] Workflow / WorkflowRun ✅
- [ ] Trace
- [ ] Memory
- [ ] KnowledgeDocument

## Task（示例骨架）

```text
Task
├── task_id
├── task_type
├── requester
├── input
├── status
├── assigned_agent
├── context
├── parent_task_id
├── result
├── evidence_ids
└── created_at
```

## Evidence（示例骨架）

```text
Evidence
├── evidence_id
├── task_id
├── type          # log / metric / screenshot / tool_result / report
├── source
├── content
├── timestamp
└── hash
```

## 其余实体（按同样格式补齐）

### Agent / AgentIdentity

（待填）

### Skill / Tool / ToolCall

（待填）

### Context

（待填）

### Approval

（待填）

### Workflow / WorkflowRun

（待填）

## 状态机

Task 与 WorkflowRun 的状态流转（初赛必须画出主链路）：

```text
（待定义，例如 WorkflowRun: CREATED → RUNNING → WAITING_APPROVAL → EXECUTING → VERIFYING → DONE / FAILED / REJECTED）
```

## 相关文档

- 上游：[00 产品提案](00-product-proposal.md)
- 下游：[08 系统设计](08-system-design.md)（数据库设计由此派生）
