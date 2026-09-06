import os
import json
import inspect
import subprocess
from dataclasses import dataclass, field
from dotenv import load_dotenv
from openai import OpenAI
import yaml
from pathlib import Path

# 加载 .env 文件中的环境变量
load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

# 初始化 OpenAI 兼容的客户端
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

class SkillLoader:
    def __init__(self):
        self.skills = {}

    def scan(self, path: Path):
        """扫描指定路径下的所有 skill"""
        if not path.exists() or not path.is_dir():
            return
        for skill_dir in path.iterdir():
            if skill_dir.is_dir():
                skill_md_path = skill_dir / "SKILL.md"
                if skill_md_path.exists():
                    self._parse_skill(skill_md_path)

    def _parse_skill(self, file_path: Path):
        try:
            content = file_path.read_text(encoding='utf-8')
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    metadata = yaml.safe_load(frontmatter)
                    name = metadata.get('name')
                    description = metadata.get('description', '')
                    if name:
                        self.skills[name] = {
                            "name": name,
                            "description": description,
                            "content": content
                        }
        except Exception as e:
            print(f"解析技能文件出错 {file_path}: {e}")

    def load_skill(self, skill_name: str) -> str:
        """加载指定技能的SKILL.md"""
        if skill_name in self.skills:
            return self.skills[skill_name]['content']
        return f"技能 {skill_name} 未找到。"

    def get_skill_prompt(self) -> str:
        """加载技能的提示词 (只包含name + description)"""
        if not self.skills:
            return ""
        prompt = "可用技能列表 (通过 load_skill 详细了解):\n"
        for name, info in self.skills.items():
            prompt += f"- {name}: {info['description'].strip()}\n"
        return prompt

SKILL_LOADER = SkillLoader()
SKILL_LOADER.scan(Path.cwd() / "skills")

def run_bash(command: str) -> str:
    try:
        # 运行命令，捕获输出
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            errors='replace', # 防止 Windows 下某些命令由于输出特殊字符导致解码报错
            timeout=60 # 防止某些命令卡死
        )
        
        # 优先返回标准输出，如果没有则返回标准错误
        output = result.stdout if result.stdout else result.stderr
        
        if not output.strip():
            output = "命令执行成功，无输出内容。"
        return output
    except Exception as e:
        return f"命令执行出错: {str(e)}"

def write_file(file_path: str, content: str) -> str:
    """用于创建新文件或完全重写（覆盖）已有文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"文件 {file_path} 写入/覆盖成功。"
    except Exception as e:
        return f"写入出错: {e}"

def read_file(file_path: str) -> str:
    """用于读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"读取出错: {e}"

def edit_file(file_path: str, old_text: str, new_text: str) -> str:
    """用于局部修改已有文件（替换特定文本）"""
    import os
    if not os.path.exists(file_path):
        return f"编辑失败：文件 {file_path} 不存在，请先使用 write_file 工具创建。"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()
        if old_text not in data:
            return f"编辑失败：在文件中未找到要替换的旧文本 '{old_text}'。"
        data = data.replace(old_text, new_text)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data)
        return f"文件 {file_path} 编辑成功：已完成局部替换。"
    except Exception as e:
        return f"编辑出错: {e}"

def glob_bash(pattern: str) -> str:
    """用于查找文件"""
    import glob
    try:
        results = glob.glob(pattern, recursive=True)
        if results:
            return "\n".join(results)
        return "未找到匹配的文件。"
    except Exception as e:
        return f"查找出错: {e}"

# --- 系统角色 Prompt 定义 ---
BASE_PROMPT = ""
skill_prompt = SKILL_LOADER.get_skill_prompt()
if skill_prompt:
    BASE_PROMPT += f"\n\n{skill_prompt}\n这些skill是可用的skill, 如果有相关的部分优先使用skill\n"

SYSTEM_PROMPT = "我是一名代码工程师, 擅长将复杂任务拆分为多个小任务按步骤依次执行, 使用 todo_write 去规划你的子任务步骤, 使用 task 派发 subagent 完成需求, 或者自己完成需求, 并更新状态" + BASE_PROMPT
SUBAGENT_SYSTEM_PROMPT = "你是一个子任务执行助手。完成指定派发下来的 task 并将答案返回上去" + BASE_PROMPT

