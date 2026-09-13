---
name: Cron 定时任务 run date
type: 项目事实
description: 项目中存在一个每 2 分钟触发、执行 date 命令的 Cron 定时任务 a0f9fbd0
---

该对话由 Cron 定时任务触发。任务 ID 为 a0f9fbd0，名称为 "run date"，每 2 分钟触发一次，执行 `date` 命令；命令通过后台异步任务运行（Background Task），执行结果会在完成后自动注入上下文，属于正常周期性执行，无需额外操作。