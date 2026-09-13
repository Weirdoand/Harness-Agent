---
name: Cron 定时任务 a0f9fbd0 (run date)
type: 项目事实
description: 项目中存在一个名为 run date 的 Cron 定时任务，周期性执行 date 命令
---

环境内配置了 Cron 定时任务，ID 为 a0f9fbd0，名称为 `run date`，作用是执行 `date` 命令。触发方式为【Cron 定时任务触发】提示。执行时命令会在后台异步运行（返回形如 4d99c1a6 的后台任务 ID），结果完成后自动注入上下文，属于正常周期性执行，无需额外操作。