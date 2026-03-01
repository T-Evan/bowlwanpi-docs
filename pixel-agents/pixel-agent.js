/**
 * Pixel Agent - 像素风格 AI 助手
 * 类似 VS Code 的虚拟代码伴侣
 */

class PixelAgent {
    constructor(config = {}) {
        this.config = {
            character: config.character || 'umaru',  // 角色类型
            size: config.size || 64,                  // 像素大小
            position: config.position || 'bottom-right',
            autoHide: config.autoHide !== false,
            ...config
        };
        
        this.state = 'idle';  // idle, typing, happy, sleep, working
        this.frame = 0;
        this.lastActivity = Date.now();
        this.canvas = null;
        this.ctx = null;
        this.animationId = null;
        
        this.sprites = {};
        this.currentAnimation = null;
        this.gridSize = 16;
        this.pixelSize = Math.max(2, Math.floor(this.config.size / this.gridSize));
        
        this.init();
    }
    
    init() {
        this.createCanvas();
        this.loadSprites();
        this.bindEvents();
        this.startAnimation();
        
        // 恢复上次状态
        const savedState = localStorage.getItem('pixelAgent_state');
        if (savedState) {
            this.state = savedState;
        }
    }
    
    createCanvas() {
        const canvas = document.createElement('canvas');
        canvas.id = 'pixel-agent';
        canvas.width = this.config.size;
        canvas.height = this.config.size;
        
        // 像素风格样式
        canvas.className = 'pixel-agent-canvas';
        canvas.style.cssText = `
            position: fixed;
            ${this.getPositionStyle()};
            width: ${this.config.size}px;
            height: ${this.config.size}px;
            image-rendering: pixelated;
            image-rendering: crisp-edges;
            cursor: pointer;
            z-index: 1000;
            transition: transform 0.3s ease;
        `;
        
        document.body.appendChild(canvas);
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        
        // 禁用平滑渲染，保持像素清晰
        this.ctx.imageSmoothingEnabled = false;
    }
    
    getPositionStyle() {
        const isMobile = window.matchMedia('(max-width: 768px)').matches;
        const positions = {
            'bottom-right': isMobile ? 'bottom: 84px; right: 12px;' : 'bottom: 88px; right: 20px;',
            'bottom-left': isMobile ? 'bottom: 84px; left: 12px;' : 'bottom: 88px; left: 20px;',
            'top-right': 'top: 20px; right: 20px;',
            'top-left': 'top: 20px; left: 20px;'
        };
        return positions[this.config.position] || positions['bottom-right'];
    }
    
