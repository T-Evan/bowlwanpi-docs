#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火山引擎融合信息搜索脚本
支持多种认证方式：
1. Bearer Token (API Key)
2. AK/SK 签名认证 (Access Key / Secret Key)
"""

import os
import sys
import json
import hmac
import hashlib
import datetime
import argparse
import urllib.request
import urllib.error
from typing import Optional, Dict, Any


def get_api_key() -> Optional[str]:
    """从环境变量获取 API Key (Bearer Token 方式)"""
    return os.environ.get("VOLCENGINE_API_KEY")


def get_ak_sk() -> tuple:
    """从环境变量获取 AK/SK (签名认证方式)"""
    ak = os.environ.get("VOLCENGINE_ACCESS_KEY_ID")
    sk = os.environ.get("VOLCENGINE_SECRET_ACCESS_KEY")
    return ak, sk


def sign_request(ak: str, sk: str, method: str, uri: str, query: str, headers: dict, body: bytes) -> dict:
    """
    火山引擎 AK/SK 签名
    参考: https://www.volcengine.com/docs/6369/67269
    """
    # 获取当前时间
    now = datetime.datetime.utcnow()
    date_stamp = now.strftime("%Y%m%d")
    time_stamp = now.strftime("%Y%m%dT%H%M%SZ")
    
    # 规范化 URI
    if not uri:
        uri = "/"
    canonical_uri = uri
    
    # 规范化 Query
    canonical_query = query if query else ""
    
    # 规范化 Headers
    signed_headers = "host;x-date"
    host = headers.get("Host", "ark.cn-beijing.volces.com")
    canonical_headers = f"host:{host}\n" + f"x-date:{time_stamp}\n"
    
    # 计算 Body 的 SHA256
    if body:
        body_hash = hashlib.sha256(body).hexdigest()
    else:
        body_hash = hashlib.sha256(b"").hexdigest()
    
    # 构建规范请求
    canonical_request = f"{method}\n{canonical_uri}\n{canonical_query}\n{canonical_headers}\n{signed_headers}\n{body_hash}"
    
    # 构建待签名字符串
    algorithm = "HMAC-SHA256"
    credential_scope = f"{date_stamp}/cn-beijing/ark/request"
    string_to_sign = f"{algorithm}\n{time_stamp}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
    
    # 计算签名密钥
    k_date = hmac.new(f"TC3{sk}".encode(), date_stamp.encode(), hashlib.sha256).digest()
    k_region = hmac.new(k_date, "cn-beijing".encode(), hashlib.sha256).digest()
    k_service = hmac.new(k_region, "ark".encode(), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, "request".encode(), hashlib.sha256).digest()
    
    # 计算签名
    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
    
    # 构建 Authorization
    authorization = f"{algorithm} Credential={ak}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    
    return {
        "Authorization": authorization,
        "X-Date": time_stamp,
        "Host": host
    }


def load_config() -> dict:
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    default_config = {
        "api_endpoint": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        "endpoint_id": None,
        "bot_id": None,
        "timeout": 60,
        "max_tokens": 4096,
        "temperature": 0.7,
        "debug": False,
        "use_search": True,
        "auth_type": "auto"  # auto, apikey, aksk
    }
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
    except FileNotFoundError:
        return default_config


def make_request_with_apikey(endpoint: str, payload: dict, api_key: str, timeout: int = 60, debug: bool = False) -> dict:
    """使用 API Key (Bearer Token) 发送请求"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    if debug:
        print(f"\n[DEBUG] API Key 模式", file=sys.stderr)
        print(f"[DEBUG] 端点: {endpoint}", file=sys.stderr)
    
    try:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
            return {"success": True, "data": result}
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        return {"success": False, "error": f"HTTP {e.code}", "details": error_body}
    except Exception as e:
        return {"success": False, "error": str(e)}


def make_request_with_aksk(endpoint: str, payload: dict, ak: str, sk: str, timeout: int = 60, debug: bool = False) -> dict:
    """使用 AK/SK 签名发送请求"""
    import urllib.parse
    
    parsed = urllib.parse.urlparse(endpoint)
    uri = parsed.path
    query = parsed.query
    
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    
    base_headers = {
        "Content-Type": "application/json",
        "Host": parsed.netloc
    }
    
    # 计算签名
    signed_headers = sign_request(ak, sk, "POST", uri, query, base_headers, body)
    headers = {**base_headers, **signed_headers}
    
    if debug:
        print(f"\n[DEBUG] AK/SK 签名模式", file=sys.stderr)
        print(f"[DEBUG] AK: {ak[:8]}...", file=sys.stderr)
        print(f"[DEBUG] 端点: {endpoint}", file=sys.stderr)
        print(f"[DEBUG] Authorization: {headers['Authorization'][:50]}...", file=sys.stderr)
    
    try:
        req = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
            return {"success": True, "data": result}
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        return {"success": False, "error": f"HTTP {e.code}", "details": error_body}
    except Exception as e:
        return {"success": False, "error": str(e)}


