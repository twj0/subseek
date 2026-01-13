#!/usr/bin/env python3
"""
独立的中国代理收集脚本

该脚本专门用于收集中国代理，保存到data文件夹供主程序使用
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.collectors.china_proxies import get_china_proxy_links
from src.utils.proxy_tester import test_china_proxies
from src.utils.protocol_converter import convert_china_proxies

def save_china_proxies_to_file(proxies, filename="china_proxies.txt"):
    """保存中国代理到文件"""
    data_dir = Path("data/china_proxies")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = data_dir / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for proxy in proxies:
            f.write(f"{proxy}\n")
    
    print(f"保存了 {len(proxies)} 个代理到 {file_path}")
    return str(file_path)

def save_china_proxies_json(proxies, stats, filename="china_proxies.json"):
    """保存中国代理和统计信息到JSON文件"""
    data_dir = Path("data/china_proxies")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = data_dir / filename
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "total_collected": len(proxies),
        "stats": stats,
        "proxies": proxies
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"保存了代理数据和统计信息到 {file_path}")
    return str(file_path)

def save_working_proxies(working_proxies, filename="working_china_proxies.txt"):
    """保存可用的中国代理到文件"""
    data_dir = Path("data/china_proxies")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = data_dir / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for proxy in working_proxies:
            f.write(f"{proxy}\n")
    
    print(f"保存了 {len(working_proxies)} 个可用代理到 {file_path}")
    return str(file_path)

def main():
    """主函数 - 独立的中国代理收集流程"""
    print("=" * 60)
    print("独立中国代理收集器")
    print("=" * 60)
    
    start_time = time.time()
    
    # 1. 收集中国代理
    print("\n🔍 步骤 1: 收集中国代理...")
    china_proxies = get_china_proxy_links()
    
    if not china_proxies:
        print("❌ 没有收集到任何中国代理")
        return
    
    print(f"✅ 收集到 {len(china_proxies)} 个中国代理")
    
    # 保存原始代理列表
    save_china_proxies_to_file(china_proxies, "raw_china_proxies.txt")
    
    # 2. 测试代理可用性
    print("\n🧪 步骤 2: 测试代理可用性...")
    
    # 从环境变量获取配置
    max_workers = int(os.environ.get("MAX_WORKERS", "10"))
    timeout = int(os.environ.get("PROXY_TEST_TIMEOUT", "10"))
    max_test_count = int(os.environ.get("MAX_TEST_COUNT", "50"))
    
    # 限制测试数量以节省时间
    test_proxies = china_proxies[:max_test_count] if len(china_proxies) > max_test_count else china_proxies
    
    print(f"准备测试 {len(test_proxies)} 个代理（最多 {max_test_count} 个）")
    print(f"配置: 并发={max_workers}, 超时={timeout}s")
    
    working_proxies, stats = test_china_proxies(
        test_proxies, 
        timeout=timeout, 
        max_workers=max_workers
    )
    
    print(f"✅ 测试完成: {len(working_proxies)}/{len(test_proxies)} 个代理可用")
    
    # 3. 协议转换
    print("\n🔄 步骤 3: 转换代理协议...")
    
    if working_proxies:
        # 获取目标协议配置
        target_protocols_str = os.environ.get("CHINA_PROXY_PROTOCOLS", "vmess,vless,ss")
        target_protocols = [p.strip() for p in target_protocols_str.split(',')]
        
        print(f"目标协议: {', '.join(target_protocols)}")
        
        converted_proxies = convert_china_proxies(working_proxies, target_protocols)
        
        print(f"✅ 转换完成: {len(working_proxies)} 个HTTP代理 -> {len(converted_proxies)} 个标准协议代理")
        
        # 保存转换后的代理
        save_china_proxies_to_file(converted_proxies, "converted_china_proxies.txt")
    else:
        converted_proxies = []
        print("⚠️  没有可用代理，跳过协议转换")
    
    # 4. 保存最终结果
    print("\n💾 步骤 4: 保存最终结果...")
    
    # 保存可用代理（供主程序使用）
    if working_proxies:
        save_working_proxies(working_proxies, "working_china_proxies.txt")
    
    # 保存详细统计信息
    stats_data = {
        "collection": {
            "total_collected": len(china_proxies),
            "tested": len(test_proxies),
            "working": len(working_proxies),
            "success_rate": len(working_proxies) / len(test_proxies) if test_proxies else 0
        },
        "conversion": {
            "original_working": len(working_proxies),
            "converted": len(converted_proxies),
            "target_protocols": target_protocols
        },
        "test_stats": stats
    }
    
    save_china_proxies_json(working_proxies, stats_data, "china_proxies_stats.json")
    
    # 5. 总结
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("📊 收集总结")
    print("=" * 60)
    print(f"⏱️  总耗时: {duration:.2f} 秒")
    print(f"📥 收集总数: {len(china_proxies)}")
    print(f"🧪 测试数量: {len(test_proxies)}")
    print(f"✅ 可用代理: {len(working_proxies)}")
    print(f"🔄 转换代理: {len(converted_proxies)}")
    print(f"📈 成功率: {len(working_proxies)/len(test_proxies)*100:.1f}%")
    
    # 生成主程序可用的配置文件
    config_data = {
        "timestamp": datetime.now().isoformat(),
        "working_proxies": working_proxies,
        "converted_proxies": converted_proxies,
        "stats": stats_data
    }
    
    config_file = save_china_proxies_json(working_proxies, config_data, "china_proxy_config.json")
    
    print(f"\n🎯 主程序配置文件: {config_file}")
    print("✅ 中国代理收集完成！主程序可以使用这些代理进行延迟测试。")

if __name__ == "__main__":
    main()
