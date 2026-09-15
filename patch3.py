with open('h:/AI Files/Harness-Agent/llm_chat.py', 'r', encoding='utf-8') as f:
    text = f.read()

if 'def run(self):\n        while True:' in text:
    text = text.replace('def run(self):\n        while True:', 'def run(self):\n        while getattr(self, "stop_flag", False) == False:')

main_old = """    # AgentTeam: 启动 Teammate
    threading.current_thread().name = "lead"
    
    teammate_1 = TeammateRuntime("teammate_1")
    teammate_1.start()
    teammate_2 = TeammateRuntime("teammate_2")
    teammate_2.start()
    print("\\033[96m[AgentTeam] Teammate_1 和 Teammate_2 已启动，运行在后台线程中。\\033[0m")"""

main_new = """    # AgentTeam: 启动 Lead
    threading.current_thread().name = "lead"
    print("\\033[96m[AgentTeam] Lead 已启动。\\033[0m")"""

text = text.replace(main_old, main_new)

with open('h:/AI Files/Harness-Agent/llm_chat.py', 'w', encoding='utf-8') as f:
    f.write(text)