def search(query: str, endpoint_id: Optional[str] = None, bot_id: Optional[str] = None, 
           debug: bool = False) -> str:
    """
    执行融合信息搜索
    自动检测使用 API Key 还是 AK/SK 认证
    """
    config = load_config()
    if debug:
        config["debug"] = True
    
    # 获取认证信息
    api_key = get_api_key()
    ak, sk = get_ak_sk()
    
    auth_type = config.get("auth_type", "auto")
    
    if debug:
        print(f"[DEBUG] API Key: {'有' if api_key else '无'}", file=sys.stderr)
        print(f"[DEBUG] AK/SK: {'有' if ak and sk else '无'}", file=sys.stderr)
        print(f"[DEBUG] 认证类型: {auth_type}", file=sys.stderr)
    
    # 确定认证方式
    if auth_type == "aksk" or (auth_type == "auto" and ak and sk and not api_key):
        if not ak or not sk:
            return "错误: 未设置 AK/SK 环境变量\n请执行:\nexport VOLCENGINE_ACCESS_KEY_ID='your-ak'\nexport VOLCENGINE_SECRET_ACCESS_KEY='your-sk'"
        use_aksk = True
    elif auth_type == "apikey" or api_key:
        if not api_key:
            return "错误: 未设置 VOLCENGINE_API_KEY 环境变量"
        use_aksk = False
    else:
        return "错误: 未设置任何认证信息\n请设置 API Key 或 AK/SK"
    
    # 构建请求
    endpoint = config.get("api_endpoint", "https://ark.cn-beijing.volces.com/api/v3/chat/completions")
    
    # 确定 model
    ep_id = endpoint_id or config.get("endpoint_id")
    b_id = bot_id or config.get("bot_id")
    
    if ep_id:
        model = ep_id
    elif b_id:
        model = b_id
        endpoint = f"https://ark.cn-beijing.volces.com/api/v3/bots/{b_id}/chat/completions"
    else:
        model = config.get("default_model", "doubao-1.5-pro-32k-250115")
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": query}
        ],
        "stream": False
    }
    
    if config.get("max_tokens"):
        payload["max_tokens"] = config["max_tokens"]
    if config.get("temperature") is not None:
        payload["temperature"] = config["temperature"]
    
    # 发送请求
    if use_aksk:
        result = make_request_with_aksk(endpoint, payload, ak, sk, config.get("timeout", 60), debug)
    else:
        result = make_request_with_apikey(endpoint, payload, api_key, config.get("timeout", 60), debug)
    
    if result["success"]:
        data = result["data"]
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0].get("message", {}).get("content", "")
        return json.dumps(data, ensure_ascii=False)
    else:
        error_msg = f"错误: {result.get('error')}\n详情: {result.get('details', '无')}"
        if "401" in result.get('error', ''):
            error_msg += "\n\n提示: 认证失败，请检查:\n"
            if use_aksk:
                error_msg += "1. AK/SK 是否正确\n2. 是否有权限访问该服务"
            else:
                error_msg += "1. API Key 是否正确\n2. 是否需要使用 AK/SK 方式"
        return error_msg


def main():
    parser = argparse.ArgumentParser(description="火山引擎融合信息搜索")
    parser.add_argument("query", help="搜索查询内容")
    parser.add_argument("--endpoint-id", "-e", help="指定 Endpoint ID (如 ep-xxxxxxxx)")
    parser.add_argument("--bot-id", "-b", help="指定 Bot ID")
    parser.add_argument("--debug", "-d", action="store_true", help="开启调试模式")
    parser.add_argument("--aksk", "-a", action="store_true", help="强制使用 AK/SK 认证")
    
    args = parser.parse_args()
    
    if args.aksk:
        config = load_config()
        config["auth_type"] = "aksk"
        with open(os.path.join(os.path.dirname(__file__), "config.json"), "w") as f:
            json.dump(config, f, indent=2)
    
    result = search(args.query, args.endpoint_id, args.bot_id, args.debug)
    print(result)


if __name__ == "__main__":
    main()
