import re
with open('h:/AI Files/Harness-Agent/llm_chat.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad = """
    },

BASE_TOOLS.extend(["""

good = """
    }
])
BASE_TOOLS.extend(["""

text = text.replace(bad, good)

with open('h:/AI Files/Harness-Agent/llm_chat.py', 'w', encoding='utf-8') as f:
    f.write(text)
