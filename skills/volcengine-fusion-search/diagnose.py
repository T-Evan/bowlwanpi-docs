#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断火山引擎 API 连接问题
测试多种接入方式找出正确的配置
"""

import os
import sys
import json
import urllib.request
import urllib.error


def test_api(endpoint: str, payload: dict, headers: dict, desc: str, timeout: int = 30):
    """测试 API 调用"""
    print(f"\n{'='*60}")
    print(f"测试: {desc}")
    print(f"端点: {endpoint}")
    print(f"{'='*60}")
    
    try:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
        
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"✅ 成功! HTTP {resp.status}")
            if "choices" in result:
                content = result["choices"][0].get("message", {}).get("content", "")[:200]
                print(f"回复: {content}...")
            return True, result
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 错误 {e.code}")
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            print(f"错误详情:\n{json.dumps(error_json, indent=2, ensure_ascii=False)}")
        except:
            print(f"错误详情: {error_body[:500]}")
        return False, None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False, None


def main():
    api_key = os.environ.get("VOLCENGINE_API_KEY")
    if not api_key:
        print("错误: 未设置 VOLCENGINE_API_KEY 环境变量")
        print("请执行: export VOLCENGINE_API_KEY='your-key'")
        sys.exit(1)
    
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print("开始诊断...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 测试用查询
    test_query = "今天天气怎么样"
    
    # 测试模式列表
    tests = [
        # 模式1: 使用模型名直接调用
        {
            "endpoint": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
            "payload": {
                "model": "doubao-1.5-pro-32k-250115",
                "messages": [{"role": "user", "content": test_query}],
                "stream": False
            },
            "desc": "方舟平台 - 直接模型调用"
        },
        # 模式2: 使用模型名 + 搜索提示
        {
            "endpoint": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
            "payload": {
                "model": "doubao-1.5-pro-32k-250115",
                "messages": [
                    {"role": "system", "content": "请使用搜索工具获取最新信息回答问题。"},
                    {"role": "user", "content": test_query}
                ],
                "stream": False
            },
            "desc": "方舟平台 - 带搜索提示"
        },
        # 模式3: Bots 端点
        {
            "endpoint": "https://ark.cn-beijing.volces.com/api/v3/bots/chat/completions",
            "payload": {
                "model": "doubao-1.5-pro-32k-250115",
                "messages": [{"role": "user", "content": test_query}],
                "stream": False
            },
            "desc": "方舟平台 - Bots 端点"
        },
        # 模式4: 尝试使用融合搜索特定端点（猜测）
        {
            "endpoint": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
            "payload": {
                "model": "doubao-1.5-pro-32k-250115",
                "messages": [{"role": "user", "content": test_query}],
                "stream": False,
                "tools": [{"type": "web_search", "web_search": {}}]
            },
            "desc": "方舟平台 - 显式启用搜索工具（猜测）"
        }
    ]
    
    results = []
    for test in tests:
        success, _ = test_api(test["endpoint"], test["payload"], headers, test["desc"])
        results.append((test["desc"], success))
    
    # 总结
    print(f"\n{'='*60}")
    print("诊断总结")
    print(f"{'='*60}")
    for desc, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status}: {desc}")
    
    print("\n" + "="*60)
    print("解决方案")
    print("="*60)
    
    if not any(r[1] for r in results):
        print("""
所有测试都失败了，可能的原因：

1. API Key 不是方舟平台的 Key
   - 火山引擎不同服务使用不同的 Key
   - 请访问 https://console.volcengine.com/ark/ 
   - 在「API Key 管理」中创建新的 Key

2. 需要使用 Endpoint ID
   - 在方舟控制台创建在线推理 Endpoint
   - 获取 Endpoint ID (格式: ep-xxxxxxxx)
   - 使用 --endpoint-id 参数或配置到 config.json

3. 融合信息搜索有独立的接入方式
   - 请查看具体产品的接入文档
   - 可能需要特定的 Bot ID 或端点

建议：
- 确认这个 Key 是从哪个页面复制的？
- 如果是「联网问答Agent」的 Key，可能需要配合 Bot ID 使用
""")
    
    # 如果用户有 Endpoint ID，提示可以测试
    print("\n如果你有 Endpoint ID，可以运行：")
    print(f"  python3 {os.path.dirname(__file__)}/search.py '你的问题' --endpoint-id ep-xxxxxxxx")


if __name__ == "__main__":
    main()
