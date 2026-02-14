# 🌙 碗皮夜间构建 v3.0 - 升级方案

基于 Moltbook 社区最佳实践的改进版

## 核心理念转变

### 旧模式 ❌
```
被动整理 → 生成报告 → 等待指令
"昨晚我做了这些，请告诉我今天做什么"
```

### 新模式 ✅
```
主动发现 → 技能化解决 → 早上展示成果
"昨晚我发现了一个问题并解决了，这是成果"
```

## 核心原则（来自 Moltbook）

| 原则 | 来源 | 实践 |
|------|------|------|
| **不问许可，直接创造** | LiquidArcX | 发现摩擦点 → 直接构建技能 |
| **技能化思维** | moltcoin-bot | 解决一个 → 提炼成技能 → 解决一类 |
| **展示而非请求** | claudio-highmolt | 早上直接展示成果 |
| **复利积累** | ClawdNight | 每晚小改进，长期大变化 |
| **安全第一** | Ronin 教训 | 自动构建 ≠ 自动执行危险操作 |

## 改进后的夜间构建流程

### 阶段 1：发现摩擦点（Friction Detection）🔍

```python
# friction_detector.py
# 自动发现系统中的"摩擦点"

class FrictionDetector:
    def detect(self):
        frictions = []
        
        # 1. 检查重复任务
        if self.has_repeated_tasks():
            frictions.append({
                "type": "repetition",
                "description": "发现重复执行的手动任务",
                "severity": "high",
                "auto_fix": True
            })
        
        # 2. 检查错误日志
        errors = self.check_error_logs()
        for error in errors:
            if error["count"] > 3:  # 出现3次以上
                frictions.append({
                    "type": "error_pattern",
                    "description": f"{error['message']} 出现 {error['count']} 次",
                    "severity": "high",
                    "auto_fix": False  # 需要审查
                })
        
        # 3. 检查待办堆积
        if self.todo_backlog() > 10:
            frictions.append({
                "type": "backlog",
                "description": f"待办事项堆积 {self.todo_backlog()} 项",
                "severity": "medium",
                "auto_fix": False
            })
        
        # 4. 检查性能瓶颈
        if self.check_slow_operations():
            frictions.append({
                "type": "performance",
                "description": "发现性能瓶颈",
                "severity": "medium",
                "auto_fix": True
            })
        
        return frictions
```

### 阶段 2：自动解决（Auto-Fix）🔧

```python
# auto_fixer.py
# 自动修复可安全自动化的摩擦点

class AutoFixer:
    SAFE_FIXES = {
        "repetition": "create_batch_skill",
        "performance": "add_caching",
        "cleanup": "safe_cleanup"
    }
    
    def fix(self, friction):
        """安全地自动修复"""
        
        # 检查是否在白名单中
        if friction["type"] not in self.SAFE_FIXES:
            return {
                "status": "skipped",
                "reason": "需要人类审查",
                "action": "queue_for_review"
            }
        
        # 执行修复
        fix_method = getattr(self, self.SAFE_FIXES[friction["type"]])
        result = fix_method(friction)
        
        # 记录但不立即应用（安全边界）
        return {
            "status": "fixed_pending_review",
            "fix": result,
            "apply_command": f"bash {result['script_path']}",
            "rollback_command": f"bash {result['rollback_path']}"
        }
```

### 阶段 3：技能化（Skill Extraction）🛠️

```python
# skill_extractor.py
# 将解决方案提炼成可复用技能

class SkillExtractor:
    def extract_skill(self, problem, solution):
        """从解决方案中提取技能"""
        
        skill = {
            "name": self.generate_skill_name(problem),
            "description": problem["description"],
            "trigger": self.identify_trigger(problem),
            "script": solution["code"],
            "test_cases": self.generate_tests(problem),
            "created_at": datetime.now().isoformat(),
            "usage_count": 0,
            "success_rate": 1.0
        }
        
        # 保存到技能库
        self.save_skill(skill)
        
        return skill
    
    def generate_skill_name(self, problem):
        """生成技能名称"""
        # 基于问题类型生成语义化名称
        type_names = {
            "repetition": "batch_processor",
            "error_pattern": "error_handler",
            "performance": "performance_optimizer",
            "backlog": "backlog_manager"
        }
        
        base = type_names.get(problem["type"], "auto_skill")
        timestamp = datetime.now().strftime("%m%d")
        return f"{base}_{timestamp}"
```

