---
name: novelai-image-gen
description: NovelAI 图像生成技能，支持自定义 API、角色管理和场景生图。基于 chami_tavern-scene-plugin 项目参考实现。
version: 1.0.0
metadata:
  openclaw:
    emoji: 🎨
    requires:
      bins:
        - python3
      python_packages:
        - requests
        - pillow
    homepage: https://novelai.net
---

# NovelAI 图像生成技能

基于 [chami_tavern-scene-plugin](https://github.com/shaochami/chami_tavern-scene-plugin) 项目参考实现的 NovelAI 图像生成工具。

## ✨ 功能特性

- 🎨 **文生图**: 支持 NovelAI Anime/Furry 模型
- 👤 **角色管理**: 创建、保存、加载角色卡
- 🏷️ **场景标签**: 16000+ 标签库，支持中英文搜索
- 🔧 **自定义 API**: 支持自定义 NovelAI API 端点
- ⚙️ **参数配置**: 分辨率、采样器、CFG、步数等
- 🖼️ **智能提示词**: 角色+场景自动组合

## 🚀 快速开始

### 1. 配置 API Key

编辑 `config.json`，填入你的 NovelAI API Key：

```json
{
  "api_key": "your-api-key-here",
  "base_url": "https://image.novelai.net"
}
```

### 2. 基础生图

```bash
python3 scripts/generate.py --prompt "1girl, anime style, blue hair"
```

### 3. 使用角色

```bash
# 创建角色
python3 scripts/character.py create --name "蓝发少女" --tags "1girl,blue hair,school uniform"

# 使用角色生图
python3 scripts/generate.py --character "蓝发少女" --scene "教室背景"
```

## 📖 详细用法

### 命令行参数

```bash
python3 scripts/generate.py [选项]

必选参数:
  --prompt TEXT          正面提示词

可选参数:
  --character TEXT       使用已保存的角色
  --scene TEXT          使用场景标签
  --negative TEXT       负面提示词
  --resolution TEXT     分辨率 (如 832x1216)
  --sampler TEXT        采样器 (k_euler_ancestral/k_euler/k_dpmpp_2m...)
  --steps INT           采样步数 (1-50)
  --cfg FLOAT           CFG Scale (1-10)
  --seed INT           随机种子 (-1 为随机)
  --model TEXT         模型 (anime/anime_v3/furry)
  --output PATH        输出路径
```

### 角色管理

```bash
# 列出所有角色
python3 scripts/character.py list

# 创建角色
python3 scripts/character.py create --name "角色名" --tags "标签1,标签2"

# 查看角色
python3 scripts/character.py show --name "角色名"

# 删除角色
python3 scripts/character.py delete --name "角色名"

# 导入角色卡 (PNG)
python3 scripts/character.py import --file character.png

# 导出角色卡
python3 scripts/character.py export --name "角色名" --output char.png
```

### 场景标签

```bash
# 搜索标签
python3 scripts/scene.py search "教室"

# 浏览分类
python3 scripts/scene.py categories

# 列出分类下的标签
python3 scripts/scene.py list --category "背景"
```

## 🎨 提示词技巧

### 基础结构

```
[质量标签], [角色描述], [服装], [姿势], [表情], [场景], [光照], [画风]
```

### 示例

```
masterpiece, best quality, 1girl, solo, blue hair, long hair, 
school uniform, serafuku, standing, smile, looking at viewer,
classroom, window, sunset, warm lighting, anime style
```

### 负面提示词推荐

```
lowres, bad anatomy, bad hands, text, error, missing fingers, 
extra digit, fewer digits, cropped, worst quality, low quality, 
normal quality, jpeg artifacts, signature, watermark, username, 
blurry, bad feet, mutation, deformed, extra limbs, extra arms, 
extra legs, malformed limbs, fused fingers, too many fingers, 
long neck, cross-eyed, mutated hands, polar lowres, bad face
```

## 🔧 配置说明

### config.json

```json
{
  "api_key": "your-api-key",
  "base_url": "https://image.novelai.net",
  "defaults": {
    "model": "anime",
    "width": 1024,
    "height": 1024,
    "sampler": "k_euler_ancestral",
    "steps": 28,
    "cfg_scale": 6.0,
    "negative_prompt": "lowres, bad anatomy...",
    "seed": -1,
    "n_samples": 1,
    "output_dir": "outputs"
  },
  "models": {
    "anime": "nai-diffusion-4-5-full",
    "anime_v3": "nai-diffusion-3",
    "furry": "nai-diffusion-furry-3"
  }
}
```

### 自定义 API 端点

如果你有自定义的 NovelAI 兼容 API，修改 `base_url`：

```json
{
  "api_key": "your-key",
  "base_url": "https://your-custom-api.com"
}
```

## 📁 文件结构

```
novelai-image-gen/
├── SKILL.md                 # 本文档
├── config.json             # 配置文件
├── data/
│   ├── characters/         # 角色数据
│   ├── scenes/            # 场景标签
│   └── outputs/           # 生成图片
├── scripts/
│   ├── generate.py        # 主生图脚本
│   ├── character.py       # 角色管理
│   ├── scene.py           # 场景标签
│   └── novelai_client.py  # API 客户端
└── modules/
    ├── __init__.py
    ├── character_db.py    # 角色数据库
    ├── prompt_builder.py  # 提示词构建器
    ├── tag_manager.py     # 标签管理器
    └── novelai_api.py     # API 封装
```

## ⚠️ 注意事项

1. **API Key 安全**: 不要将包含 API Key 的 config.json 提交到 Git
2. **图片版权**: 使用 NovelAI 生成的图片需遵守 NovelAI 使用条款
3. **网络代理**: 如需要代理，可设置环境变量 `HTTP_PROXY` 和 `HTTPS_PROXY`

## 📝 许可

参考 chami_tavern-scene-plugin 项目实现，仅供学习研究使用。
