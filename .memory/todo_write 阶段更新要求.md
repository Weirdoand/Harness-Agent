---
name: todo_write 阶段更新要求
type: 项目事实
description: Harness-Agent 要求定期调用 todo_write 更新子任务状态。
---

在 Harness-Agent 中，如果连续 3 次及以上未更新任务阶段步骤，系统会提示调用 todo_write 工具更新当前分解的子任务状态与进展。更新后应展示形如 '[x]/[-]/[ ] 序号. 步骤名' 的阶段任务清单。