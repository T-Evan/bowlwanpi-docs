#!/bin/bash
# 火山引擎 API 认证环境变量
# 使用方法: source ~/.openclaw/workspace/skills/volcengine-fusion-search/env.sh

# AK/SK 认证方式
export VOLCENGINE_ACCESS_KEY_ID="AKLTOGM0YTE2NDEwNzAzNDQ3YTg3M2E2YmNkN2EzMGVlNDI"
export VOLCENGINE_SECRET_ACCESS_KEY="OTIxNTZmNWUxZWMzNGY5MDk3YjJmZjRiNGI1OTUzYjA"

echo "✅ 火山引擎 AK/SK 已加载"
echo "   AK: ${VOLCENGINE_ACCESS_KEY_ID:0:12}..."
