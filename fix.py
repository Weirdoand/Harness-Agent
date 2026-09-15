import re
with open('h:/AI Files/Harness-Agent/llm_chat.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('print("\n \033[96m" + "="*15 + " 任务面板 " + "="*15 + " \033[0m")', 'print("\\n\\033[96m" + "="*15 + " 任务面板 " + "="*15 + "\\033[0m")')
text = text.replace('print("\n\033', 'print("\\n\\033')
text = text.replace('print("\n \033', 'print("\\n\\033')
text = text.replace('print("\\033[96m" + "="*40 + "\\033[0m\n")', 'print("\\033[96m" + "="*40 + "\\033[0m\\n")')
text = text.replace('print("\\033[96m" + "="*40 + "\\033[0m\\n")', 'print("\\033[96m" + "="*40 + "\\033[0m\\n")')

# Specifically for line 844:
bad_print = 'print("\n\n \033[96m" + "="*15 + " 任务面板 " + "="*15 + " \033[0m")'.replace('\n\n', '\n')
text = text.replace(bad_print, 'print("\\n\\033[96m" + "="*15 + " 任务面板 " + "="*15 + "\\033[0m")')

bad_print_2 = 'print("\n \033[96m" + "="*15 + " 任务面板 " + "="*15 + " \033[0m")'
text = text.replace(bad_print_2, 'print("\\n\\033[96m" + "="*15 + " 任务面板 " + "="*15 + "\\033[0m")')

with open('h:/AI Files/Harness-Agent/llm_chat.py', 'w', encoding='utf-8') as f:
    f.write(text)
