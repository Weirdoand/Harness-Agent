import re
with open('h:/AI Files/Harness-Agent/llm_chat.py', 'r', encoding='utf-8') as f:
    text = f.read()

# find print_task_panel
start = text.find('def print_task_panel(self):')
end = text.find('def create_task(', start)

new_print_task_panel = '''def print_task_panel(self):
        tasks = self.list_tasks()
        print("\\n\\033[96m" + "="*15 + " 任务面板 " + "="*15 + "\\033[0m")
        if not tasks:
            print("  暂无任务")
        else:
            for i, t in enumerate(tasks, 1):
                state_flags = {
                    TaskState.PENDING.value: "[ ]",
                    TaskState.IN_PROCESS.value: "[-]",
                    TaskState.COMPLETE.value: "[x]"
                }
                flag = state_flags.get(t["state"], "[?]")
                owner_info = f" (执行者: {t['owner']})" if t.get("owner") else ""
                dep_info = f" [依赖: {','.join(t.get('blockBy', []))}]" if t.get("blockBy") else ""
                worktree_info = f" [Worktree: {t.get('worktree')}]" if t.get("worktree") else ""
                state_str = f"状态: {t['state']}"
                print(f"  {flag} {i}. {t['subject']}{owner_info}{dep_info}{worktree_info} | {state_str} | ID: {t['id']}")
        print("\\033[96m" + "="*40 + "\\033[0m\\n")

    '''

text = text[:start] + new_print_task_panel + text[end:]

# Fix create_task's print
text = re.sub(r'print\(f"\n\s*\[92m\[TaskManager\]', r'print(f"\\033[92m[TaskManager]', text)

with open('h:/AI Files/Harness-Agent/llm_chat.py', 'w', encoding='utf-8') as f:
    f.write(text)
