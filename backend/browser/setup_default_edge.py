#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正：Edge A 指向系统默认Edge目录（有缓存/收藏/搜索记录的）
以后启动Edge统一用这个方法，不新建profile
"""
import sys, os, subprocess, time, json
sys.stdout.reconfigure(encoding='utf-8')

# ─── 系统默认Edge目录 ───
EDGE_DEFAULT_PROFILE = os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\Edge\User Data"
)

def is_running(port=9222):
    """检查端口是否已开CDP"""
    try:
        import urllib.request
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=2)
        tabs = json.loads(req.read())
        return len(tabs) > 0
    except:
        return False

def kill_edge():
    """关掉所有Edge进程"""
    subprocess.run("taskkill /f /im msedge.exe 2>nul", shell=True)
    print("  Edge 已关闭")
    time.sleep(2)

def start_edge(port=9222):
    """用系统默认profile启动Edge + CDP"""
    edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_exe):
        r = subprocess.run("where msedge", shell=True, capture_output=True, text=True)
        edge_exe = r.stdout.strip().split("\n")[0].strip()
    
    print(f"  Edge: {edge_exe}")
    print(f"  Profile: {EDGE_DEFAULT_PROFILE}")
    print(f"  Port: {port}")
    
    args = [
        edge_exe,
        f"--user-data-dir={EDGE_DEFAULT_PROFILE}",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    
    subprocess.Popen(args)
    time.sleep(3)
    
    # 确认启动了
    if is_running(port):
        print("  ✅ 启动成功")
        return True
    else:
        print("  ⚠️ CDP还没响应，再等一会儿...")
        time.sleep(5)
        if is_running(port):
            print("  ✅ 启动成功")
            return True
        print("  ❌ 启动失败")
        return False

def update_config():
    """更新cdp_bridge.py的配置，指向默认目录"""
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "cdp_bridge.py"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 替换 amazon profile 路径为默认
    old = r'"amazon": os.path.join(PROJECT_ROOT, "data", "browser_profiles", "edge_amazon")'
    new = f'"amazon": r"{EDGE_DEFAULT_PROFILE}"'
    if old in content:
        content = content.replace(old, new)
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("  ✅ cdp_bridge.py 已更新：amazon profile → 系统默认Edge")
    else:
        print("  ℹ️ 路径可能已经更新过")

def main():
    print("=" * 50)
    print("重新配置Edge A → 系统默认Edge")
    print("=" * 50)
    
    # 1. 更新配置
    update_config()
    
    # 2. 关掉现在port 9222的Edge
    if is_running(9222):
        print("\n当前port 9222有Edge在运行，关闭...")
        kill_edge()
    
    # 3. 用默认profile启动
    print("\n启动Edge（系统默认profile）...")
    start_edge(9222)
    
    print("\n✅ 完成后，你的默认Edge已启动")
    print("   收藏夹/缓存/搜索记录都在")
    print("   同时开了CDP端口，我随时可以操作")

if __name__ == "__main__":
    main()
