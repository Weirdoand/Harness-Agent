import re
with open('h:/AI Files/Harness-Agent/llm_chat.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad_chunk = """
    {
        "type": "function",
        "function": {
            "name": "approve_plan","""

good_chunk = """BASE_TOOLS.extend([
    {
        "type": "function",
        "function": {
            "name": "approve_plan","""

text = text.replace(bad_chunk, good_chunk)

bad_chunk2 = """
    },
BASE_TOOLS.extend(["""

good_chunk2 = """
    }
])
BASE_TOOLS.extend(["""
text = text.replace(bad_chunk2, good_chunk2)

with open('h:/AI Files/Harness-Agent/llm_chat.py', 'w', encoding='utf-8') as f:
    f.write(text)