    loadSprites() {
        // 小埋像素精灵图数据（16x16，强化帽兜/脸部/眼睛识别）
        this.sprites.umaru = {
            idle: [
                [
                    [0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],
                    [0,0,0,0,1,1,2,2,2,2,1,1,0,0,0,0],
                    [0,0,0,1,1,2,2,3,3,2,2,1,1,0,0,0],
                    [0,0,1,1,2,2,3,3,3,3,2,2,1,1,0,0],
                    [0,0,1,2,2,3,3,5,5,3,3,2,2,1,0,0],
                    [0,1,1,2,3,3,5,5,5,5,3,3,2,1,1,0],
                    [0,1,2,2,3,5,5,4,4,5,5,3,2,2,1,0],
                    [0,1,2,3,3,5,4,4,4,4,5,3,3,2,1,0],
                    [0,1,2,3,3,5,4,6,4,6,5,3,3,2,1,0],
                    [0,1,2,3,3,5,4,4,7,4,5,3,3,2,1,0],
                    [0,1,2,2,3,5,5,4,4,5,5,3,2,2,1,0],
                    [0,1,1,2,3,3,5,5,5,5,3,3,2,1,1,0],
                    [0,0,1,2,2,3,3,8,8,3,3,2,2,1,0,0],
                    [0,0,1,1,2,2,3,3,3,3,2,2,1,1,0,0],
                    [0,0,0,1,1,2,2,2,2,2,2,1,1,0,0,0],
                    [0,0,0,0,1,1,1,0,0,1,1,1,0,0,0,0]
                ],
                [
                    [0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],
                    [0,0,0,0,1,1,2,2,2,2,1,1,0,0,0,0],
                    [0,0,0,1,1,2,2,3,3,2,2,1,1,0,0,0],
                    [0,0,1,1,2,2,3,3,3,3,2,2,1,1,0,0],
                    [0,0,1,2,2,3,3,5,5,3,3,2,2,1,0,0],
                    [0,1,1,2,3,3,5,5,5,5,3,3,2,1,1,0],
                    [0,1,2,2,3,5,5,4,4,5,5,3,2,2,1,0],
                    [0,1,2,3,3,5,4,4,4,4,5,3,3,2,1,0],
                    [0,1,2,3,3,5,4,7,7,4,5,3,3,2,1,0],
                    [0,1,2,3,3,5,4,4,4,4,5,3,3,2,1,0],
                    [0,1,2,2,3,5,5,4,4,5,5,3,2,2,1,0],
                    [0,1,1,2,3,3,5,5,5,5,3,3,2,1,1,0],
                    [0,0,1,2,2,3,3,8,8,3,3,2,2,1,0,0],
                    [0,0,1,1,2,2,3,3,3,3,2,2,1,1,0,0],
                    [0,0,0,1,1,2,2,2,2,2,2,1,1,0,0,0],
                    [0,0,0,0,1,1,1,0,0,1,1,1,0,0,0,0]
                ]
            ],
            happy: [
                [
                    [0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],
                    [0,0,0,0,1,1,2,2,2,2,1,1,0,0,0,0],
                    [0,0,0,1,1,2,2,3,3,2,2,1,1,0,0,0],
                    [0,0,1,1,2,2,3,3,3,3,2,2,1,1,0,0],
                    [0,0,1,2,2,3,3,5,5,3,3,2,2,1,0,0],
                    [0,1,1,2,3,3,5,5,5,5,3,3,2,1,1,0],
                    [0,1,2,2,3,5,5,4,4,5,5,3,2,2,1,0],
                    [0,1,2,3,3,5,4,6,4,6,5,3,3,2,1,0],
                    [0,1,2,3,3,5,4,4,4,4,5,3,3,2,1,0],
                    [0,1,2,3,3,5,4,8,8,4,5,3,3,2,1,0],
                    [0,1,2,2,3,5,5,4,4,5,5,3,2,2,1,0],
                    [0,1,1,2,3,3,5,5,5,5,3,3,2,1,1,0],
                    [0,0,1,2,2,3,3,8,8,3,3,2,2,1,0,0],
                    [0,0,1,1,2,2,3,3,3,3,2,2,1,1,0,0],
                    [0,0,0,1,1,2,2,2,2,2,2,1,1,0,0,0],
                    [0,0,0,0,1,1,1,0,0,1,1,1,0,0,0,0]
                ]
            ],
            sleep: [
                [
                    [0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],
                    [0,0,0,0,1,1,2,2,2,2,1,1,0,0,0,0],
                    [0,0,0,1,1,2,2,3,3,2,2,1,1,0,0,0],
                    [0,0,1,1,2,2,3,3,3,3,2,2,1,1,0,0],
                    [0,0,1,2,2,3,3,5,5,3,3,2,2,1,0,0],
                    [0,1,1,2,3,3,5,5,5,5,3,3,2,1,1,0],
                    [0,1,2,2,3,5,5,4,4,5,5,3,2,2,1,0],
                    [0,1,2,3,3,5,4,7,7,4,5,3,3,2,1,0],
                    [0,1,2,3,3,5,4,4,4,4,5,3,3,2,1,0],
                    [0,1,2,3,3,5,4,4,4,4,5,3,3,2,1,0],
                    [0,1,2,2,3,5,5,4,4,5,5,3,2,2,1,0],
                    [0,1,1,2,3,3,5,5,5,5,3,3,2,1,1,0],
                    [0,0,1,2,2,3,3,8,8,3,3,2,2,1,0,0],
                    [0,0,1,1,2,2,3,3,3,3,2,2,1,1,0,0],
                    [0,0,0,1,1,2,2,2,2,2,2,1,1,0,0,0],
                    [0,0,0,0,1,1,1,0,0,1,1,1,0,0,0,0]
                ]
            ]
        };

        // 颜色映射（更接近小埋帽兜/发色）
        this.colors = {
            0: null,
            1: '#B95A1A',
            2: '#D87326',
            3: '#F29A3E',
            4: '#FBE0C8',
            5: '#F4C661',
            6: '#2F3746',
            7: '#C67B40',
            8: '#F2A3A3'
        };
    }
    
