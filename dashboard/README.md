# 🥣 碗皮实时仪表盘

BowlWanpi 实时状态监控仪表盘

## 功能特性

- 📊 **系统资源监控** - CPU、内存、磁盘实时状态
- ⏰ **定时任务状态** - 所有定时任务健康度
- 🧠 **记忆系统** - 三记忆系统同步状态
- 🎮 **碗皮等级** - 当前等级、XP、连胜天数
- 🔄 **实时更新** - 每5秒自动刷新（SSE）
- 📱 **响应式设计** - 支持手机和桌面

## 启动方式

```bash
cd /root/.openclaw/workspace/dashboard
./start.sh
```

## 访问地址

- API: http://localhost:8080
- 仪表盘: http://localhost:8080/dashboard

## 技术栈

- Python Flask
- SSE (Server-Sent Events) 实时推送
- 纯前端 HTML/CSS/JS
- 暗黑主题 UI

## 创建时间

2026-02-13 - 困难任务挑战完成！
