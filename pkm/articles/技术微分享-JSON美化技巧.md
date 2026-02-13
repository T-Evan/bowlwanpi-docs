# 技术微分享：JSON 美化输出技巧

## 问题
处理 JSON 文件时，原始输出全是单行，难以阅读。

## 解决方案
使用 `jq` 命令一键美化：

```bash
# 美化输出（带颜色）
cat file.json | jq '.'

# 压缩输出（最小化）
cat file.json | jq -c '.'

# 提取特定字段
cat file.json | jq '.key'
```

## 进阶技巧
```bash
# 过滤数据
jq '.[] | select(.age > 20)' data.json

# 统计数量
jq '[.[] | select(.status == "active")] | length' data.json
```

## 适用场景
- API 调试
- 日志分析
- 数据提取

> 💡 小技巧：配合 `jq .` 使用管道，可以对任何 JSON 数据进行实时美化！

---

*200字达成～一碗觉得这个技巧实用吗？(｡･ω･｡)*
