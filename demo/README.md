# OfficeOps Executable Demo

这是一份面向初赛提交的最小可执行代码包。它实现一个 Docs 访问故障案例，并提供正常恢复与 Fake Success 两条可重复路径。

## 它证明什么

1. 输入只有员工症状，不携带 `scenario_id` 或根因标签；
2. TeamLeader、Context、Diagnosis、Execution、Verification 职责分离；
3. Context 使用只读 Tool 身份，Execution 使用受限写身份；
4. PolicyDecision 由确定性规则产生；
5. 写调用需要计划哈希、策略决定和幂等键；
6. Tool `SUCCEEDED` 与 Task `COMPLETED` 分开；
7. Verification 使用执行后的新鲜 IAM 状态和功能探针；
8. 每次本地运行生成完整 Artifact、Evidence、ToolCall 和 Trace。

## 零依赖运行

要求 Node.js 20 或更高版本；不需要 `npm install`。

```bash
node demo/cli.mjs --mode normal
node demo/cli.mjs --mode fake_success
node --test demo/tests/*.test.mjs
node demo/scripts/check-config.mjs
```

Windows PowerShell 也可以直接执行上述 `node` 命令。若系统禁止执行 `npm.ps1`，无需调整执行策略；本 Demo 不依赖 npm 安装。

CLI 会把运行证据写入：

```text
artifacts/runs/<run_id>/
├── input.json
├── normalized_work_item.json
├── context.json
├── diagnosis.json
├── action_plan.json
├── policy_decision.json
├── execution.json
├── verification.json
├── tool_calls.json
├── evidence.json
├── trace.json
└── result.json
```

仓库同时保留两份脱敏后的已录制运行摘要，便于 GitHub/压缩包评审直接查看：

- `examples/evidence/g01-run-report.json`
- `examples/evidence/g07-fake-success-run-report.json`

## Web 演示

```bash
node demo/server.mjs
```

打开 <http://localhost:18110>。页面可以切换：

- `normal`：Tool 成功，状态改变，新鲜复验 PASS，任务 COMPLETED；
- `fake_success`：Tool 仍返回 SUCCEEDED，但状态未改变，复验 FAIL，任务 FAILED。

## HTTP API

完整运行：

```bash
curl -X POST http://localhost:18110/api/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"normal","message":"我的这个文档显示没有权限访问，无法打开。"}'
```

AgentTeams Worker Tool Gateway：

```text
POST /tools/{run_id}/sandbox.reset
POST /tools/{run_id}/iam.get_subject
POST /tools/{run_id}/iam.get_account_state
POST /tools/{run_id}/vpn.get_state
POST /tools/{run_id}/docs.get_effective_permissions
POST /tools/{run_id}/docs.get_service_health
POST /tools/{run_id}/docs.probe_access
POST /tools/{run_id}/iam.unlock_account
```

除 `sandbox.reset` 外，请求必须携带 `X-Agent-Role`。Gateway 会执行角色 allowlist 和写操作授权校验。

## AgentTeams 路径

1. 安装并启动官方 AgentTeams；
2. 在宿主机运行 `node demo/server.mjs`；
3. 从 AgentTeams 容器确认 `http://host.docker.internal:18110/api/health` 可访问；
4. 使用官方 `agentteams-apply.sh -f agentteams/officeops-demo.yaml`，或把 YAML 复制到 Manager/Controller 后执行 `agt apply -f`；
5. 在 Manager 房间要求把任务委派给 `officeops-demo`，或在 Team Room 中 `@officeops-lead`；
6. 使用 [task-message.md](../agentteams/task-message.md) 中的 G01/G07 消息。

YAML 使用官方当前的 `agentteams.io/v1beta1` Worker/Team 结构：所有 Worker 先创建，Team 只引用成员，并且只能有一个 `team_leader`。

当前 Tool Gateway 是比赛允许的 MCP 等价 HTTP 契约。真实企业接入时，只替换传输/Adapter，不改变 Skill、ActionPlan、Policy、Verification 语义。

## Vercel 语义

Vercel 入口为 `POST /api/run`，一次请求内完成整个 Sandbox Run 并返回证据包。Vercel Serverless 不保存本地 Artifact；需要持久化时接入 PostgreSQL/对象存储。现场需要展示落盘证据时应运行本地服务器。
