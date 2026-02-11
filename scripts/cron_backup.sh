#!/bin/bash
# 系统级定时任务备份
# 当 OpenClaw cron 失败时使用

DATE=$(date +%Y-%m-%d)
WORKDIR="/root/.openclaw/workspace"
LOGFILE="/var/log/bowlwanpi-cron.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOGFILE
}

# 8:00 网易云日推
if [ "$(date +%H)" = "08" ]; then
    log "执行网易云日推..."
    python3 $WORKDIR/scripts/push_netease_music.py 2>&1 | tee -a $LOGFILE
fi

# 8:00 一分钟新闻
if [ "$(date +%H)" = "08" ] && [ "$(date +%M)" = "00" ]; then
    log "执行一分钟新闻..."
    python3 $WORKDIR/scripts/push_one_minute_news.py 2>&1 | tee -a $LOGFILE
fi

# 8:30 微博热搜
if [ "$(date +%H:%M)" = "08:30" ]; then
    log "执行微博热搜..."
    python3 $WORKDIR/scripts/push_weibo_hot.py 2>&1 | tee -a $LOGFILE
fi

# 8:30 早晨简报
if [ "$(date +%H:%M)" = "08:30" ]; then
    log "执行早晨简报..."
    python3 $WORKDIR/scripts/push_morning_brief.py 2>&1 | tee -a $LOGFILE
fi

# 9:00 Product Hunt
if [ "$(date +%H:%M)" = "09:00" ]; then
    log "执行 Product Hunt..."
    python3 $WORKDIR/scripts/push_producthunt.py 2>&1 | tee -a $LOGFILE
fi

log "检查完成"
