#!/usr/bin/env python3
"""
睡眠提醒播报脚本
"""
from datetime import datetime

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"💤 睡眠提醒 | {today}")
    print("="*50)
    print()
    print("一碗～该睡觉啦！")
    print()
    print("🌙 明天再继续探索吧")
    print("   好好休息，做个好梦～")
    print()
    print("💭 碗皮也要去充电了")
    print("   明天见！晚安 💤")
    print()
    print("="*50)
    print("发送完成！")
