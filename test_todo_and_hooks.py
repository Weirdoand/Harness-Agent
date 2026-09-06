import io
import sys
from unittest.mock import patch
from llm_chat import (
    SYSTEM_PROMPT,
    TODOManager,
    todo_manager,
    todo_write,
    ToolCall,
    trigger_hooks,
    tool_usage_stats,
    agent_loop
)

def test_todo_manager():
    print("--- 1. 测试 TODOManager ---")
    mgr = TODOManager()
    
    # 初始状态
    assert mgr.log() == "当前暂无分解的子任务。"
    
    # 4. 当小任务规划出来就只有一个或非列表时，提示 LLM todo_write 传入的参数必须是一个列表
    single_todo = [{"task": "单一任务", "status": "pending"}]
    assert mgr.update(single_todo) == "todo_write 传入的参数必须是一个列表"
    assert mgr.update({"task": "非列表单一任务", "status": "pending"}) == "todo_write 传入的参数必须是一个列表"
    assert mgr.update([]) == "todo_write 传入的参数必须是一个列表"
    
    # 1. 超过 20 个子任务测试：直接返回给 LLM "分解的子任务不要超过20个"
    too_many_todos = [{"task": f"子任务{i}", "status": "pending"} for i in range(21)]
    captured_stdout = io.StringIO()
    sys.stdout = captured_stdout
    try:
        ret_msg = mgr.update(too_many_todos)
    finally:
        sys.stdout = sys.__stdout__
    assert ret_msg == "分解的子任务不要超过20个"
    assert captured_stdout.getvalue() == ""  # 确保不向控制台打印
    
    # 正常多个子任务更新测试（update 最后直接调用 log 并返回格式化结果）
    todos = [
        {"task": "分析问题", "status": "completed"},
        {"task": "编写代码", "status": "in_progress"},
        {"task": "测试验证", "status": "pending"}
    ]
    res_update = mgr.update(todos)
    print("TODOManager update 输出：\n" + res_update)
    
    # 2. update 最后直接调用 log 返回当前状态
    assert "[x] 1. 分析问题" in res_update
    assert "[-] 2. 编写代码" in res_update
    assert "[ ] 3. 测试验证" in res_update
    assert res_update == f"阶段任务已更新，当前状态如下：\n{mgr.log()}"
    
    # 非法 enum 状态兜底测试
    mgr.update([{"task": "合法步骤", "status": "completed"}, {"task": "非法状态步骤", "status": "unknown"}])
    log_output2 = mgr.log()
    assert "[x] 1. 合法步骤" in log_output2
    assert "[ ] 2. 非法状态步骤" in log_output2
    
    # 测试 todo_write 全局函数直接返回 update 结果
    res = todo_write(todos=[{"task": "任务A", "status": "in_progress"}, {"task": "任务B", "status": "pending"}])
    assert "阶段任务已更新" in res
    assert "[-] 1. 任务A" in todo_manager.log()
    
    res_overflow = todo_write(todos=too_many_todos)
    assert res_overflow == "分解的子任务不要超过20个"
    
    res_single = todo_write(todos=single_todo)
    assert res_single == "todo_write 传入的参数必须是一个列表"
    
    print("TODOManager 测试通过！\n")

def test_after_tool_hook_counting():
    print("--- 2. 测试 after_tool hook 计数与 after_loop 打印 ---")
    # 触发 before_loop 重置计数
    trigger_hooks("before_loop", user_input="测试输入")
    assert tool_usage_stats["count"] == 0
    
    # 模拟工具调用后触发 after_tool
    tc1 = ToolCall(id="call_1", name="run_bash", args={"command": "dir"})
    tc2 = ToolCall(id="call_2", name="read_file", args={"file_path": "test.txt"})
    
    trigger_hooks("after_tool", tool=tc1)
    assert tool_usage_stats["count"] == 1
    assert tool_usage_stats["tools"]["run_bash"] == 1
    
    trigger_hooks("after_tool", tool=tc2)
    assert tool_usage_stats["count"] == 2
    assert tool_usage_stats["tools"]["read_file"] == 1
    
    # 测试 after_loop 打印
    captured_stdout = io.StringIO()
    sys.stdout = captured_stdout
    try:
        trigger_hooks("after_loop", final_content="测试完成")
    finally:
        sys.stdout = sys.__stdout__
        
    output = captured_stdout.getvalue()
    print("after_loop 捕获输出:\n" + output)
    assert "本轮交互结束，共调用工具 2 次" in output
    print("after_tool Hook 计数与 after_loop 打印测试通过！\n")

class FakeToolCallFunc:
    def __init__(self, name, args):
        self.name = name
        self.arguments = args

class FakeToolCall:
    def __init__(self, call_id, name, args):
        self.id = call_id
        self.function = FakeToolCallFunc(name, args)

class FakeChoiceMessage:
    def __init__(self, tool_calls=None, content=None):
        self.tool_calls = tool_calls or []
        self.content = content
        self.role = "assistant"

class FakeChoice:
    def __init__(self, message):
        self.message = message

class FakeResponse:
    def __init__(self, choice_msg):
        self.choices = [FakeChoice(choice_msg)]

