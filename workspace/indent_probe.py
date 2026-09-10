# -*- coding: utf-8 -*-
"""探测代码文件真实的缩进构成：每级缩进是 tab 还是空格、几个空格。"""
import os, re, sys

TARGETS = [
    r"H:\AI Files\Harness-Agent\llm_chat.py",
    r"H:\AI Files\Harness-Agent\hello.py",
    r"H:\AI Files\learn-claude-code\s07_skill_loading\code.py",
    r"H:\AI Files\learn-claude-code\s06_subagent\code.py",
    r"H:\AI Files\learn-claude-code\s05_todo_write\code.py",
    r"H:\AI Files\learn-claude-code\s06_subagent\example\string_tools.py",
    r"H:\AI Files\learn-claude-code\web\src\types\agent-data.ts",
    r"H:\AI Files\learn-claude-code\web\src\lib\utils.ts",
    r"H:\AI Files\learn-claude-code\web\src\lib\i18n-server.ts",
    r"H:\AI Files\Harness-Agent\example\demo_pkg\utils.py",
    r"H:\AI Files\Harness-Agent\example\demo_pkg\tests\test_utils.py",
    r"H:\AI Files\learn-claude-code\s09_memory\README.zh.md",
    r"H:\AI Files\learn-claude-code\agents\AGENTS_SUMMARY.md",
    r"H:\AI Files\learn-claude-code\SUMMARY.md",
]

def classify(path):
    try:
        with open(path, 'rb') as f:
            raw = f.read()
    except Exception as e:
        return f"{path}\n  读取失败: {e}"
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        text = raw.decode('gbk', errors='replace')
    lines = text.splitlines()

    # 统计“真正的缩进行”（忽略空行、纯注释、markdown 的列表/引用符）
    indent_chars = {'space': 0, 'tab': 0}
    levels = {}          # 每级缩进由什么构成 -> 出现次数
    breakdown = []       # 直接记录每个缩进串的 repr 与次数

    for ln in lines:
        if not ln.strip():
            continue
        stripped = ln.lstrip(' \t')
        if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
            continue
        lead = ln[:len(ln) - len(stripped)]
        if not lead:
            continue
        if '\t' in lead:
            indent_chars['tab'] += 1
        else:
            indent_chars['space'] += 1
        key = repr(lead)
        levels[key] = levels.get(key, 0) + 1

    # 推断“每级”的空格数：取最常见的空格缩进串，看它是否严格为 3/4 的倍数
    common = sorted(levels.items(), key=lambda kv: -kv[1])[:6]

    return (f"{path}\n"
            f"  文件总行数={len(lines)}, 缩进行: 空格={indent_chars['space']}, tab={indent_chars['tab']}\n"
            f"  前几种缩进串(次数): {common}")

def main():
    for t in TARGETS:
        if os.path.exists(t):
            print(classify(t))
        else:
            print(f"{t}\n  [不存在]")

if __name__ == '__main__':
    main()
