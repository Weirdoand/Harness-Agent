---
name: Cron定时任务a0f9fbd0
type: 项目事实
description: 一个持久化 Cron 定时任务，每 2 分钟执行一次 run date。
---

存在一个持久化的 Cron 定时任务，任务 ID 为 a0f9fbd0。该任务每 2 分钟触发一次 `run date` 命令（在后台异步运行，结果自动注入上下文）。该任务无需额外操作即可周期性执行；如需停止，可通过任务 ID a0f9fbd0 取消。