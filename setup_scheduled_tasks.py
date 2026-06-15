#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_scheduled_tasks.py
在 Windows 任务计划程序中创建 CrossMart Monitor 定时任务
每天 08:00 和 17:30 自动运行 reset_and_run.py
"""
import subprocess
import sys
import os
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_EXE = sys.executable
RESET_AND_RUN = os.path.join(PROJECT_ROOT, "reset_and_run.py")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def get_uuid():
    """生成唯一的任务名称"""
    return "CrossMartMonitor"

def create_task(time_h, time_m, label):
    task_name = get_uuid()
    log_file = os.path.join(LOG_DIR, f"monitor_{time_h:02d}{time_m:02d}.log")

    # 将 Python 脚本包装成 bat 文件（避免任务计划程序编码问题）
    bat_path = os.path.join(PROJECT_ROOT, f"_run_{time_h:02d}{time_m:02d}.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(f"""@echo off\r
chcp 65001 >nul 2>&1\r
cd /d "{PROJECT_ROOT}"\r
"{PYTHON_EXE}" "{RESET_AND_RUN}" >> "{log_file}" 2>&1\r
""")

    # 创建任务计划程序任务
    # /SC DAILY = 每天 /TR = 任务操作 /ST = 启动时间 /RU = 运行账户
    cmd = [
        "schtasks",
        "/Create",
        "/TN", task_name + f"_{label}",
        "/TR", f'"{bat_path}"',
        "/SC", "DAILY",
        "/ST", f"{time_h:02d}:{time_m:02d}",
        "/F"  # 强制覆盖已存在的任务
    ]
    print("执行: " + " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
    return result.returncode == 0 or "已存在" in result.stderr or "already exists" in result.stderr.lower()

def main():
    print("=" * 50)
    print("CrossMart Monitor 定时任务设置")
    print("时间: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 50)

    tasks = [
        (8, 0, "morning"),
        (17, 30, "evening"),
    ]

    for h, m, label in tasks:
        label_str = f"{h:02d}:{m:02d}"
        print(f"\n--- 创建任务: 每天 {label_str} ---")
        ok = create_task(h, m, label)
        if ok:
            print(f"  ✓ 任务 {label_str} 创建成功")
        else:
            print(f"  ✗ 任务 {label_str} 创建失败")

    print("\n" + "=" * 50)
    print("完成！查看当前任务列表：")
    print("  schtasks /Query /TN \"CrossMartMonitor\"")
    print("\n删除所有任务：")
    print("  schtasks /Delete /TN \"CrossMartMonitor_morning\" /F")
    print("  schtasks /Delete /TN \"CrossMartMonitor_evening\" /F")
    print("=" * 50)

if __name__ == "__main__":
    main()