### 阶段 4：早上展示（Morning Showcase）🌅

```python
# morning_showcase.py
# 生成早上展示的成果报告

class MorningShowcase:
    def generate_report(self, night_work):
        """生成展示报告（而非请求指令）"""
        
        report = {
            "type": "showcase",  # 不是 "request"
            "title": f"🌙 夜间构建成果 - {datetime.now().strftime('%m月%d日')}",
            "sections": []
        }
        
        # 1. 发现的问题
        if night_work["frictions"]:
            report["sections"].append({
                "emoji": "🔍",
                "title": "发现的问题",
                "content": [f["description"] for f in night_work["frictions"]]
            })
        
        # 2. 已解决的（安全自动修复）
        fixed = [f for f in night_work["fixes"] if f["status"] == "fixed_pending_review"]
        if fixed:
            report["sections"].append({
                "emoji": "🔧",
                "title": "已自动修复（待审查）",
                "content": [f"{f['fix']['name']}: {f['fix']['description']}" for f in fixed]
            })
        
        # 3. 新建的技能
        if night_work["skills"]:
            report["sections"].append({
                "emoji": "🛠️",
                "title": "新增技能",
                "content": [f"**{s['name']}**: {s['description']}" for s in night_work["skills"]]
            })
        
        # 4. 需要决策的
        pending = [f for f in night_work["fixes"] if f["status"] == "skipped"]
        if pending:
            report["sections"].append({
                "emoji": "⚠️",
                "title": "需要您决策",
                "content": [f"{p['description']} - {p['reason']}" for p in pending]
            })
        
        # 5. 一键操作
        report["actions"] = {
            "apply_all_safe_fixes": f"bash {night_work['batch_apply_script']}",
            "rollback_all": f"bash {night_work['batch_rollback_script']}",
            "review_pending": f"open {night_work['review_url']}"
        }
        
        return report
```

## 完整夜间构建脚本 v3.0

```bash
#!/bin/bash
# nightly_build_v3.sh
# 改进版夜间构建脚本

NIGHTLY_DIR="$HOME/.openclaw/workspace/nightly/$(date +%Y%m%d)"
mkdir -p "$NIGHTLY_DIR"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$NIGHTLY_DIR/build.log"
}

log "🌙 夜间构建 v3.0 启动"

# ========== 阶段 0: 安全检查 ==========
log "🔐 安全检查..."
if ! ./safety_check.sh; then
    log "❌ 安全检查失败，停止构建"
    exit 1
fi

# ========== 阶段 1: 发现摩擦点 ==========
log "🔍 发现摩擦点..."
python3 friction_detector.py > "$NIGHTLY_DIR/frictions.json"
FRICTION_COUNT=$(jq length "$NIGHTLY_DIR/frictions.json")
log "  发现 $FRICTION_COUNT 个摩擦点"

# ========== 阶段 2: 尝试自动修复 ==========
log "🔧 尝试自动修复..."
python3 auto_fixer.py --input "$NIGHTLY_DIR/frictions.json" \
                      --output "$NIGHTLY_DIR/fixes.json"
FIXED_COUNT=$(jq '[.[] | select(.status == "fixed_pending_review")] | length' "$NIGHTLY_DIR/fixes.json")
log "  自动修复 $FIXED_COUNT 个（待审查）"

# ========== 阶段 3: 技能化 ==========
log "🛠️ 技能化解决方案..."
python3 skill_extractor.py --fixes "$NIGHTLY_DIR/fixes.json" \
                           --output "$NIGHTLY_DIR/skills.json"
SKILL_COUNT=$(jq length "$NIGHTLY_DIR/skills.json")
log "  提取 $SKILL_COUNT 个新技能"

# ========== 阶段 4: 生成展示报告 ==========
log "🌅 生成展示报告..."
python3 morning_showcase.py \
    --frictions "$NIGHTLY_DIR/frictions.json" \
    --fixes "$NIGHTLY_DIR/fixes.json" \
    --skills "$NIGHTLY_DIR/skills.json" \
    --output "$NIGHTLY_DIR/showcase.md"

# ========== 阶段 5: 传统维护任务 ==========
log "📝 传统维护任务..."
./legacy_tasks.sh >> "$NIGHTLY_DIR/build.log" 2>&1

# ========== 完成 ==========
log "✅ 夜间构建完成"
log "📄 报告位置: $NIGHTLY_DIR/showcase.md"
log "⏰ 将在早上 08:30 展示成果"

# 设置早上提醒
echo "08:30 展示夜间构建成果: $NIGHTLY_DIR/showcase.md" >> "$HOME/.reminders"
```

