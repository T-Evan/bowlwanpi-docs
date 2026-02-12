#!/usr/bin/env python3
"""
测试正确的 memU API 路径
"""
import json
import requests

with open('/root/.openclaw/workspace/secrets/memu-credentials.json', 'r') as f:
    creds = json.load(f)
    API_KEY = creds.get('api_key', '')

BASE_URL = "https://api.memu.so"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 测试不同路径
PATHS = [
    "/v1/memorize",
    "/api/v1/memorize", 
    "/memorize",
    "/api/memorize",
    "/v1/memory",
    "/api/memory",
]

print("🧠 寻找正确的 API 路径...")
print(f"Base URL: {BASE_URL}")
print("-" * 50)

payload = {
    "conversation": [
        {"role": "user", "content": "测试消息"},
        {"role": "assistant", "content": "测试回复"}
    ],
    "user_id": "yiwan",
    "agent_id": "bowlwanpi"
}

for path in PATHS:
    url = f"{BASE_URL}{path}"
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} POST {path}: {response.status_code}")
        if response.status_code == 200:
            print(f"   🎉 找到正确路径: {path}")
            print(f"   响应: {response.text[:200]}")
        else:
            print(f"   响应: {response.text[:100]}")
    except Exception as e:
        print(f"❌ POST {path}: {type(e).__name__}")

# 同时测试 GET 路径
print("\n" + "-" * 50)
print("🔍 测试 GET 路径...")
GET_PATHS = ["/v1/health", "/api/v1/health", "/health", "/api/health", "/"]
for path in GET_PATHS:
    url = f"{BASE_URL}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} GET {path}: {response.status_code}")
        print(f"   响应: {response.text[:150]}")
    except Exception as e:
        print(f"❌ GET {path}: {type(e).__name__}")
