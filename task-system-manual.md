# 任务生命周期管理系统 - 使用手册

## 系统概述

本系统实现完整的任务生命周期管理：
- **派发** → **执行** → **更新** → **检查** → **完成**

## 核心组件

| 组件 | 文件 | 用途 |
|-----|------|------|
| 任务管理器 | `task-manager.js` | 任务CRUD、状态管理 |
| 任务派发器 | `task-dispatcher.js` | 小碗皮派发任务 |
| 代理API | `task-agent-api.js` | 子代理更新状态 |
| 心跳检查 | `task-heartbeat.js` | 定时检查未完成任务 |

## 使用流程

### 1. 小碗皮派发任务

```bash
node scripts/task-dispatcher.js create "任务标题" "任务描述" 负责人 优先级 截止时间(小时)
```

**示例：**
```bash
node scripts/task-dispatcher.js create \
  "设计系统架构图" \
  "为新功能设计架构图并编写文档" \
  img_worker \
  p1 \
  24
```

**输出：**
```
✅ 任务已创建并分配

📋 任务信息:
  ID: TASK-20260307-001
  标题: 设计系统架构图
  负责人: img_worker
  优先级: P1
  状态: assigned

💡 子代理更新状态命令:
  node scripts/task-agent-api.js TASK-20260307-001 start
  node scripts/task-agent-api.js TASK-20260307-001 complete '{"result":"..."}'
  node scripts/task-agent-api.js TASK-20260307-001 block "原因"
```

### 2. 子代理更新状态

子代理收到任务后，使用 `task-agent-api.js` 更新状态：

```bash
# 开始执行
node scripts/task-agent-api.js TASK-20260307-001 start

# 更新进度
node scripts/task-agent-api.js TASK-20260307-001 progress 50

# 标记阻塞
node scripts/task-agent-api.js TASK-20260307-001 block "等待API密钥"

# 完成任务
node scripts/task-agent-api.js TASK-20260307-001 complete '{"deliverable":"/path/to/file"}'

# 标记失败
node scripts/task-agent-api.js TASK-20260307-001 fail "无法连接数据库"
```

### 3. 心跳自动检查

系统每分钟自动检查未完成任务：

**检查频率：**
- **P0 任务**（紧急）：30分钟检查一次
- **P1 任务**（重要）：2小时检查一次  
- **P2 任务**（普通）：4小时检查一次

**提醒规则：**
- 空闲时间超过检查间隔的2倍 → 发送提醒
- P0任务或逾期任务 → 立即发送紧急提醒
- 阻塞状态任务 → 询问需要的协助

### 4. 查看任务状态

```bash
# 列出所有任务
node scripts/task-dispatcher.js list

# 查看统计
node scripts/task-dispatcher.js stats
```

## 任务数据结构

```typescript
interface Task {
  id: string;              // 任务ID: TASK-YYYYMMDD-NNN
  title: string;           // 标题
  description: string;     // 描述
  assignee: string;        // 负责人
  priority: 'p0'|'p1'|'p2'; // 优先级
  status: 'pending'|'assigned'|'running'|'blocked'|'completed'|'failed';
  createdAt: number;       // 创建时间
  updatedAt: number;       // 更新时间
  deadline: number|null;   // 截止时间
  history: TaskHistory[];  // 状态变更历史
  result?: any;            // 完成结果
}
```

## 集成到工作流

### 心跳检查Cron配置

已配置每分钟检查：
```bash
# 查看cron配置
openclaw cron list

# 手动运行检查
node scripts/task-heartbeat.js
```

### 在子代理中集成

子代理可以在代码中调用API：

```javascript
const { agentStartTask, agentCompleteTask } = require('../scripts/task-agent-api');

// 开始任务
agentStartTask('TASK-20260307-001');

// 完成任务
agentCompleteTask('TASK-20260307-001', {
  deliverable: '/path/to/output',
  summary: '任务完成摘要'
});
```

## 最佳实践

### 1. 任务粒度

- **P0任务**：紧急修复、关键阻塞
- **P1任务**：功能开发、常规优化
- **P2任务**：文档整理、低优先级改进

### 2. 状态更新时机

- **开始执行时**：立即更新为 `start`
- **遇到阻塞时**：更新为 `block` 并说明原因
- **有阶段性进展时**：使用 `progress` 更新百分比
- **完成时**：使用 `complete` 并提交结果

### 3. 阻塞处理

任务阻塞时，应：
1. 立即更新状态为 `blocked`
2. 说明阻塞原因
3. 提出需要的协助
4. 等待协调后解除阻塞

## 文件位置

```
~/.openclaw/workspace/
├── scripts/
│   ├── task-manager.js      # 核心管理模块
│   ├── task-dispatcher.js   # 派发器
│   ├── task-agent-api.js    # 代理API
│   └── task-heartbeat.js    # 心跳检查
├── tasks/
│   ├── index.json           # 任务索引
│   ├── TASK-20260307-001.json
│   └── TASK-20260307-002.json
└── logs/
    └── task-agent-actions.log
```

## 故障排查

### 任务没有提醒

1. 检查任务状态：`node scripts/task-dispatcher.js list`
2. 检查心跳配置：`openclaw cron list`
3. 手动运行检查：`node scripts/task-heartbeat.js`

### 子代理无法更新状态

1. 确认任务ID正确
2. 检查任务文件是否存在：`ls ~/.openclaw/workspace/tasks/`
3. 查看错误日志：`cat ~/.openclaw/workspace/logs/task-agent-actions.log`

## 版本历史

- **v1.0** (2026-03-07): 初始版本，实现核心功能

---

*好工具胜过千言万语，清晰的任务管理让团队协作更高效* 📝
