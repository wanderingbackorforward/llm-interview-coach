#!/usr/bin/env python3
"""
coach_watcher_v4.py — Python 版 Watcher（替代 bash coach-watcher.sh）
功能：
1. 皇帝耐心倒计时（tmux 状态栏）
2. 进度条缺失检测 + 兜底注入
3. 空闲检测 + 批判注入（最多3次，间隔15分钟）
"""

import subprocess
import time
import sys
import os
import json
import re
from datetime import datetime

PROGRESS_FILE = "/root/llm-coach-v4/progress.json"
SESSIONS = ["coach-v4"]
IDLE_LIMIT = 600
WARN1_AT = 480
WARN2_AT = 540
CRITIQUE_INTERVAL = 900
MAX_CRITIQUES = 3
POLL_INTERVAL = 3

class SessionState:
    def __init__(self, name):
        self.name = name
        self.last_hash = ""
        self.last_active = time.time()
        self.state = 0  # 0=正常, 1=警告1, 2=警告2, 3=批判
        self.last_critique = 0
        self.critique_count = 0
        self.missing_bar_count = 0

def get_pane_hash(session):
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", session, "-p"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split('\n')
        last5 = '\n'.join(lines[-5:]) if lines else ""
        return hash(last5)
    except:
        return ""

def get_pane_content(session, lines=500):
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", session, "-p", "-S", f"-{lines}"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout
    except:
        return ""

def has_progress_bar(content):
    return bool(re.search(r'📊 P0:✓\d+/\d+', content))

def is_waiting_for_input(content):
    lines = content.strip().split('\n')
    if not lines:
        return False
    last = lines[-1].strip()
    return last.startswith('❯') or last.startswith('>')

def update_status_bar(session, idle):
    remain = IDLE_LIMIT - idle
    if remain <= 0:
        timer_text, color = "⛔", "red"
    elif remain <= 60:
        timer_text = f"🔴{remain//60:02d}:{remain%60:02d}"
        color = "red"
    elif remain <= 180:
        timer_text = f"🟡{remain//60:02d}:{remain%60:02d}"
        color = "yellow"
    else:
        timer_text = f"🟢{remain//60:02d}:{remain%60:02d}"
        color = "green"
    
    try:
        subprocess.run(["tmux", "set", "-t", session, "status", "on"], 
                       capture_output=True, timeout=3)
        subprocess.run(["tmux", "set", "-t", session, "status-right-length", "20"], 
                       capture_output=True, timeout=3)
        subprocess.run(["tmux", "set", "-t", session, "status-left", ""], 
                       capture_output=True, timeout=3)
        subprocess.run(["tmux", "set", "-t", session, "status-right", 
                       f"#[fg={color},bold]⏱{timer_text}"], 
                       capture_output=True, timeout=3)
    except:
        pass

def inject_message(session, msg):
    try:
        subprocess.run(["tmux", "send-keys", "-t", session, "C-u"], 
                       capture_output=True, timeout=5)
        time.sleep(0.3)
        subprocess.run(["tmux", "send-keys", "-t", session, msg], 
                       capture_output=True, timeout=5)
        time.sleep(0.3)
        subprocess.run(["tmux", "send-keys", "-t", session, "Enter"], 
                       capture_output=True, timeout=5)
    except Exception as e:
        print(f"[watcher] 注入失败: {e}", file=sys.stderr)

