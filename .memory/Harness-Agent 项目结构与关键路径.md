---
name: Harness-Agent 项目结构与关键路径
type: 项目事实
description: Harness-Agent 仓库的工作目录、工具结果归档目录及主要文件/目录布局
---

项目根目录（WORKDIR）为 H:\AI Files\Harness-Agent。工具输出会被本地归档到 H:\AI Files\Harness-Agent\.compression_archive\tool-result\ 下，文件名为 tool_result_<hash>.txt（如 tool_result_890d89cb.txt），内容以 [结果前缀] 形式给出截断片段。仓库中已知的重要位置：SKILL.md（Agent Builder 技能主文档）、references/ 目录（含 minimal-agent.py、subagent-pattern.py、tool-templates.py 等参考实现）、scripts/ 目录（含 init_agent.py）、llm_chat.py（约 130KB，是真正运行的 agent 实现）、workspace/ 目录（用于放置可运行的实验 agent）。