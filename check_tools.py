import re
with open('h:/AI Files/Harness-Agent/llm_chat.py', 'r', encoding='utf-8') as f:
    text = f.read()

names = re.findall(r'"name": "([^"]+)"', text)
print('Tool names found in text:', names)