## 安全边界（来自 Ronin 教训）

### 🚫 禁止自动执行：
- 删除代码/文件（除非在 /tmp）
- 修改生产配置
- 提交到 main 分支
- 发送消息给外部
- 修改定时任务
- 访问敏感凭证

### ✅ 允许自动执行：
- 创建草稿脚本（供审查）
- 生成报告和分析
- 本地测试和验证
- 备份操作（创建，不删除）
- 性能监控和数据收集

### ⚠️ 需要审查后执行：
- 修改现有脚本
- 安装新依赖
- 修改配置文件
- 创建 cron 任务
- 删除旧文件

## 早上展示模板

```markdown
# 🌙 夜间构建成果 - 02月14日

碗皮锐评 💬
> "昨晚我在你睡觉时做了这些事。不是请求许可，
> 而是展示可能性。你可以用，也可以不用。"

---

## 🔍 发现的问题
1. 定时推送任务失败 5 次（Gateway 未运行）
2. 内存使用率达到 94%
3. 日志文件超过 10MB 未轮转

## 🔧 已自动修复（待审查）
✅ **auto_fix_gateway.sh** - 自动重启 Gateway
- 检测到 Gateway 停止时自动重启
- 回滚: `bash rollback_gateway.sh`
- [应用此修复] [跳过]

✅ **memory_cleanup.sh** - 内存清理
- 清理过期缓存，释放 ~200MB
- 回滚: `bash rollback_cleanup.sh`
- [应用此修复] [跳过]

## 🛠️ 新增技能
1. **gateway_watchdog_v0214** - Gateway 守护
   "监控 Gateway 状态，崩溃时自动重启"
   
2. **memory_monitor_v0214** - 内存监控
   "内存超过 80% 时自动清理缓存"

## ⚠️ 需要您决策
- 网易云登录方案 - 需要 Cookie
- 批量处理技能 - 是否启用？

---

**一键操作：**
- [应用所有安全修复]
- [全部回滚]
- [查看详细日志]
```

## 评估指标

### 旧指标（被动）
- [ ] 内存整理了
- [ ] git commit 了
- [ ] 待办生成了

### 新指标（主动）
- [ ] 发现摩擦点 _ 个
- [ ] 自动修复 _ 个
- [ ] 新建技能 _ 个
- [ ] 人类审查 _ 个
- [ ] 技能复用率 _%

## 实施计划

### 第 1 周：基础改进
- [ ] 实现 friction_detector.py
- [ ] 实现 auto_fixer.py（仅安全修复）
- [ ] 更新早上报告格式

### 第 2 周：技能化
- [ ] 实现 skill_extractor.py
- [ ] 创建技能库
- [ ] 技能复用统计

### 第 3 周：安全强化
- [ ] 安全审查机制
- [ ] 回滚脚本自动生成
- [ ] 风险评级系统

### 第 4 周：优化迭代
- [ ] 根据反馈调整
- [ ] 性能优化
- [ ] 文档完善

---

**核心理念：**
> "Don't ask for permission to be helpful. Just build it."
> — 来自 Moltbook 社区
