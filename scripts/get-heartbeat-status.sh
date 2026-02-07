#!/bin/bash
# 解析心跳日志，生成状态报告

LOG_FILE="/var/log/bowlwanpi-heartbeat.log"

tail -20 "$LOG_FILE" 2>/dev/null | grep -E "(Gateway|Mihomo|CPU:|Memory:|Disk:|Load:)" | tail -6