# --- 阶段任务管理定义 ---
class TODOManager:
    """
    管理复杂任务的阶段步骤与执行状态。
    将任务划分为各个小阶段任务进行依次处理。
    """
    STATUS_FLAGS = {
        "pending": "[ ]",
        "in_progress": "[-]",
        "completed": "[x]"
    }

    def __init__(self):
        self.tasks = []

    def update(self, todos: list = None, **kwargs) -> str:
        """
        更新当前阶段分解的子任务信息，由 LLM 传递子任务状态。
        :param todos: 子任务列表，每个元素形如 {"task": "描述", "status": "pending|in_progress|completed"}
        :return: 格式化后的状态字符串或提示信息
        """
        # 4. 当小任务规划出来就只有一个或非列表时，提示 LLM
        if not isinstance(todos, list) or len(todos) <= 1:
            return "todo_write 传入的参数必须是一个列表"

        # 1. 分解的子任务不要超过20个
        if len(todos) > 20:
            return "分解的子任务不要超过20个"

        new_tasks = []
        for item in todos:
            if isinstance(item, dict):
                task = item.get("task", "未命名子任务")
                status = item.get("status")
                # tools 已限制 enum，直接精确匹配合法状态，否则默认 pending
                if status not in self.STATUS_FLAGS:
                    status = "pending"
                new_tasks.append({"task": task, "status": status})

        if len(new_tasks) <= 1:
            return "todo_write 传入的参数必须是一个列表"

        self.tasks = new_tasks
        # 2. update的最后直接调用log, 不要再todo_write来调用
        return f"阶段任务已更新，当前状态如下：\n{self.log()}"

    def log(self) -> str:
        """
        整合当前阶段每个子任务的状态，分别有 pending、in_progress、completed 分别对应一个不同的标志。
        :return: 格式化后的状态字符串
        """
        if not self.tasks:
            return "当前暂无分解的子任务。"
        lines = []
        for idx, item in enumerate(self.tasks, 1):
            flag = self.STATUS_FLAGS.get(item["status"], "[?]")
            lines.append(f"{flag} {idx}. {item['task']}")
        return "\n".join(lines)

# 全局 TODOManager 实例
todo_manager = TODOManager()

def todo_write(todos: list = None, **kwargs) -> str:
    """
    用于供 LLM 更新任务阶段列表与各子任务执行状态，内部调用 TODOManager.update
    """
    # 2. update的最后直接调用log, 不要再todo_write来调用
    return todo_manager.update(todos=todos, **kwargs)

# 定义供 LLM 调用的基础工具 Schema
BASE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": "执行本地系统 cmd 或 bash 命令并获取终端输出结果。例如用来查看文件、运行脚本等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "需要执行的终端命令"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "用于创建新文件，或将已有文件完全重写（全量覆盖）。注意：这会替换掉目标文件的所有原有内容！",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "要写入的完整新内容"}
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "用于读取文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "要读取的文件路径"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "用于对已有文件进行局部修改（打补丁）。通过精准匹配旧文本并替换为新文本来实现修改。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"},
                    "old_text": {"type": "string", "description": "文件中需要被替换的旧文本内容（必须完全一致）"},
                    "new_text": {"type": "string", "description": "替换成的新文本内容"}
                },
                "required": ["file_path", "old_text", "new_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "glob_bash",
            "description": "用于查找文件，支持匹配模式表达式（例如 **/*.py）",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "glob查找模式，如 src/**/*.py"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "todo_write",
            "description": "更新任务阶段列表与各步骤的执行状态。用于将复杂任务划分为各个小阶段并跟踪进度。",
            "parameters": {
                "type": "object",
                "properties": {
                    "todos": {
                        "type": "array",
                        "description": "阶段步骤列表，每个步骤包含任务描述(task)和状态(status: pending, in_progress, completed)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "task": {
                                    "type": "string",
                                    "description": "阶段步骤的任务描述"
                                },
                                "status": {
                                    "type": "string",
                                    "enum": ["pending", "in_progress", "completed"],
                                    "description": "当前步骤状态：pending(待处理)、in_progress(进行中)、completed(已完成)"
                                }
                            },
                            "required": ["task", "status"]
                        }
                    }
                },
                "required": ["todos"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "load_skill",
            "description": "加载指定技能的 SKILL.md 内容，获取技能的详细指南和约束。",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {"type": "string", "description": "技能名称"}
                },
                "required": ["skill_name"]
            }
        }
    }
]

