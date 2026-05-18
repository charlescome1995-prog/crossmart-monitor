#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""初始化双浏览器"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cdp_bridge import init_profile, check_all_profiles

def main():
    status = check_all_profiles()
    for name, info in status.items():
        label = "A" if name == "amazon" else "B"
        ini = "已初始化" if info["initialized"] else "未初始化"
        print(f"Edge {label} ({name}): {ini}, port={info['port']}")

    # 先杀可能的旧进程（防止端口冲突）
    import subprocess
    subprocess.run("taskkill /f /im msedge.exe 2>nul", shell=True)
    import time; time.sleep(2)

    print("\n1/2 启动 Edge A (亚马逊)...")
    init_profile("amazon", open_url="https://www.amazon.com")

    print("\n2/2 启动 Edge B (卖家精灵)...")
    init_profile("sellersprite", open_url="https://www.sellersprite.com")

    print()
    print("=" * 50)
    print("两个Edge浏览器已启动！")
    print("Edge A (亚马逊)  → 不登录，保持中国地址")
    print("Edge B (卖家精灵) → 手动登录卖家精灵")
    print("准备好了告诉我")

if __name__ == "__main__":
    main()
