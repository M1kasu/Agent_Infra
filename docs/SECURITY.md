# 安全边界与风险控制

## 风险等级

| 动作 | 风险 | 初赛策略 |
|---|---:|---|
| 读取员工、VPN、权限、服务和访问状态 | LOW | 自动 |
| 解锁已明确诊断为锁定的普通账号 | MEDIUM | 自动、幂等、审计、执行后验证、最多重试一次 |
| 授予应用权限 | HIGH | 阻断自动执行，要求 Human Approval |
| 授予管理员权限 | CRITICAL | 阻断自动执行，双人审批与专用审计（复赛实现） |

`RiskPolicy` 是确定性策略代码，不交给模型自由决定。Manager 没有企业系统写权限；Context/Diagnosis 保持只读；只有 Remediation Worker 能调用账号解锁。

## 初赛已实现

- 最小权限 Agent Identity；
- MEDIUM 及以下自动执行、HIGH/CRITICAL 拒绝自动执行的策略；
- 任务级幂等键；
- 每次 Tool 调用和状态迁移留痕；
- 执行后重新读取真实状态和功能访问；
- Fake Success 检测与一次有界重试；
- 未知根因 fail closed。

## 尚未实现

- Human Approval 的交互与签名记录；
- 权限授予和管理员动作；
- 通用补偿/回滚（账号解锁本身采用幂等重试）；
- 真实 SSO、密钥、RBAC、Higress Consumer 策略；
- 不可篡改审计存储和数据脱敏。