task_schema = {
    "type": "function",
    "function": {
        "name": "task",
        "description": "派发子任务给 subagent 执行。适用于独立或复杂的子需求。",
        "parameters": {
            "type": "object",
            "properties": {
                "instruction": {"type": "string", "description": "派发给子代理的具体需求指令"}
            },
            "required": ["instruction"]
        }
    }
}

# 专门给 subagent 使用的工具集合
SUB_TOOLS = list(BASE_TOOLS)

# 供父级 Agent 调用的完整工具集合（包含派发子代理的 task 工具）
TOOLS = BASE_TOOLS + [task_schema]

def task(instruction: str, **kwargs) -> str:
    """创建一个子执行代理完成子任务"""
    # run_subagent 将在稍后定义，此处做个占位或直接调用
    return run_subagent(instruction)

# 基础的函数映射（供 subagent 使用，无 task 工具）
BASE_FUNCTIONS = {
    "run_bash": run_bash,
    "write_file": write_file,
    "read_file": read_file,
    "edit_file": edit_file,
    "glob_bash": glob_bash,
    "todo_write": todo_write,
    "load_skill": SKILL_LOADER.load_skill
}

# 专门给 subagent 使用的函数集合
SUB_FUNCTIONS = dict(BASE_FUNCTIONS)

# 完整的函数映射（供父级使用，包含 task 工具）
FUNCTIONS = dict(BASE_FUNCTIONS)
FUNCTIONS["task"] = task


# --- 结构化工具调用定义 ---
@dataclass
class ToolCall:
    """
    结构化工具调用对象：将 LLM 原始调用反序列化为规整的结构
    """
    id: str
    name: str
    args: dict = field(default_factory=dict)
    result: str = ""

    @classmethod
    def from_raw(cls, raw_tool_call) -> "ToolCall":
        """从 LLM 返回的原始 tool_call 中反序列化构建结构化实例"""
        try:
            parsed_args = json.loads(raw_tool_call.function.arguments)
        except Exception:
            parsed_args = {}
        return cls(
            id=raw_tool_call.id,
            name=raw_tool_call.function.name,
            args=parsed_args
        )

# --- HOOK 流程定义 ---
# HOOK 表：类似于函数表索引函数，通过阶段名索引指定一系列 HOOK 函数（以列表形式存储）
hook_table = {
    "before_loop": [],       # a. 用户输入后没进工具死循环前
    "before_tool": [],       # b. 每次循环执行工具前
    "after_tool": [],        # c. 每次循环执行工具后 (打印结果、记录工具使用次数等)
    "after_loop": []         # d. 退出循环停止时
}

# 工具使用统计记录器
tool_usage_stats = {
    "count": 0,
    "tools": {}
}

def register_hook(stage: str, hook_func: callable) -> None:
    """
    向指定阶段注册 HOOK 函数。
    :param stage: 阶段名 ('before_loop', 'before_tool', 'after_tool', 'after_loop')
    :param hook_func: 要注册的函数对象
    """
    if stage not in hook_table:
        hook_table[stage] = []
    if hook_func not in hook_table[stage]:
        hook_table[stage].append(hook_func)

def unregister_hook(stage: str, hook_func: callable) -> bool:
    """
    从指定阶段注销（反注册）已注册的 HOOK 函数。
    :param stage: 阶段名 ('before_loop', 'before_tool', 'after_tool', 'after_loop')
    :param hook_func: 要移除的函数对象
    :return: 移除成功返回 True，不存在则返回 False
    """
    if stage in hook_table and hook_func in hook_table[stage]:
        hook_table[stage].remove(hook_func)
        return True
    return False

