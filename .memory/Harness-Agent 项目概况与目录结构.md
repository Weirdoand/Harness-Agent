---
name: Harness-Agent 项目概况与目录结构
type: 项目事实
description: 项目路径、顶层结构、skills、workspace/notesapi 文件与测试参照。
---

项目路径 H:/AI Files/Harness-Agent，以 Python 为主，是 Notes API 基线所在。顶层目录：.compression_archive、.memory、.pytest_cache、.task、example、skills、workspace、__pycache__、需求文档；顶层文件：.env、.gitignore、detail.txt、hello.py、llm_chat.py、package-lock.json、test.py、test.txt、test_task_manager.py、update_memory_script.py、update_memory_structure.py。无 package.json，npm install 会 ENOENT 失败。skills 含 agent-builder、code-review、mcp-builder、pdf（各含 SKILL.md）。Notes API 源码在 workspace/notesapi/，含 db.py、schema.sql、verify_schema.py、config.py、auth.py、test_auth.py 等；worktree 内可能各有副本。测试参照 example/demo_pkg/tests/ 与 example/conftest.py。辅助/临时脚本写入 workspace/（notesapi/ 包外，如 workspace/verify_config.py），以免污染被验证模块。