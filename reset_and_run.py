#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reset_and_run.py - 重置触发器并运行监控
一键执行：先重置 trigger.json 为 pending，再运行 run_monitor.py
"""
import os
import sys
import json
import subprocess
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data")
TRIGGER_FILE = os.path.join(DATA_DIR, "trigger.json")
REPO = "charlescome1995-prog/crossmart-monitor"


def _safe_print(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('gbk', errors='replace').decode('gbk'))


def reset_trigger():
    """重置 trigger.json 为 pending"""
    os.makedirs(DATA_DIR, exist_ok=True)
    trigger = {
        "status": "pending",
        "triggered_at": datetime.now().isoformat(),
        "author": "local-scheduler"
    }
    with open(TRIGGER_FILE, "w", encoding="utf-8") as f:
        json.dump(trigger, f, ensure_ascii=False, indent=2)
    _safe_print("trigger.json 已重置为 pending")

    # commit and push
    repo_dir = PROJECT_ROOT
    subprocess.run("git config --global user.name \"CrossMart Bot\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run("git config --global user.email \"bot@crossmart.ai\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run("git add " + TRIGGER_FILE, shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run("git commit -m \"auto: reset trigger for local run\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    pr = subprocess.run("git push", shell=True, cwd=repo_dir, timeout=60, encoding="utf-8", errors="replace")
    if pr.returncode != 0:
        subprocess.run("git push -f", shell=True, cwd=repo_dir, timeout=60, encoding="utf-8", errors="replace")
    _safe_print("trigger.json 已推送")


def main():
    _safe_print("=" * 50)
    _safe_print("CrossMart Monitor - 重置并运行")
    _safe_print("时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    _safe_print("=" * 50)

    # Step 1: reset trigger
    reset_trigger()

    # Step 2: run monitor
    run_script = os.path.join(PROJECT_ROOT, "backend", "run_monitor.py")
    _safe_print("\n--- 开始执行监控 ---\n")
    result = subprocess.run(
        [sys.executable, run_script],
        cwd=PROJECT_ROOT,
        encoding="utf-8", errors="replace"
    )
    _safe_print("\n--- 监控进程结束 ---")
    _safe_print("=" * 50)


if __name__ == "__main__":
    main()