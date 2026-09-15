import re

with open('h:/AI Files/Harness-Agent/llm_chat.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. HOOK Logs
text = re.sub(r'print\(f"\\033\[94m\[HOOK: before_loop\] 记录用户输入: .*?\\033\[0m"\)', 'pass', text)
text = re.sub(r'print\(f"\\033\[94m\[HOOK: before_tool\] 开始工具权限校验 -> .*?\\033\[0m"\)', 'pass', text)
text = re.sub(r'print\(f"\\033\[33m\[调用工具\] AI 决定执行: .*?\\033\[0m"\)', 'pass', text)
text = re.sub(r'print\(f"\\033\[90m\[HOOK: after_tool\] 工具 .*?\\033\[0m"\)', 'pass', text)
text = re.sub(r'print\(f"\\033\[94m\[HOOK: after_loop\] 本轮交互结束.*?\\033\[0m"\)', 'pass', text)

# 2. TaskManager auto prints
text = text.replace('self.print_task_panel()', '# self.print_task_panel()')
text = re.sub(r'print\(f"\\033\[92m\[TaskManager\].*?\\033\[0m"\)', 'pass', text)

# 3. Memory Manager logs
text = text.replace('print("\\033[94m[Memory] 正在总结记忆并存储...\\033[0m")', 'pass')
text = re.sub(r'print\(f"\\033\[92m\[Memory\] 已保存记忆: \{record\[\'filename\'\]\}\\033\[0m"\)', 'pass', text)
text = text.replace('print("\\033[94m[Memory] 记忆条目超过30条，正在合并与整理...\\033[0m")', 'pass')
text = re.sub(r'print\(f"\\033\[92m\[Memory\] 记忆库合并整理完成.*?\\033\[0m"\)', 'pass', text)

# 4. Background Task logs
text = re.sub(r'print\(f"\\033\[96m\[Background Task\].*?\\033\[0m"\)', 'pass', text)

# 5. Teammate/Subagent logs
text = re.sub(r'print\(f"\\033\[92m\[\{self.name\}\] 进入 WORK.*?\\033\[0m"\)', 'pass', text)
text = re.sub(r'print\(f"\\033\[92m\[\{self.name\}\] 任务执行告一段落.*?\\033\[0m"\)', 'pass', text)
text = re.sub(r'print\(f"\\033\[92m\[Subagent Start\].*?\\033\[0m"\)', 'pass', text)
text = text.replace('print(f"\\033[92m[Subagent End] 子任务执行完毕。\\033[0m")', 'pass')

with open('h:/AI Files/Harness-Agent/llm_chat.py', 'w', encoding='utf-8') as f:
    f.write(text)
