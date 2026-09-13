---
name: Harness-Agent TaskManager 导入方式
type: 项目事实
description: TaskManager 类位于 llm_chat 模块，直接 import task_manager 会失败。
---

在 `H:\AI Files\Harness-Agent` 环境中，直接 `import task_manager` 会失败，报 `ModuleNotFoundError("No module named 'task_manager'")`。正确做法是从 `llm_chat` 模块加载 TaskManager：`from llm_chat import TaskManager`（输出显示 'loaded TaskManager from: llm_chat'）。创建新任务后 TaskManager 会打印形如 `[TaskManager] 成功创建新任务: <uuid> (主题: ...)` 的日志。