---
name: complete_task 方法行为
type: 项目事实
description: complete_task 方法更新任务状态并解锁依赖任务
---

`TaskManager.complete_task(task_id)` 方法在文件锁保护下读取任务，检查任务是否存在且状态为 IN_PROCESS，然后将其状态设为 COMPLETE，更新 updated_at，并找出所有依赖该任务的任务，将其解锁。返回新解锁的任务列表。