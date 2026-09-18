---
name: Harness-Agent 真实实现 llm_chat.py 与教学样例的差异
type: 项目事实
description: 仓库中真正运行的 agent 循环位于 llm_chat.py，比教学样例多出重试、门禁、消息总线、plan 审批等机制
---

references/minimal-agent.py 和 subagent-pattern.py 只是 skill 内的教学样例；本仓库真正跑起来的 agent 循环在 llm_chat.py（约 130KB）。相比约 20 行的最小版本，它额外包含：重试机制、门禁（审批/拦截）、消息总线、plan（计划）审批流程等。若要讲解或修改真实行为，应去定位 llm_chat.py 的主循环。相关脚本还包括 scripts/init_agent.py（可用于初始化/脚手架一个 agent），实验代码通常放在 workspace/ 目录。