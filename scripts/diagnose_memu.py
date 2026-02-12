#!/usr/bin/env python3
"""
memU 连接诊断脚本
测试 API 端点、SSL 证书、认证
"""
import json
import requests
import socket
import ssl
import sys

# 加载凭证
with open('/root/.openclaw/workspace/secrets/memu-credentials.json', 'r') as f:
    creds = json.load(f)
    API_KEY = creds.get('api_key', '')

# 可能的端点列表
ENDPOINTS = [
    "https://api.memu.so/v1",      # 原端点
    "https://api.memu.pro/v1",      # 当前代码中的端点
    "https://api.memtensor.cn/v1",  # 可能的国内镜像
    "https://memu.memtensor.cn/v1", # 另一种可能
]

print("=" * 60)
print("🧠 memU 连接诊断")
print("=" * 60)
print(f"API Key (前20位): {API_KEY[:20]}...")
print()

# 测试每个端点
for endpoint in ENDPOINTS:
    print(f"\n🔍 测试端点: {endpoint}")
    print("-" * 40)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 测试1: 基础连通性 (GET)
    try:
        response = requests.get(
            f"{endpoint}/health",
            headers=headers,
            timeout=10,
            verify=True
        )
        print(f"  ✅ GET /health: {response.status_code}")
        print(f"     响应: {response.text[:100]}")
    except requests.exceptions.SSLError as e:
        print(f"  ❌ SSL 错误: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"  ❌ 连接错误: {e}")
    except Exception as e:
        print(f"  ❌ 其他错误: {type(e).__name__}: {e}")
    
    # 测试2: 存储记忆 (POST)
    try:
        payload = {
            "conversation": [
                {"role": "user", "content": "诊断测试消息"},
                {"role": "assistant", "content": "诊断测试回复"}
            ],
            "user_id": "yiwan",
            "agent_id": "bowlwanpi"
        }
        response = requests.post(
            f"{endpoint}/memorize",
            headers=headers,
            json=payload,
            timeout=10,
            verify=True
        )
        print(f"  ✅ POST /memorize: {response.status_code}")
        print(f"     响应: {response.text[:200]}")
        if response.status_code == 200:
            print(f"  🎉 此端点可用！")
            WORKING_ENDPOINT = endpoint
    except requests.exceptions.SSLError as e:
        print(f"  ❌ SSL 错误: {str(e)[:100]}")
    except requests.exceptions.ConnectionError as e:
        print(f"  ❌ 连接错误: {str(e)[:100]}")
    except Exception as e:
        print(f"  ❌ 其他错误: {type(e).__name__}: {str(e)[:100]}")

print("\n" + "=" * 60)
print("🔧 建议修复方案")
print("=" * 60)

# 检查证书问题
print("\n1. 证书检查:")
try:
    hostname = "api.memu.so"
    context = ssl.create_default_context()
    with socket.create_connection((hostname, 443), timeout=5) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()
            print(f"   ✅ {hostname} 证书有效")
            print(f"   有效期: {cert.get('notBefore')} ~ {cert.get('notAfter')}")
except Exception as e:
    print(f"   ❌ {hostname} 证书问题: {e}")

print("\n2. 代理检查:")
# 检查代理
try:
    proxy_response = requests.get(
        "https://www.google.com",
        proxies={"https": "http://127.0.0.1:7890"},
        timeout=5
    )
    print(f"   ✅ 代理可用 (127.0.0.1:7890)")
except:
    print(f"   ⚠️  代理可能不可用")

print("\n" + "=" * 60)