def test_agent_loop_no_todo_warning():
    print("--- 3. 测试 agent_loop 中未调用 todo_write 达到3次时的提示注入与清零 ---")

    # 构造5轮响应:
    # 轮次 1: glob_bash
    # 轮次 2: glob_bash
    # 轮次 3: glob_bash (此处 no_todo_count 达到 3，应注入提示)
    # 轮次 4: todo_write (执行 todo_write，no_todo_count 应被清零为 0)
    # 轮次 5: 最终回答文本 (停止循环)
    responses = [
        FakeResponse(FakeChoiceMessage(
            tool_calls=[FakeToolCall("call_1", "glob_bash", '{"pattern": "*.txt"}')]
        )),
        FakeResponse(FakeChoiceMessage(
            tool_calls=[FakeToolCall("call_2", "glob_bash", '{"pattern": "*.py"}')]
        )),
        FakeResponse(FakeChoiceMessage(
            tool_calls=[FakeToolCall("call_3", "glob_bash", '{"pattern": "*.md"}')]
        )),
        FakeResponse(FakeChoiceMessage(
            tool_calls=[FakeToolCall(
                "call_4", 
                "todo_write", 
                '{"todos": [{"task": "已完成全部扫描", "status": "completed"}, {"task": "汇总扫描结果", "status": "in_progress"}]}'
            )]
        )),
        FakeResponse(FakeChoiceMessage(
            tool_calls=[],
            content="任务全部完成！"
        )),
    ]
    
    with patch("llm_chat.client.chat.completions.create", side_effect=responses) as mock_create:
        from llm_chat import agent_loop, SYSTEM_PROMPT
        # 验证外层循环维护消息队列（纯净的用户与助手对话历史）
        chat_history = []
        user_msg = "开始批量搜索并规划任务"
        chat_history.append({"role": "user", "content": user_msg})
        messages = agent_loop(chat_history)
        
        # 3. 验证在 client.chat.completions.create 中直接放入包含 system 提示词的列表
        first_call_messages = mock_create.call_args_list[0].kwargs["messages"]
        assert first_call_messages[0]["role"] == "system"
        assert "我是一名代码工程师" in first_call_messages[0]["content"]
        assert "todo_write" in first_call_messages[0]["content"]
        assert first_call_messages[1]["role"] == "user"
        assert first_call_messages[1]["content"] == user_msg
        
        # 验证在第3次工具执行后（即 call_3 的 tool message 中）被注入了系统提示
        call_3_msg = next(m for m in messages if isinstance(m, dict) and m.get("tool_call_id") == "call_3")
        print("第 3 次工具响应 content:\n", call_3_msg["content"])
        assert "【系统提示】你已连续 3 次及以上未更新任务阶段步骤" in call_3_msg["content"]
        
        # 验证在第 1、2 次工具消息中没有提示
        call_1_msg = next(m for m in messages if isinstance(m, dict) and m.get("tool_call_id") == "call_1")
        call_2_msg = next(m for m in messages if isinstance(m, dict) and m.get("tool_call_id") == "call_2")
        assert "【系统提示】" not in call_1_msg["content"]
        assert "【系统提示】" not in call_2_msg["content"]
        
        # 验证第4次调用 todo_write 成功更新
        call_4_msg = next(m for m in messages if isinstance(m, dict) and m.get("tool_call_id") == "call_4")
        print("第 4 次 (todo_write) 工具响应 content:\n", call_4_msg["content"])
        assert "[x] 1. 已完成全部扫描" in call_4_msg["content"]
        assert "[-] 2. 汇总扫描结果" in call_4_msg["content"]
        # 执行 todo_write 后计数清零，第 4 次 tool 消息不应有未更新警告
        assert "【系统提示】" not in call_4_msg["content"]
        
        # 验证工具总调用次数通过 after_tool 记录为 4 次
        assert tool_usage_stats["count"] == 4
        print(f"统计工具调用总次数: {tool_usage_stats['count']} (期望: 4)")
        
def test_run_subagent():
    print("--- 4. 测试 run_subagent ---")
    trigger_hooks("before_loop", user_input="reset")
    tool_usage_stats["count"] = 0
    
    responses = [
        FakeResponse(FakeChoiceMessage(
            tool_calls=[FakeToolCall("call_s1", "glob_bash", '{"pattern": "*.md"}')]
        )),
        FakeResponse(FakeChoiceMessage(
            tool_calls=[],
            content="子代理任务完成"
        ))
    ]
    with patch("llm_chat.client.chat.completions.create", side_effect=responses) as mock_create:
        from llm_chat import run_subagent, SUBAGENT_SYSTEM_PROMPT
        result = run_subagent("请查找 markdown 文件")
        
        # 验证提示词和返回结果
        first_call_messages = mock_create.call_args_list[0].kwargs["messages"]
        assert first_call_messages[0]["content"] == SUBAGENT_SYSTEM_PROMPT
        assert result == "子代理任务完成"
        
        # 验证钩子记录了调用
        assert tool_usage_stats["count"] == 1

if __name__ == "__main__":
    test_todo_manager()
    test_after_tool_hook_counting()
    test_agent_loop_no_todo_warning()
    test_run_subagent()
    print("ALL TESTS PASSED SUCCESSFULLY! 所有测试均顺利通过！")
