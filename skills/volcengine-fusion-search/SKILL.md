---
name: volcengine-fusion-search
description: 火山引擎融合信息搜索 - 调用火山方舟API进行联网搜索问答，获取实时网络信息并回答用户问题。适用于需要最新资讯、实时数据、热点事件查询等场景。
when: |
  用户需要联网搜索、实时信息查询、最新资讯获取时使用。
  触发场景包括但不限于：
  - "搜索一下..." / "查一下..."
  - "联网搜索..." / "上网查..."
  - "最新..." / "今天..."
  - "帮我找一下..."
  - 涉及时效性问题（新闻、股价、天气等）
  - 用户明确要求使用联网搜索功能
examples:
  - "搜索一下今天的科技新闻"
  - "查一下最新的 AI 发展趋势"
  - "帮我搜索 iPhone 16 的评测"
  - "联网查一下今天北京天气"
  - "搜索一下最新的电影票房"
  - "查一下比特币的最新价格"
metadata:
  openclaw:
    requires:
      bins: ["python3"]
      env: ["VOLCENGINE_API_KEY"]
    emoji: "🔍"
    timeout: 120
---

# 火山引擎融合信息搜索

调用火山方舟大模型的联网搜索能力，实时获取网络信息并回答用户问题。

## 前置要求

支持两种认证方式：

### 方式 1: API Key (Bearer Token)
```bash
export VOLCENGINE_API_KEY="your-api-key"
```

### 方式 2: Access Key / Secret Key (AK/SK 签名)
```bash
export VOLCENGINE_ACCESS_KEY_ID="your-ak"
export VOLCENGINE_SECRET_ACCESS_KEY="your-sk"
```

> **注意**: 如果 SK 是 Base64 编码的（以 `==` 结尾），需要先解码：
> ```bash
> echo "your-sk" | base64 -d
> ```

## 快速开始

### 1. 配置 API Key

```bash
export VOLCENGINE_API_KEY="your-api-key-here"
```

### 2. 使用方法

直接询问需要联网搜索的问题，系统会自动调用此技能：

```
用户: 搜索一下今天的科技新闻
系统: [自动调用 volcengine-fusion-search 技能]
```

## 工作原理

1. 接收用户查询
2. 调用火山方舟 API (`https://ark.cn-beijing.volces.com/api/v3/bots/chat/completions`)
3. 模型自动进行联网搜索
4. 返回整合后的答案

## API 详情

### 端点
```
POST https://ark.cn-beijing.volces.com/api/v3/bots/chat/completions
```

### 默认模型
- `doubao-1.5-pro-32k-250115`

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model | string | 是 | 模型ID |
| messages | array | 是 | 对话消息列表 |
| stream | boolean | 否 | 是否流式输出 |
| max_tokens | integer | 否 | 最大生成token数 |
| temperature | float | 否 | 采样温度 |

## 配置选项

编辑 `config.json` 可自定义：

```json
{
  "api_endpoint": "https://ark.cn-beijing.volces.com/api/v3/bots/chat/completions",
  "default_model": "doubao-1.5-pro-32k-250115",
  "timeout": 60,
  "max_tokens": 4096,
  "temperature": 0.7
}
```

## 手动调用脚本

```bash
cd ~/.openclaw/workspace/skills/volcengine-fusion-search
python3 search.py "你的搜索问题"
```

参数说明：
- `query`: 搜索内容（必填）
- `--endpoint-id, -e`: 指定 Endpoint ID（推荐）
- `--bot-id, -b`: 指定 Bot ID
- `--debug, -d`: 开启调试模式

## 配置 Endpoint ID（推荐）

方舟平台推荐使用 Endpoint ID 而非直接使用模型名：

1. 登录[火山引擎控制台](https://console.volcengine.com/ark/)
2. 进入「在线推理」创建 Endpoint
3. 复制 Endpoint ID（格式: `ep-xxxxxxxx`）
4. 配置到 `config.json`:

```json
{
  "endpoint_id": "ep-20250204123456-xxxxx"
}
```

或使用命令行：
```bash
python3 search.py "今天的新闻" --endpoint-id ep-xxxxxxxx
```

## 错误处理

| 错误类型 | 可能原因 | 解决方案 |
|----------|----------|----------|
| API Key 无效 (401) | 密钥错误或不是方舟平台 Key | 确认 Key 来源，或修改 `api_endpoint` 为正确的服务端点 |
| 网络错误 | 连接超时 | 检查网络连接 |
| 模型不可用 | 模型ID错误 | 检查 config.json 中的模型配置 |
| 请求超时 | 查询过于复杂 | 简化查询或增加 timeout |

### 关于 401 错误的特别说明

如果收到 `AuthenticationError` / `Unauthorized` 错误：

#### 原因 1: 需要使用 Endpoint ID
你的 API Key 需要配合 Endpoint ID 使用：
```bash
# 先运行诊断工具查看问题
python3 diagnose.py

# 然后使用 Endpoint ID 调用
python3 search.py "你的问题" --endpoint-id ep-xxxxxxxx
```

#### 原因 2: API Key 服务不匹配
火山引擎不同服务使用不同的 Key：
- 方舟大模型平台 Key → 通常以 `AK-` 开头
- 其他 AI 服务 → 各自独立的 Key

**解决方案：** 前往 [方舟控制台](https://console.volcengine.com/ark/) 创建正确的 API Key

#### 原因 3: 需要使用 Bot ID
如果「联网问答Agent」是作为 Bot 发布的：
```json
{
  "bot_id": "your-bot-id"
}
```

### 诊断工具

运行诊断工具排查问题：
```bash
python3 diagnose.py
```

这将测试多种接入方式并给出解决方案。

## 适用场景

✅ **适合使用**:
- 最新新闻资讯
- 实时数据查询（股价、天气等）
- 热点事件追踪
- 产品评测对比
- 时效性知识

❌ **不适合使用**:
- 纯本地知识问答
- 需要深度推理的数学问题
- 涉及个人隐私的查询

## 安全提示

- API Key 请妥善保管，不要提交到代码仓库
- 建议在 `.bashrc` 或 `.zshrc` 中设置环境变量
- 生产环境建议使用密钥管理服务

## 参考文档

- [火山引擎融合信息搜索API文档](https://www.volcengine.com/docs/85508/1650263)
- [方舟大模型平台](https://console.volcengine.com/ark/)

## 更新日志

### v1.0.0 (2026-02-04)
- 初始版本
- 支持基础联网搜索
- 支持自定义模型和参数
