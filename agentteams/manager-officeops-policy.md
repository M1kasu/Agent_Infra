### OfficeOps 固定协同协议

- `account_lock` 事件是固定的三阶段流水线，不创建 Project、taskflow 任务或共享任务文件。
- 只通过现有 Matrix Worker 房间依次委派：`officeops-context` → `officeops-diagnosis` → `officeops-remediation-verification`。
- 每次交接都要把上一位 Worker 返回的完整结构化结果原样内联到下一条委派消息中，不能只写“已收集”或自行概括掉证据。
- 必须等待当前阶段返回有效结果才能推进。若 Worker 返回 `BLOCKED`，先补齐其指出的内联输入并重试当前阶段；不得自行推断该阶段结果，也不得声称该 Worker 已完成贡献。
- Diagnosis 的有效结果必须明确包含 `root_cause` 和 `recommended_action`；Remediation 的有效结果必须包含变更回执以及变更后的身份状态、访问状态独立复查证据。
- 只有三位 Worker 均返回有效结果，且最终复查证明账户未锁定、访问恢复后，才可向管理员输出以 `OFFICEOPS_DONE` 开头的终态消息。
