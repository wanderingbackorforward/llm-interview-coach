#!/usr/bin/env python3
"""
stop_progress.py — Claude Code Stop Hook
每次 claude 完成一轮回答时触发：
1. 检查 progress.json 是否需要写回（知识点变化/刷题/模式变化）
2. 注入进度条提醒到 claude 输入框
"""

import json
import subprocess
import sys
import os
import re
from datetime import datetime

PROGRESS_FILE = os.environ.get("PROGRESS_FILE", "/root/llm-coach-v4/progress.json")
SESSION = os.environ.get("SESSION", "coach-v4")

def read_progress():
    try:
        with open(PROGRESS_FILE, encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def count_p0(p):
    """P0 知识点计数"""
    p0_keys = ["MCP协议", "Agent框架", "Multi-Agent", "Hybrid Search", "RRF融合", "Rerank", "BM25"]
    kp = p.get("知识点掌握", {})
    done = sum(1 for k in p0_keys if kp.get(k) == "✓")
    prog = sum(1 for k in p0_keys if kp.get(k) == "◐")
    return done, prog, len(p0_keys)

def count_p1(p):
    """P1 知识点计数"""
    p1_keys = ["Function Calling", "RAG项目", "RAGAS评估", "Agent记忆", "RAG vs 微调", "Chunk切割", "Embedding选型", "向量数据库", "稠密/稀疏向量"]
    kp = p.get("知识点掌握", {})
    done = sum(1 for k in p1_keys if kp.get(k) == "✓")
    prog = sum(1 for k in p1_keys if kp.get(k) == "◐")
    return done, prog, len(p1_keys)

def count_quiz(p):
    """题库进度"""
    qp = p.get("题库进度", {})
    total = sum(qp.get(cat, {}).get("已练", 0) for cat in qp)
    return total, 44

def get_progress_bar():
    p = read_progress()
    if not p:
        return "📊 进度文件未找到"

    p0_done, p0_prog, p0_total = count_p0(p)
    p1_done, p1_prog, p1_total = count_p1(p)
    quiz_done, quiz_total = count_quiz(p)

    project_intro = p.get("简历", {}).get("项目", [{}])[0].get("项目介绍状态", "未练")
    mock_count = len(p.get("模拟面试场次", []))
    current = p.get("中断点", {}).get("知识点", "?")

    return (
        f"📊 P0:✓{p0_done}/{p0_total} ◐{p0_prog} | "
        f"P1:✓{p1_done}/{p1_total} ◐{p1_prog} | "
        f"题库:{quiz_done}/{quiz_total} | "
        f"项目介绍:{project_intro} | "
        f"模拟:{mock_count}场 | "
        f"当前:{current}"
    )

def inject_message(msg):
    """通过 tmux send-keys 注入消息到 claude 输入框"""
    try:
        # 先清空输入框
        subprocess.run(["tmux", "send-keys", "-t", SESSION, "C-u"], 
                       capture_output=True, timeout=5)
        import time
        time.sleep(0.3)
        # 注入消息
        subprocess.run(["tmux", "send-keys", "-t", SESSION, msg], 
                       capture_output=True, timeout=5)
        time.sleep(0.3)
        # Enter 发送
        subprocess.run(["tmux", "send-keys", "-t", SESSION, "Enter"], 
                       capture_output=True, timeout=5)
        return True
    except Exception as e:
        print(f"[stop_progress] 注入失败: {e}", file=sys.stderr)
        return False

def check_needs_writeback(p):
    """检查是否需要提醒 claude 写回 progress.json"""
    # 检查最近对话摘要的时间
    summary = p.get("最近对话摘要", {})
    last_time = summary.get("时间", "")
    if last_time:
        try:
            last_dt = datetime.fromisoformat(last_time)
            if (datetime.now() - last_dt).total_seconds() > 600:  # 10分钟
                return True, "最近对话摘要超过10分钟未更新"
        except:
            pass
    return False, ""

def main():
    # 生成进度条
    bar = get_progress_bar()
    
    # 注入进度条提醒
    msg = f"【系统：请在回答开头补上进度条。格式：{bar}】"
    inject_message(msg)
    
    # 检查是否需要写回提醒
    p = read_progress()
    if p:
        needs_write, reason = check_needs_writeback(p)
        if needs_write:
            import time
            time.sleep(1)
            inject_message(f"【系统提醒：{reason}。请用 Write 工具更新 progress.json 的最近对话摘要和中断点。】")
    
    print(f"[stop_progress] 已注入进度条提醒", file=sys.stderr)

if __name__ == "__main__":
    main()
