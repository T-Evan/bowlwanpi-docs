# Pixel Agents 博客实现方案

## 概念
在博客中添加像素风格的 AI 助手角色，类似 VS Code 的虚拟代码伴侣

## 实现功能

### 1. 像素角色系统 (Pixel Character)
- **小埋像素形象**：8-bit 风格的干物妹小埋角色
- **动画状态**：
  - idle：待机动画（呼吸、眨眼）
  - typing：打字时的专注表情
  - happy：完成任务时的开心动画
  - sleep：深夜模式时的睡觉动画

### 2. 交互反馈
- **代码高亮粒子**：阅读代码文章时，像素粒子效果
- **打字机效果**：文字逐字显示，带像素光标
- **成就解锁动画**：获得成就时的像素庆祝效果

### 3. 位置与行为
- **右下角悬浮**：类似 VS Code 的右下角助手
- **智能提示**：
  - 长时间未操作：打瞌睡动画
  - 滚动页面：跟随视线移动
  - 点击交互：弹出快捷菜单

### 4. 技术实现
- **Canvas API**：绘制像素图形
- **Sprite Sheet**：精灵图动画
- **CSS Pixel Art**：纯 CSS 像素风格
- **LocalStorage**：记住用户偏好

## 文件结构
```
docs/pixel-agents/
├── pixel-character.js      # 核心角色类
├── animations/             # 动画数据
│   ├── idle.json
│   ├── typing.json
│   ├── happy.json
│   └── sleep.json
├── sprites/                # 精灵图
│   └── umaru-sprite.png
├── styles.css              # 像素风格样式
└── demo.html               # 演示页面
```

## 集成到博客
1. 添加到主页右下角
2. 与游戏系统联动（经验值、成就）
3. 日记页面专属互动
4. 响应用户操作（点击、滚动、停留）
