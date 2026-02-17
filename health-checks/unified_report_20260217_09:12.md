# 📊 系统状态统一报告

**生成时间:** 2026-02-17 09:12:40  
**系统健康度:** 70/100 (🟡 良好)

---

## 🖥️ 系统资源

| 指标 | 数值 | 状态 |
|------|------|------|
| CPU | 0.0% | ✅ |
| 内存 | 37% | ✅ |
| 磁盘 | 58% | ✅ |
| 负载 | 6.21 | 0
✅ |
| 运行时间 | up 8 hours, 18 minutes | - |

---

## 🔧 服务状态

| 服务 | 状态 | 详情 |
|------|------|------|
| OpenClaw Gateway | ✅ | 运行中 |
| Mihomo 代理 | ✅ | 运行中 |
| Cron 服务 | ⚠️ | 未运行 |

---

## 🏥 自愈系统

ℹ️ 暂无自愈记录



---

## 🔐 安全状态

| 项目 | 状态 | 详情 |
|------|------|------|
| 安全扫描 | 🔴 需关注 | 发现高风险问题 |
| 定时任务 | ✅ | 检查器未安装 |

---

## 📋 快速操作

```bash
# 查看详细报告
cat /root/.openclaw/workspace/health-checks/unified_report_20260217_09:12.md

# 运行全面检查
bash /root/.openclaw/workspace/scripts/unified_health_system.sh full

# 查看最新日志
tail -20 /var/log/bowlwanpi-health.log
```

---

*统一报告生成器 v1.1 (修复版)*
