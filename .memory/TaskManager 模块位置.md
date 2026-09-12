---
name: TaskManager 模块位置
type: 项目事实
description: TaskManager 类位于 llm_chat 模块，而非 task_manager 模块
---

在项目中，TaskManager 类可以从 `llm_chat` 模块导入。尝试 `import task_manager` 会失败，应使用 `from llm_chat import TaskManager`。