# 阶段 a 的 Hook: 重置工具统计
def hook_reset_tool_stats(**kwargs):
    """阶段 a: 每轮交互开始前重置工具调用统计数据"""
    tool_usage_stats["count"] = 0
    tool_usage_stats["tools"].clear()

# 阶段 a 的 Hook: 打印玩家输入的日志
def hook_log_user_input(user_input: str, messages: list = None, **kwargs):
    """阶段 a: 打印玩家输入的日志"""
    print(f"\033[94m[HOOK: before_loop] 记录用户输入: {user_input}\033[0m")

# 需要用户确认的文件操作工具集合（精确匹配工具名称，避免字符串模糊检索）
FILE_SENSITIVE_TOOLS = {"write_file", "edit_file", "read_file"}

# run_bash 高危命令关键词（命中直接拦截）
BASH_FORBIDDEN_KEYWORDS = ['format ', 'rm -rf /', 'mkfs', 'del /f /s /q c:\\', 'rmdir /s /q c:\\']

# run_bash 敏感命令关键词（需用户确认）
BASH_SENSITIVE_KEYWORDS = ['rm ', 'del ', 'rmdir', 'erase', 'move ', 'mv ', 'rename', 'ren ', 'remove-item']

# 阶段 b 的 Hook: 接收结构化 ToolCall，进行权限校验与高危拦截
def hook_check_tool_permission(tool: ToolCall, **kwargs) -> tuple[bool, str]:
    """阶段 b: 执行工具前的权限判断与高危拦截"""
    args_str = str(tool.args)
    if len(args_str) > 200:
        args_str = args_str[:200] + "..."
    print(f"\033[94m[HOOK: before_tool] 开始工具权限校验 -> {tool.name} | 操作信息: {args_str}\033[0m")
    
    # 1. 针对 run_bash 命令内容进行高危拦截与敏感操作确认
    if tool.name == "run_bash":
        cmd_str = str(tool.args.get("command", "")).lower()
        if any(danger in cmd_str for danger in BASH_FORBIDDEN_KEYWORDS):
            return False, "执行失败：系统已拦截高危操作（如格式化磁盘、删除系统核心文件等）。"
            
        if any(kw in cmd_str for kw in BASH_SENSITIVE_KEYWORDS):
            user_approval = input(f"\033[36m命令 '{cmd_str}' 请求执行。是否允许？(yes/no): \033[0m").strip().lower()
            if user_approval != "yes":
                return False, "用户不允许执行该操作。"
        return True, ""

    # 2. 针对文件读写/修改类敏感工具，通过工具名称集合直接判断，无需检索字符串
    if tool.name in FILE_SENSITIVE_TOOLS:
        user_approval = input(f"\033[36m工具 {tool.name} 请求执行。是否允许？(yes/no): \033[0m").strip().lower()
        if user_approval != "yes":
            return False, "用户不允许执行该操作。"
        return True, ""

    # 3. 其余安全工具（如 glob_bash, todo_write 等）直接放行
    return True, ""

# 阶段 b 的 Hook: 记录 AI 决定执行的工具，并隐藏参数
def hook_log_tool_intent(tool: ToolCall, **kwargs):
    """阶段 b: 打印 AI 决定执行的工具（不显示参数）"""
    print(f"\033[33m[调用工具] AI 决定执行: {tool.name}\033[0m")

# 阶段 c 的 Hook: 接收结构化 ToolCall，工具执行完毕后的操作
def hook_log_tool_result(tool: ToolCall, **kwargs):
    """阶段 c: 工具执行完毕后的钩子（保留 todo_write 的日志，移除其余工具的执行完毕日志）"""
    if tool.name == "todo_write":
        preview_result = tool.result if len(tool.result) < 300 else tool.result[:300] + " ...[内容太长已截断]"
        print(f"\033[90m[HOOK: after_tool] 工具 {tool.name} 执行完成 | 结果:\n{preview_result}\033[0m")

