# volcengine-fusion-search

火山引擎融合信息搜索技能 - 联网问答Agent，支持实时搜索网络信息并回答用户问题。

## 安装

```bash
# 克隆到 OpenClaw skills 目录
cd ~/.openclaw/skills
git clone https://github.com/yourusername/volcengine-fusion-search.git

# 或者直接复制到 workspace/skills/
cp -r volcengine-fusion-search ~/.openclaw/workspace/skills/
```

## 配置

### 1. 获取火山引擎 API Key

1. 访问 [火山引擎控制台](https://console.volcengine.com/)
2. 进入「方舟」->「API Key 管理」
3. 创建 API Key

### 2. 配置环境变量

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export VOLCENGINE_API_KEY="your-api-key-here"
```

## 使用方法

在聊天中直接询问需要联网搜索的问题：

- "搜索一下今天的科技新闻"
- "查一下最新的 AI 发展趋势"
- "帮我搜索某某产品的评测"
- "联网查一下今天天气"
- "搜索 + 你的问题"

## API 说明

### 端点
```
POST https://ark.cn-beijing.volces.com/api/v3/bots/chat/completions
```

### 支持的模型
- `doubao-1.5-pro-32k-250115` - Doubao 1.5 Pro
- 以及其他支持联网搜索的方舟模型

### 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| model | string | 模型ID |
| messages | array | 对话消息 |
| stream | boolean | 是否流式输出 |

## 文件说明

- `SKILL.md` - 技能定义文件
- `search.py` - 搜索脚本
- `config.json` - 配置文件

## 许可证

MIT