def get_progress_bar_text():
    try:
        with open(PROGRESS_FILE, encoding='utf-8') as f:
            p = json.load(f)
        p0_keys = ["MCP协议", "Agent框架", "Multi-Agent", "Hybrid Search", "RRF融合", "Rerank", "BM25"]
        p1_keys = ["Function Calling", "RAG项目", "RAGAS评估", "Agent记忆", "RAG vs 微调", "Chunk切割", "Embedding选型", "向量数据库", "稠密/稀疏向量"]
        kp = p.get("知识点掌握", {})
        p0d = sum(1 for k in p0_keys if kp.get(k) == "✓")
        p0p = sum(1 for k in p0_keys if kp.get(k) == "◐")
        p1d = sum(1 for k in p1_keys if kp.get(k) == "✓")
        p1p = sum(1 for k in p1_keys if kp.get(k) == "◐")
        qp = p.get("题库进度", {})
        qt = sum(qp.get(c, {}).get("已练", 0) for c in qp)
        pi = p.get("简历", {}).get("项目", [{}])[0].get("项目介绍状态", "未练")
        mc = len(p.get("模拟面试场次", []))
        cur = p.get("中断点", {}).get("知识点", "?")
        return f"📊 P0:✓{p0d}/7 ◐{p0p} | P1:✓{p1d}/9 ◐{p1p} | 题库:{qt}/44 | 项目介绍:{pi} | 模拟:{mc}场 | 当前:{cur}"
    except:
        return "📊 进度文件读取失败"

def main():
    print(f"[watcher v4] 启动，监控 sessions: {SESSIONS}", file=sys.stderr)
    
    states = {s: SessionState(s) for s in SESSIONS}
    
    while True:
        now = time.time()
        for s_name, state in states.items():
            if not subprocess.run(["tmux", "has-session", "-t", s_name], 
                                  capture_output=True).returncode == 0:
                continue
            
            current_hash = get_pane_hash(s_name)
            
            if current_hash != state.last_hash:
                state.last_active = now
                state.last_hash = current_hash
                if state.state != 0:
                    state.state = 0
                    state.missing_bar_count = 0
            
            idle = int(now - state.last_active)
            if idle < 0 or idle > 86400:
                idle = 0
            
            update_status_bar(s_name, idle)
            
            # 进度条缺失检测（仅当 claude 在等待输入时）
            if idle < 30 and state.state == 0:
                content = get_pane_content(s_name, 200)
                if is_waiting_for_input(content) and not has_progress_bar(content):
                    state.missing_bar_count += 1
                    if state.missing_bar_count >= 2:
                        # 连续2轮缺进度条，直接粘贴
                        bar = get_progress_bar_text()
                        inject_message(s_name, f"【系统：进度条缺失，补上 → {bar}】")
                        state.missing_bar_count = 0
                else:
                    state.missing_bar_count = 0
            
            # 8分钟警告
            if idle >= WARN1_AT and state.state < 1:
                remain = IDLE_LIMIT - idle
                subprocess.run(["tmux", "display-message", "-t", s_name, "-d", "5000",
                               f"⚠️ 皇帝注意到你离开了… 还剩 {remain} 秒。"], 
                              capture_output=True, timeout=5)
                state.state = 1
            
            # 9分钟紧急
            if idle >= WARN2_AT and state.state < 2:
                remain = IDLE_LIMIT - idle
                subprocess.run(["tmux", "display-message", "-t", s_name, "-d", "5000",
                               f"⏱️ 皇帝耐心即将耗尽！剩余 {remain} 秒！"], 
                              capture_output=True, timeout=5)
                state.state = 2
            
            # 10分钟批判
            if idle >= IDLE_LIMIT and state.critique_count < MAX_CRITIQUES:
                last_crit = state.last_critique
                if state.state < 3 or (now - last_crit) >= CRITIQUE_INTERVAL:
                    minutes = idle // 60
                    num = state.critique_count + 1
                    is_last = num >= MAX_CRITIQUES
                    
                    if is_last:
                        msg = f"【系统检测：用户已离开 {minutes} 分钟（第{num}次/共{MAX_CRITIQUES}次，最后一次）。请以马可·奥勒留皇帝本人严厉批判，换一个新角度。之后不再注入。】"
                    else:
                        msg = f"【系统检测：用户已离开 {minutes} 分钟（第{num}次/共{MAX_CRITIQUES}次）。请以马可·奥勒留皇帝本人严厉批判。不要重复上次内容。】"
                    
                    inject_message(s_name, msg)
                    state.state = 3
                    state.last_critique = now
                    state.critique_count = num
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
