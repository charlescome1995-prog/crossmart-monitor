#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reset_and_run.py - 重置触发器并运行监控（实时输出版）
一键执行：先重置 trigger.json 为 pending，再运行 run_monitor.py
输出实时写入日志文件
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
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
LOG_FILE = os.path.join(LOG_DIR, "monitor_reset_run.log")


def _safe_print(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('gbk', errors='replace').decode('gbk'))


def log_write(msg):
    """写入日志文件"""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass


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
    log_write("trigger.json reset to pending")

    # commit and push
    repo_dir = PROJECT_ROOT
    subprocess.run("git config --global user.name \"CrossMart Bot\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run("git config --global user.email \"bot@crossmart.ai\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run("git add " + TRIGGER_FILE, shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    cr = subprocess.run("git commit -m \"auto: reset trigger for local run\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace", capture_output=True)
    if cr.returncode != 0:
        log_write("git commit failed: " + str(cr.stderr))
    pr = subprocess.run("git push", shell=True, cwd=repo_dir, timeout=60, encoding="utf-8", errors="replace", capture_output=True)
    if pr.returncode != 0:
        subprocess.run("git push -f", shell=True, cwd=repo_dir, timeout=60, encoding="utf-8", errors="replace")
        log_write("git push forced")
    else:
        log_write("trigger.json pushed")
    _safe_print("trigger.json 已推送")


def main():
    header = "=" * 50 + "\n"
    header += "CrossMart Monitor - 重置并运行\n"
    header += "时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
    header += "=" * 50

    # 同时写 print 和日志
    _safe_print(header)
    log_write(header.replace("\n", " "))

    # 清空/创建日志（本次运行）
    log_write("=== Run started ===")

    # Step 1: reset trigger
    reset_trigger()

    # Step 2: run monitor with real-time output capture
    run_script = os.path.join(PROJECT_ROOT, "backend", "run_monitor.py")
    _safe_print("\n--- 开始执行监控 ---\n")
    log_write("Starting run_monitor.py ...")

    proc = subprocess.Popen(
        [sys.executable, run_script],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )

    # 实时读取并写入日志
    with open(LOG_FILE, "a", encoding="utf-8") as lf:
        for line in proc.stdout:
            lf.write(line)
            lf.flush()
            print(line.rstrip())

    proc.wait()
    rc = proc.returncode
    done_msg = f"\n--- 监控进程结束 (exit={rc}) ---"
    _safe_print(done_msg)
    log_write(done_msg)


if __name__ == "__main__":
    main()