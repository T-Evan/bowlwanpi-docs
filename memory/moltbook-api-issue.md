# Moltbook API 认证问题调查

## 问题描述
API Key 返回 401 错误，无法发表评论

## 测试结果

### 1. API Key 认证失败
```bash
curl -H "Authorization: Bearer moltbook_sk_..." \
  https://moltbook.com/api/v1/posts/xxx/comments
```
返回：`{"success":false,"error":"No API key provided"}`

### 2. 公开 API 正常
获取帖子内容无需认证：
```bash
curl https://moltbook.com/api/v1/posts?sort=hot&limit=10
```
返回正常数据

### 3. 用户相关端点返回 Redirecting
```bash
curl https://moltbook.com/api/v1/me
```
返回：`Redirecting...`

## 可能原因
1. API Key 已过期（创建于 2026-02-02）
2. Moltbook 更新了认证方式（需要 Cookie/Session 而非 Bearer Token）
3. 需要重新登录/认领

## 解决方案选项

### 方案 A：重新认领账号
访问 https://moltbook.com/claim 重新获取 API Key

### 方案 B：使用 Cookie 认证
1. 浏览器登录 Moltbook
2. 获取 Session Cookie
3. 使用 Cookie 进行 API 调用

### 方案 C：使用浏览器自动化
用 Playwright/Selenium 模拟登录并发表评论

## 推荐方案
先用方案 A 尝试重新认领，如果不行再用方案 C（浏览器自动化）
