#!/usr/bin/env python3
"""
腾讯云联网搜索 Skill - WSA (Web Search API) 实现
使用腾讯云 WSA 服务进行实时网页搜索
"""

import json
import os
import sys
from typing import List, Dict, Any, Optional
import asyncio

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.wsa.v20250508 import wsa_client, models

# 配置
CREDENTIALS_PATH = '/root/.openclaw/workspace/secrets/tencent-credentials.json'


class TencentWebSearchClient:
    """腾讯云 WSA 联网搜索客户端"""
    
    def __init__(self, region: str = ''):
        """
        初始化 WSA 客户端
        
        Args:
            region: 区域代码（WSA 不需要特定区域，传空字符串即可）
        """
        self.secret_id = None
        self.secret_key = None
        self.region = region
        self.cred = None
        self.client = None
        self._load_credentials()
    
    def _load_credentials(self):
        """加载腾讯云凭证"""
        try:
            if os.path.exists(CREDENTIALS_PATH):
                with open(CREDENTIALS_PATH, 'r') as f:
                    creds = json.load(f)
                    self.secret_id = creds.get('secret_id')
                    self.secret_key = creds.get('secret_key')
                    # WSA 不需要特定区域，使用空字符串
                    if self.region is None:
                        self.region = ''
                    
                    # 初始化凭证
                    if self.secret_id and self.secret_key:
                        self.cred = credential.Credential(self.secret_id, self.secret_key)
                        
                        # 创建 WSA 客户端
                        http_profile = HttpProfile()
                        http_profile.endpoint = "wsa.tencentcloudapi.com"
                        
                        client_profile = ClientProfile()
                        client_profile.httpProfile = http_profile
                        
                        self.client = wsa_client.WsaClient(
                            self.cred, 
                            self.region, 
                            client_profile
                        )
        except Exception as e:
            print(f"⚠️ 加载凭证失败: {e}")
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return self.client is not None
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        执行 WSA 联网搜索
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
        
        Returns:
            List[Dict]: 搜索结果列表
        """
        if not self.is_configured():
            return [{"error": "腾讯云凭证未配置"}]
        
        try:
            # 创建搜索请求
            req = models.SearchProRequest()
            
            # 设置请求参数
            params = {
                "Query": query,
                "Count": num_results
            }
            req.from_json_string(json.dumps(params))
            
            # 调用搜索 API
            resp = self.client.SearchPro(req)
            
            # 解析结果 - Pages 是 JSON 字符串列表
            results = []
            if resp and hasattr(resp, 'Pages') and resp.Pages:
                for page_str in resp.Pages[:num_results]:
                    try:
                        page_data = json.loads(page_str)
                        results.append({
                            "title": page_data.get('title', ''),
                            "content": page_data.get('passage', ''),
                            "url": page_data.get('url', ''),
                            "site": page_data.get('site', ''),
                            "date": page_data.get('date', ''),
                            "score": page_data.get('score', 0),
                            "source": "tencent_wsa"
                        })
                    except json.JSONDecodeError:
                        continue
            
            return results if results else [{"info": "搜索完成，但未返回结果"}]
            
        except TencentCloudSDKException as e:
            error_msg = str(e)
            if "UnauthorizedOperation" in error_msg:
                return [{
                    "error": "未授权操作",
                    "suggestion": "请在腾讯云控制台开通 WSA (Web Search API) 服务"
                }]
            else:
                return [{"error": f"腾讯云API错误: {e}"}]
        except Exception as e:
            return [{"error": f"搜索失败: {e}"}]


# 便捷函数
async def search_tencent_web(query: str, num_results: int = 10) -> List[Dict]:
    """快捷搜索函数"""
    client = TencentWebSearchClient()
    return await client.search(query, num_results)


if __name__ == '__main__':
    # 测试
    async def test():
        print("🔍 测试腾讯云 WSA 联网搜索...\n")
        
        client = TencentWebSearchClient()
        if client.is_configured():
            print("✅ WSA 客户端配置成功")
            print(f"   SecretId: {client.secret_id[:10]}...")
            print()
            
            # 测试搜索
            queries = ["人工智能", "OpenClaw"]
            
            for query in queries:
                print(f"🔍 搜索: {query}")
                results = await client.search(query, num_results=3)
                
                if results and 'error' in results[0]:
                    print(f"   ❌ 错误: {results[0]['error']}")
                    if 'suggestion' in results[0]:
                        print(f"   💡 建议: {results[0]['suggestion']}")
                elif results and 'info' in results[0]:
                    print(f"   ℹ️ {results[0]['info']}")
                else:
                    print(f"   ✅ 找到 {len(results)} 条结果:")
                    for i, result in enumerate(results, 1):
                        title = result.get('title', '无标题')
                        content = result.get('content', '无内容')[:80]
                        url = result.get('url', '')
                        site = result.get('site', '')
                        print(f"   {i}. {title}")
                        print(f"      {content}...")
                        if site:
                            print(f"      📰 {site}")
                        if url:
                            print(f"      → {url}")
                        print()
        else:
            print("❌ 腾讯云凭证未配置")
    
    asyncio.run(test())
