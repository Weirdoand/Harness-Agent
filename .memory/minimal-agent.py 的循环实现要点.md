---
name: minimal-agent.py 的循环实现要点
type: 参考资料
description: references/minimal-agent.py 中 agent() 函数的循环写法与消息历史维护方式
---

references/minimal-agent.py 是 SKILL.md 循环哲学的最小逐字实现。核心在 agent(prompt, history=None) 函数（约 100–131 行）：使用 while True 循环，调用 client.messages.create(model=..., system=..., messages=..., tools=..., max_tokens=8000)，通过 response.stop_reason != 'tool_use' 判断结束；遇到 tool_use 时执行工具，把结果组织成 {'type':'tool_result','tool_use_id': block.id,'content': output} 追加到 results，再用 history.append({'role':'user','content': results}) 把工具结果回灌进对话历史，然后继续循环。主程序入口 `if __name__ == '__main__':` 打印 'Minimal Agent - {WORKDIR}'，提示 "Type 'q' to quit."，用 input('>> ') 读取用户查询并捕获 EOFError。