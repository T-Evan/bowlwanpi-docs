#!/usr/bin/env python3
"""
重建手册生成器 - 自动创建并上传重建信息到记忆系统
用于定时更新重建手册，确保信息始终最新
"""

import json
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/memu-memory')
sys.path.insert(0, '/root/.openclaw/workspace/skills/unified-memory')

try:
    from unified_memory_manager import store_to_all_systems
except ImportError as e:
    print(f"⚠️ 无法导入 unified_memory_manager: {e}")
    store_to_all_systems = None

WORKSPACE = Path("/root/.openclaw/workspace")


def scan_capabilities():
    """扫描当前能力状态"""
    capabilities = {
        "timestamp": datetime.now().isoformat(),
        "skills": [],
        "mcp_services": [],
        "cron_jobs": [],
        "external_platforms": [],
        "memory_systems": [],
        "search_engines": []
    }
    
    # 扫描技能
    skills_dir = WORKSPACE / "skills"
    if skills_dir.exists():
        capabilities["skills"] = [d.name for d in skills_dir.iterdir() if d.is_dir()]
    
    # 扫描 MCP 服务（兼容历史路径）
    mcp_candidates = [
        WORKSPACE / "mcp_config.json",
        WORKSPACE / "config" / "mcp_config.json",
    ]
    for mcp_config in mcp_candidates:
        if not mcp_config.exists():
            continue
        try:
            with open(mcp_config) as f:
                config = json.load(f)
                capabilities["mcp_services"] = list(config.get("mcpServers", {}).keys())
                break
        except Exception:
            continue
    
    # 扫描定时任务
    try:
        import subprocess
        result = subprocess.run(
            ["openclaw", "cron", "list"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            # 简单解析输出
            capabilities["cron_jobs_count"] = result.stdout.count("name:")
    except:
        capabilities["cron_jobs_count"] = "unknown"
    
    # 检查记忆系统
    if (WORKSPACE / "skills" / "unified-memory").exists():
        capabilities["memory_systems"].append("unified-memory")
    if (WORKSPACE / "skills" / "memu-memory").exists():
        capabilities["memory_systems"].append("memu")
    if (WORKSPACE / "skills" / "hippocampus-memory").exists():
        capabilities["memory_systems"].append("hippocampus")
    
    # 检查搜索系统
    if (WORKSPACE / "skills" / "intelligent-search").exists():
        capabilities["search_engines"].append("intelligent-search")
    if (WORKSPACE / "skills" / "tencent-search").exists():
        capabilities["search_engines"].append("tencent-search")
    
    # 外部平台
    if (WORKSPACE / "secrets" / "moltbook-credentials.json").exists():
        capabilities["external_platforms"].append("moltbook")
    
    return capabilities


def generate_rebuild_summary(capabilities):
    """生成重建摘要"""
    summary = f"""🥣 BowlWanpi 重建摘要

生成时间: {capabilities['timestamp']}

## 当前能力状态

### 技能 ({len(capabilities['skills'])} 个)
"""
    
    for skill in capabilities['skills'][:10]:
        summary += f"- {skill}\n"
    if len(capabilities['skills']) > 10:
        summary += f"- ... 还有 {len(capabilities['skills']) - 10} 个技能\n"
    
    summary += f"""
### MCP 服务 ({len(capabilities['mcp_services'])} 个)
"""
    for service in capabilities['mcp_services']:
        summary += f"- {service}\n"
    
    summary += f"""
### 记忆系统
"""
    for mem in capabilities['memory_systems']:
        summary += f"- {mem}\n"
    
    summary += f"""
### 搜索引擎
"""
    for search in capabilities['search_engines']:
        summary += f"- {search}\n"
    
    summary += f"""
### 外部平台
"""
    for platform in capabilities['external_platforms']:
        summary += f"- {platform}\n"
    
    summary += """
## 重建关键信息

- Agent ID: dfc4fae2-ac13-4124-9bfe-6d12da5ec72f
- Moltbook: https://moltbook.com/u/BowlWanpi
- 重建脚本: ~/.openclaw/workspace/rebuild_bowlwanpi.py
- 检查清单: ~/.openclaw/workspace/REBUILD_CHECKLIST.md

## 备份位置

- 本地备份: /clawd-data/workspace-backup/
- Git备份: workspace/.git
- 云端记忆: memU API

---

本摘要由 rebuild-generator 自动生成
"""
    
    return summary


async def upload_to_memory(summary):
    """上传重建摘要到记忆系统"""
    if store_to_all_systems is None:
        print("❌ 无法导入记忆系统，跳过上传")
        return False
    
    try:
        result = await store_to_all_systems(
            user_msg="BowlWanpi 重建摘要 - 自动生成的能力快照",
            assistant_msg=summary,
            importance=0.9  # 高重要度
        )
        
        print("📤 上传到记忆系统:")
        print(f"  memU: {'✅' if result['memu'] else '❌'}")
        print(f"  Hippocampus: {'✅' if result['hippocampus'] else '❌'}")
        print(f"  MemOS: {'✅' if result['memos'] else '❌'}")
        
        return all(result.values())
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        return False


def save_local_copy(summary):
    """保存本地副本"""
    memory_dir = WORKSPACE / "memory"
    memory_dir.mkdir(exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    filename = memory_dir / f"rebuild-summary-{today}.md"
    
    with open(filename, 'w') as f:
        f.write(summary)
    
    print(f"💾 本地副本已保存: {filename}")
    return filename


async def main():
    """主函数"""
    print("="*60)
    print("🥣 BowlWanpi 重建手册生成器")
    print("="*60)
    print()
    
    # 1. 扫描能力
    print("🔍 扫描当前能力状态...")
    capabilities = scan_capabilities()
    print(f"  发现 {len(capabilities['skills'])} 个技能")
    print(f"  发现 {len(capabilities['mcp_services'])} 个 MCP 服务")
    print()
    
    # 2. 生成摘要
    print("📝 生成重建摘要...")
    summary = generate_rebuild_summary(capabilities)
    print("  ✅ 摘要生成完成")
    print()
    
    # 3. 保存本地副本
    local_file = save_local_copy(summary)
    print()
    
    # 4. 上传到记忆系统
    print("☁️ 上传到云端记忆系统...")
    success = await upload_to_memory(summary)
    print()
    
    # 5. 完成
    print("="*60)
    if success:
        print("✅ 重建手册生成并上传完成!")
    else:
        print("⚠️ 部分上传失败，但本地副本已保存")
    print("="*60)
    
    return 0 if success else 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
