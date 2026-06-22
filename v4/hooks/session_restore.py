#!/usr/bin/env python3
"""
session_restore.py — Claude Code SessionStart Hook
新会话启动时自动读取 progress.json 的最近对话摘要，恢复上下文。
输出到 stdout，Claude Code 会将其注入为系统上下文。
"""

import json
import sys
import os

PROGRESS_FILE = os.environ.get("PROGRESS_FILE", "/root/llm-coach-v4/progress.json")

def main():
    try:
        with open(PROGRESS_FILE, encoding='utf-8') as f:
            p = json.load(f)
    except:
        print("[session_restore] progress.json 未找到，跳过上下文恢复", file=sys.stderr)
        return
    
    summary = p.get("最近对话摘要", {})
    if not summary or not summary.get("下次第一件事"):
        print("[session_restore] 无对话摘要，跳过", file=sys.stderr)
        return
    
    # 输出恢复上下文（stdout 会被 Claude Code 注入）
    last_topic = summary.get("最后讲的知识点", "未知")
    last_exercise = summary.get("最后出的小练习", "无")
    user_last = summary.get("用户最后回答", "无")
    next_action = summary.get("下次第一件事", "继续上次的内容")
    recent = summary.get("最近3轮互动", [])
    
    output = f"""【上下文恢复】上次会话摘要：
- 最后讲的知识点：{last_topic}
- 最后出的小练习：{last_exercise}
- 用户最后回答：{user_last}
- 最近互动：{' → '.join(recent[-3:]) if recent else '无'}

新会话第一件事：{next_action}
不要说"我忘了之前的内容"——用上面的摘要直接续上。"""
    
    print(output)
    print(f"[session_restore] 已恢复上下文", file=sys.stderr)

if __name__ == "__main__":
    main()
