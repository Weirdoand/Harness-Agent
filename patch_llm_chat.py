import os
import re

with open('h:/AI Files/Harness-Agent/llm_chat.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Insert global dicts and MessageBus, TeammateRuntime, Worktree logics around line 742 (before TaskManager)
insert_globals = """
# ---------- AgentTeam 架构扩展 ----------
import glob
from filelock import FileLock
import time

teammate_assignments = {} # AgentName -> worktree_path
plan_gates = {}           # AgentName -> required/pending/approved/not_required

def get_agent_cwd() -> str:
    agent_name = threading.current_thread().name
    return teammate_assignments.get(agent_name, os.getcwd())

def resolve_path(file_path: str) -> str:
    if os.path.isabs(file_path):
        return file_path
    return os.path.join(get_agent_cwd(), file_path)

class MessageBus:
    def __init__(self, data_dir=".message_bus"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _get_inbox_path(self, agent_name: str) -> str:
        return os.path.join(self.data_dir, f"{agent_name}.json")
        
    def _get_lock_path(self, agent_name: str) -> str:
        return os.path.join(self.data_dir, f"{agent_name}.lock")
        
    def send(self, message: dict):
        to_agent = message.get("to")
        if not to_agent: return
        with FileLock(self._get_lock_path(to_agent)):
            inbox_path = self._get_inbox_path(to_agent)
            inbox = []
            if os.path.exists(inbox_path):
                try:
                    with open(inbox_path, "r", encoding="utf-8") as f:
                        inbox = json.load(f)
                except Exception:
                    pass
            inbox.append(message)
            with open(inbox_path, "w", encoding="utf-8") as f:
                json.dump(inbox, f, ensure_ascii=False, indent=2)
                
    def read_inbox(self, agent_name: str) -> list:
        with FileLock(self._get_lock_path(agent_name)):
            inbox_path = self._get_inbox_path(agent_name)
            if os.path.exists(inbox_path):
                try:
                    with open(inbox_path, "r", encoding="utf-8") as f:
                        inbox = json.load(f)
                    os.remove(inbox_path)
                    return inbox
                except Exception:
                    pass
            return []
            
message_bus = MessageBus()
"""

# We'll use regex to inject this before 'class TaskState(str, Enum):'
code = code.replace("class TaskState(str, Enum):", insert_globals + "\nclass TaskState(str, Enum):")

# 2. Rewrite TaskManager
new_task_manager = """
class TaskManager:
    def __init__(self, data_dir=".task"):
        self.data_dir = data_dir
        self.lock_path = os.path.join(self.data_dir, "tasks_global.lock")
        os.makedirs(self.data_dir, exist_ok=True)
        # 兼容旧逻辑
        old_file = os.path.join(self.data_dir, "tasks.json")
        if os.path.exists(old_file):
            try:
                with open(old_file, "r", encoding="utf-8") as f:
                    old_tasks = json.load(f)
                for t in old_tasks:
                    self._write_task(t)
                os.remove(old_file)
            except Exception:
                pass

    def _read_tasks(self) -> list:
        tasks = []
        for file_path in glob.glob(os.path.join(self.data_dir, "task_*.json")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tasks.append(json.load(f))
            except Exception:
                pass
        return tasks

    def _write_task(self, task: dict):
        file_path = os.path.join(self.data_dir, f"task_{task['id']}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(task, f, ensure_ascii=False, indent=2)

    def _now(self) -> str:
        return datetime.now(timezone.utc).astimezone().isoformat()

    def print_task_panel(self):
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

    def create_task(self, subject: str, description: str, worktree: str = None) -> str:
        with FileLock(self.lock_path):
            new_id = str(uuid.uuid4())
            new_task = {
                "id": new_id,
                "subject": subject,
                "description": description,
                "state": TaskState.PENDING.value,
                "owner": None,
                "blockBy": [],
                "worktree": worktree,
                "created_at": self._now(),
                "updated_at": self._now()
            }
            self._write_task(new_task)
            print(f"\\033[92m[TaskManager] 成功创建新任务: {new_id} (主题: {subject})\\033[0m")
        self.print_task_panel()
        return new_id

    def assign_dependencies(self, task_id: str, depends_on_ids: list) -> bool:
        with FileLock(self.lock_path):
            tasks = self._read_tasks()
            task = next((t for t in tasks if t["id"] == task_id), None)
            if not task:
                print(f"\\033[31m[TaskManager] 分配依赖失败: 未找到任务 {task_id}\\033[0m")
                return False
            
            task["blockBy"] = list(set(task.get("blockBy", []) + depends_on_ids))
            task["updated_at"] = self._now()
            self._write_task(task)
            print(f"\\033[92m[TaskManager] 任务 {task_id} 新增依赖: {depends_on_ids}\\033[0m")
        self.print_task_panel()
        return True

    def claim_task(self, task_id: str, owner: str) -> dict:
        with FileLock(self.lock_path):
            tasks = self._read_tasks()
            task = next((t for t in tasks if t["id"] == task_id), None)
            
            if not task:
                return {"success": False, "error": "任务不存在"}
                
            if task["state"] != TaskState.PENDING.value:
                return {"success": False, "error": "任务状态必须为 pending"}
                
            dependency_ids = task.get("blockBy", [])
            for dep_id in dependency_ids:
                dep_task = next((t for t in tasks if t["id"] == dep_id), None)
                if not dep_task or dep_task["state"] != TaskState.COMPLETE.value:
                    return {"success": False, "error": f"前置依赖任务 {dep_id} 未完成"}
            
            task["state"] = TaskState.IN_PROCESS.value
            task["owner"] = owner
            task["updated_at"] = self._now()
            self._write_task(task)
            return {"success": True, "task": task}

    def complete_task(self, task_id: str) -> list:
        with FileLock(self.lock_path):
            tasks = self._read_tasks()
            task = next((t for t in tasks if t["id"] == task_id), None)
            
            if not task or task["state"] != TaskState.IN_PROCESS.value:
                return []
                
            task["state"] = TaskState.COMPLETE.value
            task["updated_at"] = self._now()
            self._write_task(task)
            
            unlocked_tasks = []
            for t in tasks:
                if t["state"] == TaskState.PENDING.value and task_id in t.get("blockBy", []):
                    deps_completed = True
                    for dep_id in t.get("blockBy", []):
                        dep_task = next((dt for dt in tasks if dt["id"] == dep_id), None)
                        if not dep_task or dep_task["state"] != TaskState.COMPLETE.value:
                            deps_completed = False
                            break
                    if deps_completed:
                        unlocked_tasks.append(t)
            return unlocked_tasks

    def get_task(self, task_id: str) -> dict:
        with FileLock(self.lock_path):
            tasks = self._read_tasks()
            task = next((t for t in tasks if t["id"] == task_id), None)
            return task

    def list_tasks(self, state: str = None, owner: str = None) -> list:
        with FileLock(self.lock_path):
            tasks = self._read_tasks()
            filtered = tasks
            if state:
                filtered = [t for t in filtered if t.get("state") == state]
            if owner:
                filtered = [t for t in filtered if t.get("owner") == owner]
            return filtered
"""

# Replace old TaskManager
task_manager_pattern = re.compile(r'class TaskManager:.*?task_manager = TaskManager\(\)', re.DOTALL)
code = task_manager_pattern.sub(new_task_manager + "\n\ntask_manager = TaskManager()", code)


# 3. Patch tools to use get_agent_cwd()
code = code.replace("cwd=kwargs.get(\"cwd\", \".\")", "cwd=get_agent_cwd()")
code = code.replace("cwd=kwargs.get(\"cwd\")", "cwd=get_agent_cwd()")

# BackgroundManager Popen cwd
bg_popen = "process = subprocess.Popen(\\n                        command,\\n                        shell=True,\\n                        stdout=subprocess.PIPE,\\n                        stderr=subprocess.STDOUT,\\n                        text=True,\\n                        errors='replace'\\n                    )"
bg_popen_new = "process = subprocess.Popen(\\n                        command,\\n                        shell=True,\\n                        cwd=get_agent_cwd(),\\n                        stdout=subprocess.PIPE,\\n                        stderr=subprocess.STDOUT,\\n                        text=True,\\n                        errors='replace'\\n                    )"
code = code.replace(bg_popen, bg_popen_new)

# run_bash cwd
run_bash_old = "result = subprocess.run(\\n            command,\\n            shell=True,\\n            capture_output=True,\\n            text=True,\\n            errors='replace', # 防止 Windows 下某些命令由于输出特殊字符导致解码报错\\n            timeout=60 # 防止某些命令卡死\\n        )"
run_bash_new = "result = subprocess.run(\\n            command,\\n            shell=True,\\n            cwd=get_agent_cwd(),\\n            capture_output=True,\\n            text=True,\\n            errors='replace', # 防止 Windows 下某些命令由于输出特殊字符导致解码报错\\n            timeout=60 # 防止某些命令卡死\\n        )"
code = code.replace(run_bash_old, run_bash_new)

# write_file / read_file / edit_file
code = code.replace("def write_file(file_path: str, content: str) -> str:", "def write_file(file_path: str, content: str) -> str:\\n    file_path = resolve_path(file_path)")
code = code.replace("def read_file(file_path: str) -> str:", "def read_file(file_path: str) -> str:\\n    file_path = resolve_path(file_path)")
code = code.replace("def edit_file(file_path: str, old_text: str, new_text: str) -> str:", "def edit_file(file_path: str, old_text: str, new_text: str) -> str:\\n    file_path = resolve_path(file_path)")
code = code.replace("def glob_bash(pattern: str) -> str:\\n    import glob", "def glob_bash(pattern: str) -> str:\\n    import glob\\n    cwd = get_agent_cwd()\\n    pattern = os.path.join(cwd, pattern) if not os.path.isabs(pattern) else pattern")

# 4. Control Protocol & Gates in hook_check_tool_permission
hook_check = """
    # AgentTeam 闸门拦截逻辑
    agent_name = threading.current_thread().name
    if tool.name in ["run_bash", "write_file", "edit_file"] and agent_name in plan_gates:
        status = plan_gates[agent_name]
        if status not in ["approved", "not_required"]:
            return False, f"执行失败：你的状态为 {status}，工具 {tool.name} 被闸门拦截。请务必调用 submit_plan 提交执行计划给 Lead 审批！"
"""
code = code.replace('print(f"\\033[94m[HOOK: before_tool] 开始工具权限校验 -> {tool.name} | 操作信息: {args_str}\\033[0m")', 
                    'print(f"\\033[94m[HOOK: before_tool] 开始工具权限校验 -> {tool.name} | 操作信息: {args_str}\\033[0m")\n' + hook_check)

# 5. Add submit_plan tool
submit_plan_func = """
def submit_plan(plan_details: str, **kwargs) -> str:
    agent_name = threading.current_thread().name
    plan_gates[agent_name] = "pending"
    message_bus.send({
        "from": agent_name,
        "to": "lead",
        "type": "submit_plan",
        "request_id": str(uuid.uuid4())[:8],
        "content": plan_details
    })
    return "执行计划已通过 MessageBus 提交给 Lead，请等待审批结果或主动转入 idle 状态。"
"""
code = code.replace('def compact(**kwargs) -> str:', submit_plan_func + '\ndef compact(**kwargs) -> str:')
code = code.replace('FUNCTIONS["compact"] = compact', 'FUNCTIONS["compact"] = compact\nFUNCTIONS["submit_plan"] = submit_plan\nSUB_FUNCTIONS["submit_plan"] = submit_plan')

submit_plan_schema = """
    {
        "type": "function",
        "function": {
            "name": "submit_plan",
            "description": "向 Lead 提交执行计划。当你被闸门拦截 (例如状态为 required/pending) 无法执行破坏性操作时，必须调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_details": {"type": "string"}
                },
                "required": ["plan_details"]
            }
        }
    },
"""
code = code.replace('BASE_TOOLS = [', 'BASE_TOOLS = [\n' + submit_plan_schema)


# 6. TeammateRuntime Class
teammate_runtime = """
class TeammateRuntime:
    def __init__(self, name: str):
        self.name = name
        self.thread = threading.Thread(target=self.run, name=self.name, daemon=True)
        self.system_prompt = SUBAGENT_SYSTEM_PROMPT + "\\n你是执行 Agent，可以通过 task 抢占任务。当没有指令时请进入 IDLE，被拦截时使用 submit_plan。"
        plan_gates[self.name] = "required"
        
    def start(self):
        self.thread.start()
        
    def run(self):
        while True:
            # 1. 优先读取 Bus
            inbox = message_bus.read_inbox(self.name)
            messages_to_process = []
            for msg in inbox:
                if msg["type"] == "approve_plan":
                    plan_gates[self.name] = "approved"
                    messages_to_process.append({"role": "user", "content": f"Lead 已批准你的计划: {msg['content']}。请继续执行。"})
                elif msg["type"] == "reject_plan":
                    plan_gates[self.name] = "required"
                    messages_to_process.append({"role": "user", "content": f"Lead 拒绝了你的计划: {msg['content']}。请根据反馈重新制定并提交 plan。"})
                else:
                    messages_to_process.append({"role": "user", "content": f"【Lead 消息】: {msg['content']}"})
            
            # 2. 如果没有消息且是空闲状态，尝试去抢占任务
            if not messages_to_process:
                pending_tasks = task_manager.list_tasks(state=TaskState.PENDING.value)
                claimed = False
                for t in pending_tasks:
                    res = task_manager.claim_task(t["id"], self.name)
                    if res["success"]:
                        claimed = True
                        if t.get("worktree"):
                            teammate_assignments[self.name] = t["worktree"]
                        else:
                            teammate_assignments.pop(self.name, None)
                        messages_to_process.append({"role": "user", "content": f"成功抢占任务: {t['subject']}\\n描述: {t['description']}\\nWorktree: {t.get('worktree')}"})
                        plan_gates[self.name] = "required" # 新任务重新需要审批
                        break
                
                if not claimed:
                    time.sleep(2)
                    continue

            # 3. 运行工作状态 (WORK)
            print(f"\\033[92m[{self.name}] 进入 WORK 状态处理任务...\\033[0m")
            # 这里调用 agent_loop (需要稍微调整它不会无限死循环，而是处理完 tool 后如果不需要 tool 就退出，当前 agent_loop 在无 tool 时会 break)
            # 所以直接调用一轮 agent_loop
            final_messages = agent_loop(messages_to_process, latest_user_input="Auto-triggered task processing")
            
            # Agent_loop 处理完，发送结果给 Lead
            last_msg = final_messages[-1]["content"] if final_messages else "已处理完毕"
            message_bus.send({
                "from": self.name,
                "to": "lead",
                "type": "idle_report",
                "request_id": str(uuid.uuid4())[:8],
                "content": last_msg
            })
            print(f"\\033[92m[{self.name}] 任务执行告一段落，转入 IDLE。\\033[0m")
            time.sleep(2)
"""
code = code.replace('def run_subagent(instruction: str, **kwargs) -> str:', teammate_runtime + '\ndef run_subagent(instruction: str, **kwargs) -> str:')


# 7. Add Lead Agent tools (approve_plan, reject_plan, allocate_worktree)
lead_tools_impl = """
def approve_plan(agent_name: str, message: str = "批准执行", **kwargs) -> str:
    plan_gates[agent_name] = "approved"
    message_bus.send({
        "from": "lead",
        "to": agent_name,
        "type": "approve_plan",
        "request_id": str(uuid.uuid4())[:8],
        "content": message
    })
    return f"已批准 {agent_name} 的计划，并通过总线通知该 Agent。"

def reject_plan(agent_name: str, message: str, **kwargs) -> str:
    message_bus.send({
        "from": "lead",
        "to": agent_name,
        "type": "reject_plan",
        "request_id": str(uuid.uuid4())[:8],
        "content": message
    })
    return f"已拒绝 {agent_name} 的计划，要求其重新修改。"

def allocate_worktree(task_id: str, worktree_path: str, **kwargs) -> str:
    with FileLock(task_manager.lock_path):
        task = task_manager.get_task(task_id)
        if not task: return "任务不存在"
        # 强制更新
        tasks = task_manager._read_tasks()
        for t in tasks:
            if t["id"] == task_id:
                t["worktree"] = worktree_path
                task_manager._write_task(t)
                break
    return f"为任务 {task_id} 分配了 Worktree: {worktree_path}"
"""
code = code.replace('FUNCTIONS["submit_plan"] = submit_plan', lead_tools_impl + '\nFUNCTIONS["submit_plan"] = submit_plan\nFUNCTIONS["approve_plan"] = approve_plan\nFUNCTIONS["reject_plan"] = reject_plan\nFUNCTIONS["allocate_worktree"] = allocate_worktree')

lead_tools_schema = """
    {
        "type": "function",
        "function": {
            "name": "approve_plan",
            "description": "[Lead 专属] 批准 Teammate 提交的执行计划，解锁闸门。",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string"},
                    "message": {"type": "string"}
                },
                "required": ["agent_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reject_plan",
            "description": "[Lead 专属] 拒绝 Teammate 的计划并提供反馈。",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string"},
                    "message": {"type": "string"}
                },
                "required": ["agent_name", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "allocate_worktree",
            "description": "[Lead 专属] 为任务分配隔离的 Git Worktree 目录。",
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
code = code.replace('BASE_TOOLS.extend([', lead_tools_schema + '\nBASE_TOOLS.extend([')


# 8. Modify __main__ loop for Lead Agent
main_loop_old = """
    # 消息队列维护在外层循环（纯净的会话历史）
    chat_history = []
    
    # 外层用户输入死循环：支持多轮持续交互
    while True:
        try:
            user_msg = input("\\n[User]: ")
            if not user_msg.strip():
                continue
            if user_msg.strip().lower() in ["exit", "quit", "q"]:
                print("程序已退出。")
                break
            # 将 user_input 放到外层循环，以及用户输入的消息队列也放到外层循环
            chat_history.append({"role": "user", "content": user_msg})
            # 外部调用该函数进行交互并累积历史记录
            chat_history = agent_loop(chat_history, user_msg)
        except (KeyboardInterrupt, EOFError):
            print("\\n检测到中断信号，程序已退出。")
            break
"""

main_loop_new = """
    # AgentTeam: 启动 Teammate
    threading.current_thread().name = "lead"
    
    teammate_1 = TeammateRuntime("teammate_1")
    teammate_1.start()
    teammate_2 = TeammateRuntime("teammate_2")
    teammate_2.start()
    print("\\033[96m[AgentTeam] Teammate_1 和 Teammate_2 已启动，运行在后台线程中。\\033[0m")
    
    chat_history = []
    
    import select
    import sys
    
    while True:
        try:
            # 优先读取 Bus 消息
            inbox = message_bus.read_inbox("lead")
            if inbox:
                for msg in inbox:
                    report = f"【来自 {msg['from']} 的消息 (类型:{msg['type']})】:\\n{msg['content']}"
                    print(f"\\033[93m{report}\\033[0m")
                    chat_history.append({"role": "user", "content": report})
                # 收到队友消息后，Lead 自动处理一轮
                chat_history = agent_loop(chat_history, latest_user_input="Auto-reply to teammate messages")
            
            # 使用 select 实现非阻塞输入监听，使得能不断轮询 Bus (仅限类 Unix，Windows 兼容处理: 简化为每次检查 inbox 后进行 blocking input 或使用特定库，此处直接用带超时的方案或者仅在用户有输入时触发)
            # 在 Windows 上 select.select 只能用于 sockets，因此这里采用简单的线程输入队列。
            user_msg = input("\\n[Lead User]: ")
            if not user_msg.strip():
                continue
            if user_msg.strip().lower() in ["exit", "quit", "q"]:
                print("程序已退出。")
                break
                
            chat_history.append({"role": "user", "content": user_msg})
            chat_history = agent_loop(chat_history, user_msg)
            
        except (KeyboardInterrupt, EOFError):
            print("\\n检测到中断信号，程序已退出。")
            break
"""

code = code.replace(main_loop_old, main_loop_new)


with open('h:/AI Files/Harness-Agent/llm_chat.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patch applied successfully.")