# 阶段 c 的 Hook: 通过 after_tool 记录工具的使用次数，而不是在 loop 中进行记录
def hook_record_tool_use(tool: ToolCall, **kwargs):
    """通过 after_tool 的 hook 记录工具使用次数，而不是在 loop 中记录"""
    tool_usage_stats["count"] += 1
    tool_usage_stats["tools"][tool.name] = tool_usage_stats["tools"].get(tool.name, 0) + 1

# 阶段 d 的 Hook: 记录好了后在 after_loop 时进行打印
def hook_log_final_output_and_stats(final_content: str, messages: list = None, **kwargs):
    """阶段 d: 在 after_loop 时打印最终输出的内容日志以及使用工具的总数"""
    total_count = tool_usage_stats["count"]
    print(f"\033[94m[HOOK: after_loop] 本轮交互结束，共调用工具 {total_count} 次\033[0m")
    if final_content:
        print(f"\n[LLM]:\n{final_content}")

# 通过普通调用写法进行注册（按阶段注册功能性 Hook 函数）
register_hook("before_loop", hook_reset_tool_stats)
register_hook("before_loop", hook_log_user_input)
register_hook("before_tool", hook_log_tool_intent)
register_hook("before_tool", hook_check_tool_permission)
register_hook("after_tool", hook_log_tool_result)
register_hook("after_tool", hook_record_tool_use)
register_hook("after_loop", hook_log_final_output_and_stats)

# 单独封装处理 HOOK 的执行函数
def trigger_hooks(stage: str, **kwargs) -> list:
    """
    HOOK 处理函数：从 hook_table 索引指定阶段并顺序执行其注册的 HOOK 列表，并返回各 HOOK 的返回值列表
    """
    hook_funcs = hook_table.get(stage, [])
    results = []
    for hook in hook_funcs:
        try:
            sig = inspect.signature(hook)
            if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in sig.parameters.values()):
                res = hook(**kwargs)
            else:
                filtered_args = {k: v for k, v in kwargs.items() if k in sig.parameters}
                res = hook(**filtered_args)
            if res is not None:
                results.append(res)
        except Exception as e:
            print(f"\033[31m[HOOK 执行异常] 阶段 {stage} 函数 {getattr(hook, '__name__', str(hook))} 失败: {e}\033[0m")
    return results

def execute_function(tool: ToolCall, available_funcs: dict, messages: list) -> str:
    """执行单个工具调用并处理权限校验和错误捕获"""
    func_to_call = available_funcs.get(tool.name)
    if not func_to_call:
        return f"未找到名为 {tool.name} 的工具，无法执行。"
    
    # 触发 before_tool 钩子
    hook_results = trigger_hooks("before_tool", tool=tool, messages=messages)
    
    is_allowed = True
    deny_msg = ""
    for res in hook_results:
        if isinstance(res, tuple) and len(res) == 2 and isinstance(res[0], bool):
            is_allowed, deny_msg = res
            if not is_allowed:
                break
    
    if is_allowed:
        try:
            result = str(func_to_call(**tool.args))
        except Exception as e:
            result = f"工具 {tool.name} 执行出错: {str(e)}"
    else:
        result = deny_msg
        
    tool.result = result
    # 触发 after_tool 钩子
    trigger_hooks("after_tool", tool=tool, messages=messages)
    return result

def handle_tool_call(raw_tool_call, available_funcs: dict, messages: list) -> bool:
    """
    处理单个工具调用并将其结果附加到消息队列中
    返回本次是否调用了 todo_write
    """
    tool = ToolCall.from_raw(raw_tool_call)
    
    result = execute_function(tool, available_funcs, messages)
    
    called_todo = False
    if tool.name == "todo_write" and "执行出错" not in result and "不允许执行" not in result:
        called_todo = True
        
    messages.append({
        "role": "tool",
        "tool_call_id": tool.id,
        "name": tool.name,
        "content": tool.result
    })
    return called_todo

