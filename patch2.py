import re

with open('h:/AI Files/Harness-Agent/llm_chat.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update SYSTEM_PROMPT
new_system_prompt = '''
SYSTEM_PROMPT = """身份: 你是一个代码 Agent (Lead)。请直接执行工具，不要过度解释。
工具: 可用工具包括 bash, read_file, write_file, edit_file, glob_bash, create_task, assign_dependencies, list_tasks, get_task, claim_task, complete_task, spawn_teammate, list_teammates, send_message, request_shutdown, approve_plan, reject_plan, create_worktree 等。
任务: 请首先创建所有的任务节点。只有在 create_task 返回运行时生成的 ID 之后，才能使用这些确切的 ID 调用 assign_dependencies 添加依赖关系。只有 Lead 可以更改任务依赖关系。
团队: 当并行工作有助于完成任务时，请首先提议一个职责明确的小型团队，并等待用户的确认审批。在用户确认之前，绝对不要调用 spawn_teammate。确认后，通过为每个并行更改创建一个 Task 来委托独立的工作。分配准备好的工作时，将 task_id 传递给 spawn_teammate，然后只有当单独的工作目录可以防止编辑冲突时，才调用 create_worktree 创建绑定到任务的隔离环境。Teammate 必须完成当前任务才能认领另一个任务。Worktree 仅仅改变工具的默认工作目录 (cwd)；它不是沙盒。生成 teammate 之后，请结束当前的对话回合，不要轮询其状态；运行时会传递团队事件并唤醒 Lead。请对这些事件做出反应，并在协作完成后关闭队友 (request_shutdown)。
工作区: 当前工作目录是当前目录。
""" + BASE_PROMPT
'''

# Replace the old SYSTEM_PROMPT
text = re.sub(r'SYSTEM_PROMPT = ".*? \+ BASE_PROMPT', new_system_prompt.strip(), text, flags=re.DOTALL)


# 2. Add spawn_teammate, list_teammates, request_shutdown, create_worktree tools
tools_impl = """
active_teammates = {}

def spawn_teammate(agent_name: str, task_id: str = None, **kwargs) -> str:
    if agent_name in active_teammates:
        return f"队友 {agent_name} 已存在运行中。"
    t = TeammateRuntime(agent_name)
    active_teammates[agent_name] = t
    t.start()
    
    if task_id:
        res = task_manager.claim_task(task_id, agent_name)
        if res["success"]:
            t.messages.append({"role": "user", "content": f"Lead 指定你认领任务: {task_id}"})
    return f"成功启动队友 {agent_name}。"

def list_teammates(**kwargs) -> str:
    if not active_teammates:
        return "当前没有活跃的队友。"
    return "活跃队友: " + ", ".join(active_teammates.keys())

def request_shutdown(agent_name: str, **kwargs) -> str:
    if agent_name in active_teammates:
        t = active_teammates.pop(agent_name)
        t.stop_flag = True
        return f"已请求关闭队友 {agent_name}。"
    return f"未找到队友 {agent_name}。"

def send_message(to: str, message: str, **kwargs) -> str:
    message_bus.send({
        "from": "lead",
        "to": to,
        "type": "chat",
        "request_id": "msg",
        "content": message
    })
    return f"已发送消息给 {to}。"

def create_worktree(task_id: str, worktree_path: str, **kwargs) -> str:
    return allocate_worktree(task_id, worktree_path)

FUNCTIONS["spawn_teammate"] = spawn_teammate
FUNCTIONS["list_teammates"] = list_teammates
FUNCTIONS["request_shutdown"] = request_shutdown
FUNCTIONS["send_message"] = send_message
FUNCTIONS["create_worktree"] = create_worktree

"""

# Insert these new functions after allocate_worktree
text = text.replace('FUNCTIONS["allocate_worktree"] = allocate_worktree', 'FUNCTIONS["allocate_worktree"] = allocate_worktree\n' + tools_impl)

new_schemas = """
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

text = text.replace('BASE_TOOLS.extend([', 'BASE_TOOLS.extend([\n' + new_schemas)

# 3. Update TeammateRuntime to support stop_flag
teammate_init_old = """class TeammateRuntime:
    def __init__(self, name: str):
        self.name = name
        self.thread = threading.Thread(target=self.run, name=self.name, daemon=True)
        self.system_prompt = SUBAGENT_SYSTEM_PROMPT + "\\n你是执行 Agent，可以通过 task 抢占任务。当没有指令时请进入 IDLE，被拦截时使用 submit_plan。"
        plan_gates[self.name] = "required"
"""
teammate_init_new = """class TeammateRuntime:
    def __init__(self, name: str):
        self.name = name
        self.thread = threading.Thread(target=self.run, name=self.name, daemon=True)
        self.system_prompt = SUBAGENT_SYSTEM_PROMPT + "\\n你是执行 Agent，可以通过 task 抢占任务。当没有指令时请进入 IDLE，被拦截时使用 submit_plan。"
        self.messages = []
        self.stop_flag = False
        plan_gates[self.name] = "required"
"""
text = text.replace(teammate_init_old, teammate_init_new)

teammate_run_old = "def run(self):\\n        while True:"
teammate_run_new = "def run(self):\\n        while not self.stop_flag:"
text = text.replace(teammate_run_old, teammate_run_new)

# 4. Remove automatic teammate spawn in __main__
main_old = """
    # AgentTeam: 启动 Teammate
    threading.current_thread().name = "lead"
    
    teammate_1 = TeammateRuntime("teammate_1")
    teammate_1.start()
    teammate_2 = TeammateRuntime("teammate_2")
    teammate_2.start()
    print("\\033[96m[AgentTeam] Teammate_1 和 Teammate_2 已启动，运行在后台线程中。\\033[0m")
"""
main_new = """
    # AgentTeam: 启动 Lead
    threading.current_thread().name = "lead"
    print("\\033[96m[AgentTeam] Lead 已启动。\\033[0m")
"""
text = text.replace(main_old, main_new)


with open('h:/AI Files/Harness-Agent/llm_chat.py', 'w', encoding='utf-8') as f:
    f.write(text)

