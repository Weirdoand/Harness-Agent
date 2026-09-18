---
name: llm_chat.py 核心职责与全局运行参数
type: 项目事实
description: llm_chat.py 单文件承载运行时：LLM 调用、后台管理、压缩、技能加载、工具实现与全局参数。
---

llm_chat.py（约 133KB，仓库最大文件）是 harness 的核心，单文件包含：1) OpenAI Chat Completions 适配层 call_llm，含 429/529 重试、length 截断续写、fallback model；2) BackgroundManager——后台任务并发上限 5，使用 taskkill/进程组树终止；3) Compression——4 级上下文压缩策略（工具结果归档截断 → 滑动窗口 → 动态驱逐 → LLM 总结）以及超长错误恢复；4) SkillLoader——扫描 skills/*/SKILL.md 的 frontmatter，提供 load_skill 与技能清单注入；5) 全部工具实现：run_bash、read_file/write_file/edit_file（原子写）、glob 等。全局运行参数：MAX_SUBAGENT_ITERATIONS=30（run_subagent 子代理最大迭代轮数），MAX_TOOL_RESULT_CHARS=20000（单条工具结果追加进对话上下文的最大长度，超长截断）。另使用 threading.local() 的 TURN_CONTEXT 保存轮次上下文，并定义 LLMCallResult 数据类。修改核心文件前应格外谨慎。