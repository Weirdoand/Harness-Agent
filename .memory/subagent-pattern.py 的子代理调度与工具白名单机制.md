---
name: subagent-pattern.py 的子代理调度与工具白名单机制
type: 参考资料
description: AGENT_TYPES 工具白名单、Task 工具排除规则及子代理运行循环
---

references/subagent-pattern.py 描述子代理（subagent）调度模式：通过 AGENT_TYPES 字典按 agent_type 取该类型的工具白名单，allowed = AGENT_TYPES.get(agent_type, {}).get('tools', '*')；当 allowed == '*' 时返回全部 base_tools（但**不包含 Task 工具**），否则返回 [t for t in base_tools if t['name'] in allowed]。文档注释说明：'*' 表示所有基础工具，其它情况是具体工具名白名单；'Subagents don't get Task tool to prevent infinite recursion.'（子代理不获得 Task 工具以防无限递归）。子代理运行时用同一个 agent loop（静默执行）：while True 中调用 client.messages.create(model=model, system=sub_system, messages=sub_messages, tools=sub_tools, max_tokens=8000)，当 response.stop_reason != 'tool_use' 时跳出并返回结果。