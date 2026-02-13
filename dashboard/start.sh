#!/bin/bash
# 碗皮仪表盘启动脚本

echo "🥣 启动 BowlWanpi 仪表盘..."
echo ""

# 检查依赖
echo "📦 检查依赖..."
pip3 show flask flask-cors psutil >/dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "⚙️  安装依赖..."
    pip3 install flask flask-cors psutil -q
fi

# 进入目录
cd /root/.openclaw/workspace/dashboard

# 启动服务
echo "🚀 启动服务..."
echo "   地址: http://localhost:8080"
echo "   仪表盘: http://localhost:8080/dashboard"
echo ""
echo "💡 按 Ctrl+C 停止"
echo ""

python3 app.py
