---
name: Cron 定时任务 a0f9fbd0
type: 项目事实
description: 环境中存在一个每 2 分钟执行一次 date 命令的 Cron 定时任务
---

当前环境配置了一个 Cron 定时任务，ID 为 `a0f9fbd0`，触发频率为每 2 分钟一次，执行命令为 `date`。触发时会通过后台任务（Background Task）异步运行，结果完成后自动注入上下文。后续排查定时任务相关问题时可直接引用该 ID 与频率。