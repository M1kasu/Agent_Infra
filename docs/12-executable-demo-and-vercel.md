# 12 · Executable Demo & Vercel Deployment

## 交付物定位

仓库中的可执行 Demo 分为两条路径：

| 路径 | 用途 | 状态语义 |
| --- | --- | --- |
| 本地 Node Demo | 现场演示、自动测试、Evidence/Trace 落盘、AgentTeams HTTP Tool Gateway | 有状态，按 `run_id` 隔离 |
| Vercel Web Demo | 评委在线查看 UI、正常/Fake Success 对比和完整 JSON Artifact | 单请求内有状态，响应结束后不持久化 |

Vercel 页面不是 AgentTeams runtime 托管平台。真实 Matrix/Team/Worker 协作仍运行在 AgentTeams；Vercel 用于展示同一领域契约和可重复的 Mock 闭环。

## 本地验收

```bash
node --test demo/tests/*.test.mjs
node demo/scripts/check-config.mjs
node demo/cli.mjs --mode normal
node demo/cli.mjs --mode fake_success
node demo/server.mjs
```

打开 `http://localhost:18110`。

## GitHub → Vercel

### 1. 推送 GitHub

确认以下文件位于仓库根目录：

- `package.json`
- `vercel.json`
- `public/index.html`
- `api/run.js`
- `api/health.js`

把本分支提交并推送到 GitHub。Vercel 会为分支/PR 创建 Preview Deployment，生产分支通常使用 `main`。

### 2. 导入 Vercel

1. 登录 <https://vercel.com/new>；
2. 连接 GitHub 并选择 Agent Infra 仓库；
3. Project Root Directory 保持仓库根目录 `./`；
4. Framework Preset 选择 `Other`；
5. 不填写 Build Command；
6. Output Directory 使用仓库 `vercel.json` 中的 `public`；
7. 当前 Mock 不需要环境变量；
8. 点击 Deploy。

部署后检查：

```text
GET  https://<project>.vercel.app/api/health
POST https://<project>.vercel.app/api/run
```

### 3. 后续自动发布

- 推送非生产分支或新建 PR：生成独立 Preview URL；
- 合并到生产分支：生成 Production Deployment；
- Vercel Project Settings → Git 可修改生产分支；
- 真实 Token/数据库连接只放 Vercel Environment Variables，不写入仓库。

## 限制与演进

- Vercel Serverless 文件系统不作为 Artifact 持久化方案；当前 `/api/run` 在响应内返回全量 Evidence/Trace。
- 若需要保存在线 Run，接入 PostgreSQL 与对象存储，并继续使用 `run_id + artifact_hash`。
- 不在 Vercel 放企业 IAM/VPN 凭据；真实 Tool Gateway 应部署在企业网络或受控云环境。
- AgentTeams Worker 访问本机 Demo 时使用 `host.docker.internal:18110`；访问远程受控 Gateway 时替换 Adapter 地址，不改变 Skill 契约。

