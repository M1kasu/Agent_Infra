# Skill 清单

| Skill | Agent | 输入 → 输出 | 风险 | 依赖 |
|---|---|---|---:|---|
| EmployeeContextSkill | Context | StructuredIncident → EmployeeContext | LOW | IAM/VPN/Application/ServiceHealth Tool |
| AccessDiagnosisSkill | Diagnosis | EmployeeContext → DiagnosisResult | LOW | Context + 安全策略 |
| AccountRemediationSkill | Remediation | Diagnosis + user → ExecutionRecord | MEDIUM | IAMTool + RiskPolicy |
| AccessVerificationSkill | Remediation/Verification | user + app → VerificationResult | LOW | IAMTool + ApplicationTool |

可执行定义位于 `app/skills/`；AgentTeams 可分发包位于 `agentteams/skills/`。每个 Skill 均明确包含 `name`、`description`、`input_schema`、`output_schema`、`preconditions`、`postconditions`、`risk_level`、`dependencies`、`failure_handling`。
