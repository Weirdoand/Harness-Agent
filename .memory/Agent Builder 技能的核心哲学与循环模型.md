---
name: Agent Builder 技能的核心哲学与循环模型
type: 参考资料
description: SKILL.md 中关于 agent 本质是简单循环、模型自带 agent 能力的论述
---

Agent Builder skill（SKILL.md）的核心哲学：'The model already knows how to be an agent. Your job is to get out of the way.' 即 agent 不是复杂工程，而是一个邀请模型行动的简单循环：

LOOP:
  Model sees: context + available capabilities
  Model decides: act or respond
  If act: execute capability, add result, continue
  If respond: return to user

所谓“魔法”不在代码里，而在模型本身，代码只负责提供机会。SKILL.md 的章节结构包括：The Core Philosophy、The Three Elements（1. Capabilities/能做什么 2. Knowledge/知道什么 3. Context/发生过什么）、Agent Design Thinking、Progressive Complexity、Domain Examples、Key Principles、Anti-Patterns、Resources、The Agent Mindset。