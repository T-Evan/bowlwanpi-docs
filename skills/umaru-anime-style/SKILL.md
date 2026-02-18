---
name: umaru-anime-style
description: 固化「一碗专属动漫质感人物风格」的图片生成技能。用于根据对话内容快速生成同一人物风格的图片。
version: 1.0.0
---

# Umaru Anime Style

## 用途
- 固定使用「动漫质感」而非“动漫升舱质感”
- 固定人物锚点（长发橙金色、暖色调、可爱活泼）
- 可按场景快速出图（游戏、日常、雨夜、梦幻等）

## 触发语句
- "按一碗风格出图"
- "生成同风格图片"
- "用动漫质感再来一张"

## 执行方式
```bash
python3 {baseDir}/scripts/generate.py --scene "cozy gaming room" --mood "playful"
```

## 参数
- `--scene`: 场景描述（英文短语）
- `--mood`: 情绪（playful/happy/calm/excited）
- `--action`: 动作（holding a game controller 等）
- `--output-dir`: 输出目录（默认 `/root/.openclaw/workspace/tmp`）

## 固化规则（强制）
1. 风格关键词必须包含：`anime texture`, `clean lineart`, `rich cel-shading`
2. 人物锚点必须包含：`long flowing golden-orange hair`, `large amber eyes`, `oversized orange hoodie`
3. 输出文案使用“动漫质感”字样，不使用“动漫升舱质感”
4. 若用户未给细节，默认场景：`cozy gamer bedroom`

## 参考配置
见 `references/style_profile.md`
