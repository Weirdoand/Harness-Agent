import os
import json
import subprocess
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

def check_tool_permission(func_name: str, args: dict) -> tuple[bool, str]:
    """
    在执行工具函数前进行权限判断。只返回是否允许执行的布尔值及拦截信息。
    1. 拦截高危命令
    2. 对读写文件类工具以及敏感终端指令进行用户授权确认
    """
    args_str = json.dumps(args, ensure_ascii=False).lower()
    
    # a. 高危命令集合：禁止常见格式化磁盘、删除系统核心文件等
    forbidden_keywords = ['format ', 'rm -rf /', 'mkfs', 'del /f /s /q c:\\', 'rmdir /s /q c:\\']
    if any(danger in args_str for danger in forbidden_keywords):
        print("\033[31m[系统拦截] 检测到高危操作，已拒绝执行。\033[0m")
        return False, "执行失败：系统已拦截高危操作（如格式化磁盘、删除系统核心文件等）。"
        
    # 需要询问用户的集合（包含 edit, write, read 以及 run_bash 中的文件修改/删除等敏感指令）
    ask_keywords = ['edit', 'write', 'read', 'rm ', 'del ', 'rmdir', 'erase', 'move ', 'mv ', 'rename', 'ren ', 'remove-item']
    
    # b. 规则匹配: 函数名和 cmd 内容同时判断
    cmd_str = str(args.get("command", "")).lower()
    check_target = f"{func_name} {cmd_str}"
    
    if any(kw in check_target for kw in ask_keywords):
        # c. 用户审批, 询问用户获取权限 "yes/no"
        user_approval = input(f"\033[36m工具 {func_name} 请求执行。是否允许？(yes/no): \033[0m").strip().lower()
        if user_approval == "yes":
            return True, ""
        else:
            print("\033[33m[用户拒绝] 没获取到权限，已跳过该工具执行。\033[0m")
            return False, "用户不允许执行该操作。"
            
    # 其他工具直接允许
    return True, ""
def chat_with_llm(user_input: str, messages: list = None) -> list:
    """
    供外部调用的核心函数，用于处理用户输入并与 LLM 进行交流。
    """
    if messages is None:
        messages = []
        
    # 将用户的输入添加到消息列表中
    messages.append({"role": "user", "content": user_input})

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

        # 2. 判断：如果没有调用工具，则停止循环（正常回复）
        if not message.tool_calls:
            print(f"\n[LLM]:\n{message.content}")
            break

        # 3. 当存在调用工具时，执行该工具并将结果塞入 Content 中，等待下次循环发送
        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            func_to_call = available_functions.get(func_name)
            
            if func_to_call:
                # 解析 LLM 传过来的工具参数，将其解包作为 kwargs 传入对应的函数
                try:
                    args = json.loads(tool_call.function.arguments)
                    # 打印黄色字体的工具调用信息（带参数）
                    print(f"\033[33m[工具调用] AI 决定执行: {func_name} | 参数: {args}\033[0m")
                    
                    is_allowed, deny_msg = check_tool_permission(func_name, args)
                    if is_allowed:
                        tool_result = str(func_to_call(**args))
                    else:
                        tool_result = deny_msg
                    
                    # 在终端也打印一下工具的返回结果（使用灰色，并限制长度防刷屏）
                    preview_result = tool_result if len(tool_result) < 300 else tool_result[:300] + " ...[内容太长已截断]"
                    print(f"\033[90m  └─ [工具返回]: {preview_result}\033[0m")
                except Exception as e:
                    tool_result = f"工具 {func_name} 执行出错: {str(e)}"
            else:
                tool_result = f"未找到名为 {func_name} 的工具，无法执行。"
                
            # 将工具执行结果作为 'tool' 角色返回给 LLM
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": tool_result
            })
                
    return messages

if __name__ == "__main__":
    print("=== LLM 终端助手已启动 ===")
    print("已加载配置 URL:", BASE_URL)
    
    chat_history = []
    
    # 单次调用代码：移除了外层的无限循环
    user_msg = input("\n[User]: ")
    if user_msg.strip():
        # 外部调用该函数
        chat_history = chat_with_llm(user_msg, chat_history)
