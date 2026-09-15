with open('h:/AI Files/Harness-Agent/llm_chat.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, l in enumerate(lines):
    if i == 1709:
        new_lines.append('SUB_FUNCTIONS["submit_plan"] = submit_plan\n')
        skip = True
    elif skip:
        if l.startswith('# --- 结构化工具调用定义 ---') or l.startswith('class ToolCall:'):
            skip = False
            if l.startswith('# --- 结构化工具调用定义 ---'):
                new_lines.append(l)
            else:
                new_lines.append('# --- 结构化工具调用定义 ---\n')
                new_lines.append(l)
    else:
        new_lines.append(l)

with open('h:/AI Files/Harness-Agent/llm_chat.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
