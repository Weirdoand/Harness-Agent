import os
import json
import inspect
import subprocess
from dataclasses import dataclass, field
from dotenv import load_dotenv
from openai import OpenAI

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

# 定义供 LLM 调用的工具 Schema
tools = [
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
    }
]

# 用于将工具名 (name) 映射到对应 Python 函数对象 (function) 的字典
available_functions = {
    "run_bash": run_bash,
    "write_file": write_file,
    "read_file": read_file,
    "edit_file": edit_file,
    "glob_bash": glob_bash
}

def get_tool_function(func_name: str):
    """
    根据工具名称从可用工具函数映射表中获取对应的函数对象。
    :param func_name: 工具名称
    :return: 对应的函数对象，若未找到则返回 None
    """
    return available_functions.get(func_name)

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
    "after_tool": [],        # c. 每次循环执行工具后
    "after_loop": []         # d. 退出循环停止时
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

# 阶段 a 的 Hook: 打印玩家输入的日志
def hook_log_user_input(user_input: str, messages: list, **kwargs):
    """阶段 a: 打印玩家输入的日志"""
    print(f"\033[94m[HOOK: before_loop] 记录用户输入: {user_input}\033[0m")

# 阶段 b 的 Hook: 接收结构化 ToolCall，进行权限校验与高危拦截
def hook_check_tool_permission(tool: ToolCall, **kwargs) -> tuple[bool, str]:
    """阶段 b: 执行工具前的权限判断与高危拦截"""
    print(f"\033[94m[HOOK: before_tool] 开始工具权限校验 -> {tool.name}\033[0m")
    args_str = json.dumps(tool.args, ensure_ascii=False).lower()
    
    # 高危命令集合：禁止常见格式化磁盘、删除系统核心文件等
    forbidden_keywords = ['format ', 'rm -rf /', 'mkfs', 'del /f /s /q c:\\', 'rmdir /s /q c:\\']
    if any(danger in args_str for danger in forbidden_keywords):
        print("\033[31m[系统拦截] 检测到高危操作，已拒绝执行。\033[0m")
        return False, "执行失败：系统已拦截高危操作（如格式化磁盘、删除系统核心文件等）。"
        
    # 需要询问用户的集合（包含 edit, write, read 以及 run_bash 中的文件修改/删除等敏感指令）
    ask_keywords = ['edit', 'write', 'read', 'rm ', 'del ', 'rmdir', 'erase', 'move ', 'mv ', 'rename', 'ren ', 'remove-item']
    
    # 规则匹配: 函数名和 cmd 内容同时判断
    cmd_str = str(tool.args.get("command", "")).lower()
    check_target = f"{tool.name} {cmd_str}"
    
    if any(kw in check_target for kw in ask_keywords):
        user_approval = input(f"\033[36m工具 {tool.name} 请求执行。是否允许？(yes/no): \033[0m").strip().lower()
        if user_approval == "yes":
            return True, ""
        else:
            print("\033[33m[用户拒绝] 没获取到权限，已跳过该工具执行。\033[0m")
            return False, "用户不允许执行该操作。"
            
    return True, ""

# 阶段 c 的 Hook: 接收结构化 ToolCall，打印执行结果日志
def hook_log_tool_result(tool: ToolCall, **kwargs):
    """阶段 c: 打印工具执行返回结果的日志"""
    print(f"\033[94m[HOOK: after_tool] 工具 {tool.name} 执行完成\033[0m")
    preview_result = tool.result if len(tool.result) < 300 else tool.result[:300] + " ...[内容太长已截断]"

# 阶段 d 的 Hook: 打印最终输出的内容日志以及使用工具的总数统计
def hook_log_final_output_and_stats(final_content: str, tool_count: int, messages: list, **kwargs):
    """阶段 d: 打印最终输出的内容日志以及使用工具的总数"""
    print(f"\033[94m[HOOK: after_loop] 本轮交互结束，共调用工具 {tool_count} 次\033[0m")
    if final_content:
        print(f"\n[LLM]:\n{final_content}")

# 通过普通调用写法进行注册（按阶段注册功能性 Hook 函数）
register_hook("before_loop", hook_log_user_input)
register_hook("before_tool", hook_check_tool_permission)
register_hook("after_tool", hook_log_tool_result)
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

def chat_with_llm(user_input: str, messages: list = None) -> list:
    """
    供外部调用的核心函数，用于处理用户输入并与 LLM 进行交流。
    """
    if messages is None:
        messages = []
        
    # 将用户的输入添加到消息列表中
    messages.append({"role": "user", "content": user_input})

    # a. 用户输入后没进工具死循环前 (通过 hook 打印玩家输入日志等)
    trigger_hooks("before_loop", user_input=user_input, messages=messages)

    tool_count = 0
    final_content = ""

    # 1. 该函数内部是一个死循环，专门处理可能连续调用的工具流程
    while True:
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
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

        # 3. 当存在调用工具时，执行该工具并将结果塞入 Content 中，等待下次循环发送
        for raw_tool_call in message.tool_calls:
            # 将原始工具调用反序列化为规整的结构化对象
            tool = ToolCall.from_raw(raw_tool_call)
            func_to_call = get_tool_function(tool.name)
            
            if func_to_call:
                # b. 每次循环执行工具前 (将结构化的 tool 传递给 hook)
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
                        tool_count += 1
                        tool.result = str(func_to_call(**tool.args))
                    except Exception as e:
                        tool.result = f"工具 {tool.name} 执行出错: {str(e)}"
                else:
                    tool.result = deny_msg
                
                # c. 每次循环执行工具后 (将带结果的结构化 tool 传递给 hook)
                trigger_hooks("after_tool", tool=tool, messages=messages)
            else:
                tool.result = f"未找到名为 {tool.name} 的工具，无法执行。"
                
            # 将工具执行结果作为 'tool' 角色返回给 LLM
            messages.append({
                "role": "tool",
                "tool_call_id": tool.id,
                "name": tool.name,
                "content": tool.result
            })
                
    # d. 退出循环停止时 (通过 hook 打印最后输出的内容日志以及使用工具的总数)
    trigger_hooks("after_loop", messages=messages, final_content=final_content, tool_count=tool_count)
    return messages

if __name__ == "__main__":
    print("=== LLM 终端助手已启动 (输入 exit 或 quit 退出) ===")
    print("已加载配置 URL:", BASE_URL)
    
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
            # 外部调用该函数进行交互并累积历史记录
            chat_history = chat_with_llm(user_msg, chat_history)
        except (KeyboardInterrupt, EOFError):
            print("\n检测到中断信号，程序已退出。")
            break
