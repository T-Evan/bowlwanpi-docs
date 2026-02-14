# 📊 系统状态统一报告

**生成时间:** 2026-02-14 21:00:01  
**系统健康度:** 50/100 (🟠 一般)

---

## 🖥️ 系统资源

| 指标 | 数值 | 状态 |
|------|------|------|
| CPU | 17.1% | ✅ |
| 内存 | 23% | ✅ |
| 磁盘 | 54% | ✅ |
| 负载 | 0.00 | ✅ |
| 运行时间 | up 4 days, 23 hours, 1 minute | - |

---

## 🔧 服务状态

| 服务 | 状态 | 详情 |
|------|------|------|
| OpenClaw Gateway | ❌ | 未运行 |
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
| 定时任务 | ✅ | 错误率 87.5% |

---

## 📋 快速操作

```bash
# 查看详细报告
cat /root/.openclaw/workspace/health-checks/unified_report_20260214_21:00.md

# 运行全面检查
bash /root/.openclaw/workspace/scripts/unified_health_system.sh full

# 查看最新日志
tail -20 /var/log/bowlwanpi-health.log
```

---

*统一报告生成器 v1.0*