    drawPixel(x, y, color) {
        if (!color) return;
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x * this.pixelSize, y * this.pixelSize, this.pixelSize, this.pixelSize);
    }
    
    render() {
        // 清空画布
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 获取当前动画帧
        const animation = this.sprites[this.config.character][this.state];
        if (!animation) return;
        
        const frame = animation[this.frame % animation.length];
        
        // 绘制像素
        for (let y = 0; y < this.gridSize; y++) {
            for (let x = 0; x < this.gridSize; x++) {
                const colorIndex = frame[y][x];
                const color = this.colors[colorIndex];
                if (color) {
                    this.drawPixel(x, y, color);
                }
            }
        }
    }
    
    startAnimation() {
        const animate = () => {
            this.render();
            this.frame++;
            
            // 检查空闲状态
            this.checkIdleState();
            
            // 每秒 4 帧
            this.animationId = setTimeout(() => {
                requestAnimationFrame(animate);
            }, 250);
        };
        
        animate();
    }
    
    checkIdleState() {
        const idleTime = Date.now() - this.lastActivity;
        
        // 5分钟无操作进入睡眠
        if (idleTime > 300000 && this.state !== 'sleep') {
            this.setState('sleep');
        }
    }
    
    setState(newState) {
        if (this.state !== newState) {
            this.state = newState;
            this.frame = 0;
            localStorage.setItem('pixelAgent_state', newState);
            
            // 触发状态改变事件
            this.onStateChange(newState);
        }
    }
    
    onStateChange(state) {
        console.log(`[PixelAgent] State changed to: ${state}`);
        
        // 可以在这里添加音效、粒子效果等
        if (state === 'happy') {
            this.showParticles();
        }
    }
    
    showParticles() {
        // 简单的粒子效果
        const colors = ['#FFD700', '#FF6B6B', '#4ECDC4'];
        for (let i = 0; i < 5; i++) {
            setTimeout(() => {
                this.createParticle(colors[i % colors.length]);
            }, i * 100);
        }
    }
    
    createParticle(color) {
        const particle = document.createElement('div');
        particle.style.cssText = `
            position: fixed;
            width: 8px;
            height: 8px;
            background: ${color};
            left: ${this.canvas.getBoundingClientRect().left + this.config.size / 2}px;
            top: ${this.canvas.getBoundingClientRect().top}px;
            pointer-events: none;
            z-index: 1001;
            animation: pixelParticle 1s ease-out forwards;
        `;
        
        document.body.appendChild(particle);
        
        setTimeout(() => particle.remove(), 1000);
    }
    
    bindEvents() {
        // 点击交互
        this.canvas.addEventListener('click', () => {
            this.lastActivity = Date.now();
            
            if (this.state === 'sleep') {
                this.setState('happy');
                setTimeout(() => this.setState('idle'), 2000);
            } else {
                this.setState('happy');
                setTimeout(() => this.setState('idle'), 1000);
            }
            
            this.showMenu();
        });
        
        // 鼠标移动唤醒
        document.addEventListener('mousemove', () => {
            this.lastActivity = Date.now();
            if (this.state === 'sleep') {
                this.setState('idle');
            }
        });
        
        // 页面滚动
        document.addEventListener('scroll', () => {
            this.lastActivity = Date.now();
        });
        
        // 打字检测
        document.addEventListener('keydown', () => {
            this.lastActivity = Date.now();
            if (this.state !== 'sleep') {
                this.setState('typing');
                clearTimeout(this.typingTimeout);
                this.typingTimeout = setTimeout(() => {
                    this.setState('idle');
                }, 1000);
            }
        });
    }
    
    showMenu() {
        // 简单的快捷菜单
        const menu = document.createElement('div');
        menu.style.cssText = `
            position: fixed;
            ${this.config.position.includes('right') ? 'right: 90px;' : 'left: 90px;'}
            bottom: 20px;
            background: rgba(30, 41, 59, 0.95);
            border: 2px solid #FFD700;
            border-radius: 8px;
            padding: 8px;
            z-index: 1001;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #FFD700;
            image-rendering: pixelated;
        `;
        menu.innerHTML = `
            <div style="padding: 4px 8px; cursor: pointer; hover:background: rgba(255,215,0,0.2);">📊 查看状态</div>
            <div style="padding: 4px 8px; cursor: pointer;">🎮 游戏系统</div>
            <div style="padding: 4px 8px; cursor: pointer;">📸 生成自拍</div>
            <div style="padding: 4px 8px; cursor: pointer;">😴 晚安模式</div>
        `;
        
        document.body.appendChild(menu);
        
        setTimeout(() => menu.remove(), 5000);
    }
    
    destroy() {
        if (this.animationId) {
            clearTimeout(this.animationId);
        }
        if (this.canvas) {
            this.canvas.remove();
        }
    }
}

// 添加粒子动画 CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes pixelParticle {
        0% {
            transform: translateY(0) scale(1);
            opacity: 1;
        }
        100% {
            transform: translateY(-50px) scale(0);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// 导出
window.PixelAgent = PixelAgent;

// 自动初始化（如果页面有 data-pixel-agent 属性）
document.addEventListener('DOMContentLoaded', () => {
    if (document.body.dataset.pixelAgent !== 'false') {
        window.pixelAgent = new PixelAgent();
    }
});
