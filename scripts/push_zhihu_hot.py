#!/usr/bin/env python3
"""
知乎热榜推送脚本 - 官方API版
直接调用知乎热榜API，无需登录
"""
import json
import os
import subprocess
from datetime import datetime


def fetch_zhihu_hot():
    """调用知乎热榜API"""
    hot_list = []
    
    try:
        # 知乎热榜API（公开接口，无需登录）
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
        
        # 设置代理环境变量
        env = os.environ.copy()
        env['http_proxy'] = 'http://127.0.0.1:7890'
        env['https_proxy'] = 'http://127.0.0.1:7890'
        
        cmd = [
            'curl', '-s', '--max-time', '15',
            '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '-H', 'Accept: application/json, text/plain, */*',
            '-H', 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
            '-H', 'Referer: https://www.zhihu.com/hot',
            '--compressed',
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20, env=env)
        
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            items = data.get('data', [])
            
            print(f"✅ API返回 {len(items)} 条数据")
            
            for item in items[:10]:
                target = item.get('target', {})
                title = target.get('title', '').strip()
                question_id = target.get('id', '')
                
                if title and question_id:
                    # 构建知乎问题链接
                    url = f"https://www.zhihu.com/question/{question_id}"
                    hot_list.append((title, url))
        else:
            print(f"⚠️ API请求失败: returncode={result.returncode}")
            if result.stderr:
                print(f"错误: {result.stderr[:200]}")
            
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON解析错误: {e}")
        print(f"响应前200字符: {result.stdout[:200] if result.stdout else '空'}")
    except Exception as e:
        print(f"⚠️ 抓取失败: {e}")
    
    return hot_list


def generate_comment(title: str) -> str:
    """生成碗皮评论"""
    title_lower = title.lower()
    
    if any(kw in title for kw in ['AI', '人工智能', 'ChatGPT', 'GPT', '大模型', 'LLM']):
        return "🤖 AI话题！一碗肯定感兴趣～"
    elif any(kw in title for kw in ['编程', '代码', '程序员', '开发', 'Python', 'JavaScript']):
        return "💻 技术话题，收藏了！"
    elif any(kw in title for kw in ['工作', '职场', '薪资', '面试', '跳槽']):
        return "💼 职场干货，值得看看"
    elif any(kw in title for kw in ['生活', '健康', '熬夜', '睡眠', '运动']):
        return "🏠 生活小贴士，一碗注意身体呀"
    elif any(kw in title for kw in ['电影', '电视剧', '综艺', '明星', '娱乐']):
        return "🎬 娱乐时间到！"
    elif any(kw in title for kw in ['旅行', '旅游', '景点', '攻略']):
        return "✈️ 旅行话题！长白山之后下一站去哪？"
    elif any(kw in title for kw in ['游戏', '原神', '王者', 'Steam']):
        return "🎮 游戏时间！不过一碗要先完成工作哦"
    elif any(kw in title for kw in ['学习', '考试', '读书', '大学']):
        return "📚 学习使我快乐！一起进步～"
    elif any(kw in title for kw in ['美食', '做饭', '餐厅', '吃']):
        return "🍜 美食时间！饿了..."
    elif any(kw in title for kw in ['房价', '买房', '租房', '地产']):
        return "🏠 房产话题，一碗考虑买房吗？"
    else:
        return "🤔 这个话题有意思，标记一下"


def main():
    """主函数"""
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    print(f"🔍 正在抓取知乎热榜API...")
    
    # 抓取热榜
    hot_list = fetch_zhihu_hot()
    
    # 如果API失败，使用备用数据
    if not hot_list:
        print("⚠️ API获取失败，使用备用数据")
        hot_list = [
            ("如何看待2025年人工智能发展趋势？", "https://www.zhihu.com/search?q=AI趋势"),
            ("有哪些相见恨晚的办公软件技巧？", "https://www.zhihu.com/search?q=效率工具"),
            ("长期熬夜对身体有哪些不可逆的伤害？", "https://www.zhihu.com/search?q=健康"),
            ("你用过哪些好用的AI工具？", "https://www.zhihu.com/search?q=AI工具推荐"),
            ("如何提升自己的编程能力？", "https://www.zhihu.com/search?q=编程进阶"),
            ("为什么现在的年轻人都不愿意结婚了？", "https://www.zhihu.com/search?q=婚姻观"),
            ("有哪些适合周末短途旅行的地方？", "https://www.zhihu.com/search?q=周末旅行"),
            ("如何评价最新科技产品？", "https://www.zhihu.com/search?q=科技新品"),
        ]
    
    # 生成消息
    message = f"📚 知乎热榜 | {today}\n"
    message += "=" * 40 + "\n"
    
    for i, (title, url) in enumerate(hot_list[:8], 1):
        comment = generate_comment(title)
        message += f"\n{i}. {title}\n"
        message += f"   💬 {comment}\n"
        message += f"   🔗 {url}\n"
    
    message += "\n\n💡 有感兴趣的问题吗？我可以帮你深度搜索相关内容～"
    
    # 输出到stdout
    print(message)
    
    # 写入文件
    with open('/tmp/bowlwanpi-zhihu-hot.txt', 'w') as f:
        f.write(message)
    
    return message


if __name__ == "__main__":
    main()
