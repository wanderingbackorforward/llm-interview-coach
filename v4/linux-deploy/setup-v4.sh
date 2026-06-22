#!/bin/bash
# setup-v4.sh — 一键部署 v4 系统
# 用法: bash setup-v4.sh

set -e

V4_DIR="/root/llm-coach-v4"
V3_DIR="/root/llm-coach"

echo "=== 1. 创建目录 ==="
mkdir -p "$V4_DIR/.claude/hooks"
mkdir -p "$V4_DIR/.claude/skills/llm-interview-coach"
mkdir -p "$V4_DIR/.claude/skills/llm-interview-coach/references"
mkdir -p "$V4_DIR/watcher/logs"
mkdir -p "$V4_DIR/linux-deploy"

echo "=== 2. 复制 v3 文件到 v4 ==="
# SKILL.md 和 references 从本地 Windows 同步（scp 会处理）
# 这里先从 v3 复制作为基础
cp -r "$V3_DIR/.claude/skills/llm-interview-coach/"* "$V4_DIR/.claude/skills/llm-interview-coach/" 2>/dev/null || true
cp "$V3_DIR/progress.json" "$V4_DIR/progress.json" 2>/dev/null || true

echo "=== 3. 复制 v4 特有文件 ==="
cp /tmp/v4-deploy/settings.json "$V4_DIR/.claude/settings.json"
cp /tmp/v4-deploy/hooks/*.py "$V4_DIR/.claude/hooks/"
cp /tmp/v4-deploy/watcher/*.py "$V4_DIR/watcher/"
chmod +x "$V4_DIR/.claude/hooks/"*.py
chmod +x "$V4_DIR/watcher/"*.py
cp /tmp/v4-deploy/linux-deploy/*.service /etc/systemd/system/

echo "=== 4. 启动 watcher ==="
systemctl daemon-reload
systemctl enable coach-watcher-v4
systemctl start coach-watcher-v4
sleep 2
systemctl is-active coach-watcher-v4

echo "=== 5. 创建 tmux session ==="
tmux new -d -s coach-v4 -x 200 -y 50 "cd /root/llm-coach-v4 && claude --allowedTools Bash,Read,Write,Edit,Skill,WebSearch,WebFetch" 2>&1 || true
sleep 2

echo "=== 6. 配置 ttyd (端口 7682) ==="
# 检查是否已有 ttyd 在 7682
if lsof -i :7682 >/dev/null 2>&1; then
    echo "端口 7682 已被占用，跳过 ttyd 启动"
else
    nohup ttyd -p 7682 -t coach-v4 -W > /tmp/ttyd-v4.log 2>&1 &
    echo "ttyd 已启动: http://0.0.0.0:7682"
fi

echo "=== 7. 配置 nginx ==="
if [ -f /etc/nginx/sites-enabled/smartinfracloud.top ]; then
    # 检查是否已有 /coach-v4/ location
    if ! grep -q "coach-v4" /etc/nginx/sites-enabled/smartinfracloud.top; then
        # 在 coach2 location 后添加 coach-v4
        sed -i '/location \/coach2\//a\\
    location /coach-v4/ {\n        proxy_pass http://127.0.0.1:7682/;\n        proxy_http_version 1.1;\n        proxy_set_header Upgrade \$http_upgrade;\n        proxy_set_header Connection \"upgrade\";\n        proxy_set_header Host \$host;\n    }' /etc/nginx/sites-enabled/smartinfracloud.top
        nginx -t && nginx -s reload
        echo "nginx 已配置: https://smartinfracloud.top/coach-v4/"
    else
        echo "nginx 已有 /coach-v4/ 配置"
    fi
fi

echo "=== 完成 ==="
echo "旧系统: https://smartinfracloud.top/coach/ (继续运行)"
echo "新系统: https://smartinfracloud.top/coach-v4/ (v4)"
