---
name: task_manager.py 与任务板机制
type: 项目事实
description: TaskManager 导入方式、任务落盘字段、共享任务板与多智能体协作角色。
---

task_manager.py 提供 TaskManager、TaskState，构造支持 data_dir 参数，配套 unittest 测试 TestTaskManager（测试用 .test_task 目录并在 setUp/tearDown 中清理）。任务板落盘至 .task/*.json，每个任务一个 JSON 文件，字段包含 id、subject、description、state、owner、blockBy、worktree、created_at 等；任务状态如 complete，owner 为 teammate 名称，worktree 可能为 None 或 git worktree 路径。多智能体通过共享任务板协调：存在 teammate_auth、teammate_config 等角色，分别负责认证模块、配置抽取等子任务；Lead 审批 teammate 执行计划，任务依赖通过 assign_dependencies 写入并回读校验。在 H:/AI Files/Harness-Agent 中，直接 import task_manager 会失败（ModuleNotFoundError），正确方式是 from llm_chat import TaskManager。创建新任务会打印 [TaskManager] 成功创建新任务: <uuid> (主题: ...)。工具函数：_now、_read_tasks、_write_tasks、assign_dependencies、claim_。