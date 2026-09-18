---
name: Agent 设计参考资料与最小循环实现
type: 参考资料
description: Agent 三大要素、核心理念、agent-builder 资料路径与最小循环实现。
---

Agent 的三大要素：Capabilities（能力，它能做什么）、Knowledge（知识，它知道什么）、Context（上下文，发生了什么）。Agent 核心理念（来自 SKILL.md）：'The model already knows how to be an agent. Your job is to get out of the way.'（模型已经知道如何成为 agent，你的工作是别挡路。）Agent 本质不是复杂工程，而是一个简单的循环，邀请模型行动：模型看到 context + 可用能力 → 决定行动或回复 → 若行动则执行能力、添加结果、继续；若回复则返回给用户。魔法不在代码里，而在模型里，代码只是提供机会。需要真实（非 mock）的 agent loop 说明时，可读取仓库内资料：skills/agent-builder/SKILL.md（技能说明），及其 references/ 目录下的示例实现 minimal-agent.py（最小 agent 实现）与 subagent-pattern.py（子代理模式）；这些是仓库自带的权威资料，优于 mock 的 docs MCP 检索结果。最小版循环实现在 references/minimal-agent.py 的 agent() 函数（约 100–131 行）：核心为 while True 循环，调用 client.messages.create(model, system, messages, tools, max_tokens)，若 response.stop_reason != 'tool_use' 则跳出循环结束；否则执行工具，把 tool_result（含 type、tool_use_id、content）追加到 history 的 user 消息中继续循环。Subagent 不分配 Task 工具以防无限递归；工具权限通过 AGENT_TYPES 白名单（'*' 表示所有基础工具但排除 Task）控制。相关设计主题还包括：Agent Design Thinking、Progressive Complexity、Domain Examples、Key Principles、Anti-Patterns、The Agent Mindset。