def run_subagent(instruction: str, **kwargs) -> str:
    """
    执行一个子代理任务，最多执行30轮
    """
    print(f"\033[92m[Subagent Start] 开始执行子任务: {instruction}\033[0m")
    messages = [
        {"role": "system", "content": SUBAGENT_SYSTEM_PROMPT},
        {"role": "user", "content": instruction}
    ]
    
    # 共享钩子
    trigger_hooks("before_loop", user_input=instruction, messages=messages)
    
    final_content = ""
    for _ in range(30):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=SUB_TOOLS,
                tool_choice="auto"
            )
        except Exception as e:
            final_content = f"请求 LLM 时出错: {e}"
            break
            
        message = response.choices[0].message
        messages.append(message)
        
        if not message.tool_calls:
            final_content = message.content or ""
            break
            
        for raw_tool_call in message.tool_calls:
            handle_tool_call(raw_tool_call, SUB_FUNCTIONS, messages)
    else:
        final_content = "【系统提示】子代理执行已达30轮最大上限，自动终止。"
        
    trigger_hooks("after_loop", messages=messages, final_content=final_content)
    print(f"\033[92m[Subagent End] 子任务执行完毕。\033[0m")
    return final_content

def agent_loop(messages: list = None) -> list:
    """
    供外部调用的核心函数，用于处理模型调用与工具循环。
    :param messages: 对话消息队列（在外层循环中维护并追加用户消息）
    """
    if messages is None:
        messages = []

    # 提取最近一条用户输入用于 Hook 日志记录
    latest_user_input = ""
    for m in reversed(messages):
        if isinstance(m, dict) and m.get("role") == "user":
            latest_user_input = m.get("content", "")
            break

    # a. 用户输入后没进工具死循环前 (通过 hook 打印玩家输入日志等)
    trigger_hooks("before_loop", user_input=latest_user_input, messages=messages)

    final_content = ""
    # 4. 在 agent 主循环中通过一个变量记录没调用 todo_write 的次数
    no_todo_count = 0

    # 1. 该函数内部是一个死循环，专门处理可能连续调用的工具流程
    while True:
        try:
            # 直接在 client.chat.completions.create 里面拼接传入系统角色提示词
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                tools=TOOLS,
                tool_choice="auto"
            )
        except Exception as e:
            print(f"请求 LLM 时出错: {e}")
            break
            
        message = response.choices[0].message
        
        # 将 LLM 的回复记录到上下文中（包括它发出的 tool_calls 信息）
        messages.append(message)

        # 2. 判断：如果没有调用工具，则记录最后回复内容并停止循环
        if not message.tool_calls:
            final_content = message.content or ""
            break

        # 3. 使用封装的 handle_tool_call 函数执行工具
        called_todo = False
        for raw_tool_call in message.tool_calls:
            if handle_tool_call(raw_tool_call, FUNCTIONS, messages):
                called_todo = True

        # 4. 在 agent 主循环中通过一个变量记录没调用 todo_write 的次数
        no_todo_count = 0 if called_todo else no_todo_count + 1

        # 当大于等于3次的时候需要加一段话到content中给LLM提示需要更新阶段步骤了
        if no_todo_count >= 3:
            tip_msg = "\n\n【系统提示】你已连续 3 次及以上未更新任务阶段步骤，请调用 todo_write 工具更新当前分解的子任务状态与进展。"
            if messages and messages[-1].get("role") == "tool":
                messages[-1]["content"] += tip_msg
                
    # 2. 记录好了后在after_loop时进行打印
    trigger_hooks("after_loop", messages=messages, final_content=final_content)
    return messages

if __name__ == "__main__":
    print("=== LLM 终端助手已启动 (输入 exit 或 quit 退出) ===")
    print("已加载配置 URL:", BASE_URL)
    
    # 消息队列维护在外层循环（纯净的会话历史）
    chat_history = []
    
    # 外层用户输入死循环：支持多轮持续交互
    while True:
        try:
            user_msg = input("\n[User]: ")
            if not user_msg.strip():
                continue
            if user_msg.strip().lower() in ["exit", "quit", "q"]:
                print("程序已退出。")
                break
            # 将 user_input 放到外层循环，以及用户输入的消息队列也放到外层循环
            chat_history.append({"role": "user", "content": user_msg})
            # 外部调用该函数进行交互并累积历史记录
            chat_history = agent_loop(chat_history)
        except (KeyboardInterrupt, EOFError):
            print("\n检测到中断信号，程序已退出。")
            break
