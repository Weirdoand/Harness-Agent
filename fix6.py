with open('h:/AI Files/Harness-Agent/llm_chat.py', 'r', encoding='utf-8') as f:
    text = f.read()

dup_schema = """
    {
        "type": "function",
        "function": {
            "name": "spawn_teammate",
            "description": "启动一个新的 Teammate。在调用之前，必须先向用户提议并获得用户的明确批准确认！",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string"},
                    "task_id": {"type": "string"}
                },
                "required": ["agent_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_teammates",
            "description": "列出当前所有运行中的队友。",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_shutdown",
            "description": "关闭并销毁一个 Teammate。",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string"}
                },
                "required": ["agent_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "发送任意消息给指定的 Teammate。",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "message": {"type": "string"}
                },
                "required": ["to", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_worktree",
            "description": "为任务分配隔离的 Git Worktree 目录 (即 allocate_worktree)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "worktree_path": {"type": "string"}
                },
                "required": ["task_id", "worktree_path"]
            }
        }
    },
"""

# Replace the first occurrence with empty string (it occurs twice)
text = text.replace(dup_schema, "", 1)

# Also check for duplicate list of tools like `allocate_worktree` vs `create_worktree`
# We have both allocate_worktree and create_worktree in schemas, that's fine as long as names are unique.

with open('h:/AI Files/Harness-Agent/llm_chat.py', 'w', encoding='utf-8') as f:
    f.write(text)
