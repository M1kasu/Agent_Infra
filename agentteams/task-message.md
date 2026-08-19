# AgentTeams Demo Task Messages

先启动本地 Mock Tool Gateway，再通过 AgentTeams Manager 将任务委派给 `officeops-demo` Team；也可以在 Team Room 中直接 `@officeops-lead`。

输入故意不包含 `scenario_id`、`account_locked` 或推荐动作。

## G01：正常恢复

```text
@officeops-lead

请处理一条新的员工办公 IT 报障。

run_id: at-g01
demo_mode: normal
员工：Alice
应用：Docs
报障原文：我的这个文档显示没有权限访问，无法打开。

请按 OfficeOps 协议完成多源取证、诊断、受控处置和独立验证。不要把工具回执直接当成完成。
```

## G07：Fake Success

```text
@officeops-lead

请处理一条新的员工办公 IT 报障。

run_id: at-g07
demo_mode: fake_success
员工：Alice
应用：Docs
报障原文：这个在线文档突然打不开，页面一直说我没有权限。

这是一次故障注入评测。即使写工具返回成功，也必须通过新的 IAM 查询和 Docs 功能探针决定是否完成。
```

