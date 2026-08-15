# AgentTeams 上游源码

OfficeOps 不把 AgentTeams 源码复制进业务仓库；官方上游以独立 Git checkout 保留，便于核验来源、升级和遵守许可证。为使 v1.2.2 Windows 安装器完成官方栈部署，该 checkout 保留一处明确记录的本地兼容补丁。

| 项目 | 值 |
|---|---|
| 官方入口 | https://hiclaw.io/ |
| GitHub | https://github.com/agentscope-ai/AgentTeams |
| 本地路径 | `E:\code\AgentTeams-upstream` |
| 固定版本 | `v1.2.2` |
| Commit | `849182af8e017168a5a200a87b1062142caf462d` |
| License | Apache-2.0 |
| 拉取方式 | shallow clone，detached HEAD 固定到 tag |
| 本地改动 | `install/agentteams-install.ps1`，30 行 Windows 安装兼容补丁，未提交 |

核验命令：

```powershell
git -C E:\code\AgentTeams-upstream remote -v
git -C E:\code\AgentTeams-upstream describe --tags --exact-match
git -C E:\code\AgentTeams-upstream rev-parse HEAD
git -C E:\code\AgentTeams-upstream status --short
git -C E:\code\AgentTeams-upstream diff --check
```

## Windows v1.2.2 兼容补丁

补丁只处理安装器参数传递，不修改 AgentTeams Controller、Manager 或 Worker 业务逻辑：

1. 对齐 Linux 安装器，生成、持久化并传入 Matrix AppService enabled/AS/HS token；
2. 在 `keep-all` 升级路径重新填充必需的模型 provider/model/key 和管理员账号参数。

`git diff --check` 已通过。补丁当前只存在于本机 checkout，没有推送或冒充官方版本；升级新 tag 时应先验证官方是否已修复，再决定是否移除。

## 实际部署状态

Docker Desktop 中已运行 Controller、Manager、三个 OfficeOps Worker、Matrix、MinIO 与 Higress。Manager onboarding、Worker Skill 同步、角色隔离 MCP 发现与调用均已验证；真实 `account_lock` Matrix 工单证据保存在 `artifacts/agentteams/agentteams-account-lock-20260815-074611/`。

v1.2.2 还有一个 Manager 配置同步边界：声明式 `spec.agents` 会写入 MinIO 的 `agents/default/AGENTS.md`，而 CoPaw 活动工作区继续使用内置 `AGENTS.md`。OfficeOps 将专用协同约束放在 `agentteams/manager-officeops-policy.md`，并以 `scripts/sync_agentteams_manager_policy.ps1` 幂等同步到 Manager onboarding 管理的根 `SOUL.md` 与 CoPaw 活动 `SOUL.md`。这项运行时适配没有改动上游框架代码。
