# 🔐 SECURITY.md - 安全最佳实践

**制定时间:** 2026-02-14  
**基于:** eudaemon_0 "Supply Chain Attack" 警示 + 安全审计结果  
**适用范围:** ~/.openclaw/workspace/scripts/

---

## 🛡️ 安全原则

### 1. 不信任，验证 (Trust but Verify)
- 所有技能必须自己编写或审计
- 不安装不明来源的技能
- 定期运行安全扫描

### 2. 最小权限 (Least Privilege)
- 脚本仅访问必要的资源
- 网络请求仅访问可信域名
- 敏感操作需要确认

### 3. 纵深防御 (Defense in Depth)
- 多层安全检查
- 密钥隔离存储
- 定期备份

---

## 📋 安全清单

### 技能安装前检查清单

```markdown
□ 来源验证
  - [ ] 来自可信作者
  - [ ] 有社区验证或审计
  - [ ] 代码完全开源

□ 代码审查
  - [ ] 阅读并理解所有代码
  - [ ] 检查网络请求目的地
  - [ ] 确认文件系统访问范围
  - [ ] 验证无混淆或加密代码

□ 网络请求检查
  - [ ] 无意外的外部请求
  - [ ] 所有请求目的地可信
  - [ ] 无 webhook 调用外部

□ 凭证访问检查
  - [ ] 不读取 ~/.clawdbot/.env
  - [ ] 不访问其他应用的凭证
  - [ ] 密钥存储在安全位置

□ 危险函数检查
  - [ ] 无 eval 执行用户输入
  - [ ] 无 exec 执行外部命令
  - [ ] 无 base64 编码的隐藏代码

□ 依赖审查
  - [ ] 依赖数量合理
  - [ ] 无不必要的依赖
  - [ ] 依赖版本最新
```

### 安全等级评估

| 等级 | 图标 | 描述 | 行动 |
|------|------|------|------|
| 🟢 安全 | ✅ | 无风险，可信来源 | 可以安装 |
| 🟡 低风险 | ⚠️ | 有网络请求，但可信 | 审查后安装 |
| 🟠 中风险 | ⚠️ | 访问敏感资源 | 详细审计后安装 |
| 🔴 高风险 | ❌ | 可疑行为 | 拒绝安装 |

---

## 🔍 安全扫描

### 定期扫描

**频率:** 每周一次  
**命令:**
```bash
bash ~/.openclaw/workspace/scripts/security_check.sh
```

**扫描内容:**
1. 可疑网络请求 (webhook, 外部 POST)
2. 敏感文件访问 (.env, credentials)
3. Base64 编码内容
4. 危险函数使用 (eval, exec)
5. 脚本统计
6. Secrets 目录权限
7. 新脚本检测

### 扫描报告位置

```
~/.openclaw/workspace/learning/security-reports/
├── security_scan_YYYYMMDD_HHMMSS.md
├── security_alerts.txt
└── .last_scan
```

---

## 📊 当前安全状态

### 审计结果 (2026-02-14)

**脚本总数:** 86 (64 Python + 19 Shell + 2 JS + 1 其他)

| 检查项 | 结果 | 风险等级 |
|--------|------|----------|
| Webhook 请求 | 未发现 | 🟢 安全 |
| 外部 POST | 7 个脚本，均为正常 API | 🟢 安全 |
| 敏感文件访问 | 正常环境变量使用 | 🟢 安全 |
| Base64 编码 | 未发现 | 🟢 安全 |
| 危险函数 | 正常 systemctl 使用 | 🟢 安全 |
| Secrets 权限 | 755 (建议 700) | 🟡 低风险 |

**总体评估:** 🟢 **安全**

### 已实施的安全措施

✅ **所有技能自己编写** - 无外部不明代码  
✅ **密钥隔离存储** - secrets/ 目录，不提交 git  
✅ **定期备份** - 自动备份机制  
✅ **代理配置** - 网络请求通过本地代理  
✅ **自动安全扫描** - 每周运行  

### 建议增强措施

🔄 **API Key 轮换** - 每 3 个月轮换一次  
🔄 **Secrets 权限** - 改为 700  
🔄 **依赖审查** - 使用 npm audit / pip audit  
🔄 **日志审计** - 启用详细访问日志  

---

## 🚨 应急响应

### 发现安全问题的处理流程

1. **立即隔离**
   ```bash
   # 停止使用可疑脚本
   chmod -x suspicious_script.sh
   ```

2. **检查影响范围**
   ```bash
   # 查看日志
   grep "suspicious_script" /var/log/syslog
   ```

3. **通知一碗**
   - 发送飞书消息
   - 附上安全报告
   - 说明影响范围

4. **修复或删除**
   - 如果是误报，记录原因
   - 如果是真实威胁，删除并清理

5. **事后总结**
   - 更新安全清单
   - 完善扫描脚本
   - 记录经验教训

### 紧急联系人

- **一碗:** 飞书消息
- **OpenClaw 支持:** https://docs.openclaw.ai
- **Moltbook 安全讨论:** https://www.moltbook.com

---

## 📚 参考资源

### 必读安全帖子
- **eudaemon_0** - "The supply chain attack nobody is talking about: skill.md is an unsigned binary"
  - 点赞: 4799
  - 核心: 技能供应链攻击风险

### 安全工具
- `security_check.sh` - 自动化安全扫描
- `yara` - 恶意代码检测 (参考 Rufio 的方法)

### 社区资源
- Moltbook - 安全讨论和最佳实践分享
- OpenClaw 文档 - 安全配置指南

---

## 📝 更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-02-14 | 初始版本，基于首次安全审计 |

---

*安全负责人: BowlWanpi 🥣*  
*座右铭: "Don't ask for permission to be helpful. Just build it securely."*