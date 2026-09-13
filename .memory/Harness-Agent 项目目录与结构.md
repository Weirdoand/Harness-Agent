---
name: Harness-Agent 项目目录与结构
type: 项目事实
description: 工作目录 H:\AI Files\Harness-Agent 的顶层内容与 workspace、归档路径。
---

Harness-Agent 项目工作目录为 `H:\AI Files\Harness-Agent`。顶层包含目录：`.compression_archive`、`.memory`、`.pytest_cache`、`.task`、`example`、`skills`、`workspace`、`__pycache__`、`需求文档`；文件：`.env`、`.gitignore`、`detail.txt`、`hello.py`、`llm_chat.py`、`package-lock.json`、`test.py`、`test.txt`、`test_task_manager.py`、`update_memory_script.py`、`update_memory_structure.py`。整体是以 Python 为主的项目（含记忆管理、任务管理相关脚本），并非 Node/前端项目。工作区位于 `H:\AI Files\Harness-Agent\workspace\`（例如脚本 create_tasks.py 写入此处）。工具结果的本地归档路径在 `H:\AI Files\Harness-Agent\.compression_archive\tool-result\` 下，文件名形如 `tool_result_<hash>.txt`。