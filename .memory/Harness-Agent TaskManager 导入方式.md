---
name: Harness-Agent TaskManager 导入方式
type: 项目事实
description: 在 Harness-Agent 环境中导入 TaskManager 时 task_manager 模块不存在，需从 llm_chat 加载。
---

在 H:\AI Files\Harness-Agent 环境中，直接 `import task_manager` 会失败，报 ModuleNotFoundError("No module named 'task_manager'")。正确的做法是从 `llm_chat` 模块加载 TaskManager（输出显示 'loaded TaskManager from: llm_chat'）。创建新任务后 TaskManager 会打印形如 '[TaskManager] 成功创建新任务: <uuid> (主题: ...)' 的日志。