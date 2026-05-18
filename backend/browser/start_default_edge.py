#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动你的默认Edge（带所有缓存/收藏）并打开CDP端口
运行这个脚本，Edge会以你的默认账户启动+可被CDP控制
"""
import sys, os, subprocess, time

def main():
    edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    default_profile = r"C:\Users\OPENPC\AppData\Local\Microsoft\Edge\User Data"
    
    if not os.path.exists(edge_exe):
        # 找一下Edge在哪
        r = subprocess.run("where msedge", shell=True, capture_output=True, text=True)
        edge_exe = r.stdout.strip().split("\n")[0].strip() or edge_exe
    
    args = [
        edge_exe,
        f"--user-data-dir={default_profile}",
        "--remote-debugging-port=9222",
        "--remote-allow-origins=*",
        "--no-first-run",
    ]
    
    print("启动你的默认Edge...")
    print(f"  使用profile: {default_profile}")
    print(f"  CDP端口: 9222")
    subprocess.Popen(args)
    time.sleep(3)
    print("启动完成。你的Edge应该已打开，所有收藏夹/缓存都在。")
    print("检查一下Edge窗口是否正常，然后告诉我好了")

if __name__ == "__main__":
    main()
