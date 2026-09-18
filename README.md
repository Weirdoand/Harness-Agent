# Harness-Agent S15 契约

本项目运行语义对齐 `s15_integrated_harness`，同时保留 OpenAI Chat Completions 适配层。

模型可见的核心工具使用 S15 名称：`bash`、`glob`、`update_task`、`schedule_cron`、`list_crons`、`cancel_cron`、`request_plan`、`review_plan`；旧名称仅作为内部兼容。项目扩展工具单独管理，不冒充内置契约。

安全契约包括：路径必须位于当前 Agent 工作目录；异步 Agent 无 assignment 不得访问文件或 Shell；前台 Bash/MCP 按权限策略执行；MCP 工具使用 `mcp__server__tool` 命名空间和宿主 allowlist；Task 完成必须由 owner 执行；Cron 使用 Lead 同一 history，并采用 pending_delivery、成功 ack、失败 restore。

OpenAI API 仅是传输适配，不改变上述运行语义。`.task`、`.cron`、`.message_bus`、`.worktrees` 为运行数据，程序不会自动迁移或清理。
