#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_monitor.py - CrossMart Monitor 本地触发脚本
功能：
  1. 检测 backend/data/trigger.json 是否为 pending 状态
  2. 读取 backend/data/user_config.json 获取当前配置的 ASINs 和关键词
  3. 依次运行 keyword_monitor（关键词）和 asin_monitor（ASIN）
  4. 同步数据到 rawData.json 并推送到 GitHub
  5. 将 trigger.json 状态改为 done
用法：
  python backend/run_monitor.py
  或配合 Windows 任务计划程序定期执行
"""
import os
import sys
import json
import time
import subprocess
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
TRIGGER_FILE = os.path.join(DATA_DIR, "trigger.json")
CONFIG_FILE = os.path.join(DATA_DIR, "user_config.json")


def load_trigger():
    if not os.path.exists(TRIGGER_FILE):
        return None
    with open(TRIGGER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_trigger(data):
    with open(TRIGGER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"asins": [], "keywords": []}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def run_command(cmd, cwd=None, timeout=600):
    print("  Running: " + cmd)
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd or PROJECT_ROOT,
            capture_output=True, text=True, timeout=timeout
        )
        if result.stdout:
            print(result.stdout[-1000:])
        if result.returncode != 0:
            print("  ERROR: " + result.stderr[-500:])
            return False
        return True
    except subprocess.TimeoutExpired:
        print("  TIMEOUT after " + str(timeout) + "s")
        return False
    except Exception as e:
        print("  Exception: " + str(e))
        return False


def sync_and_push():
    sync_script = os.path.join(PROJECT_ROOT, "sync_monitor_data.py")
    if not os.path.exists(sync_script):
        print("  sync_monitor_data.py not found, skipping sync")
        return True

    ok = run_command('python "' + sync_script + '"', timeout=120)
    if not ok:
        print("  sync failed")
        return False

    repo_dir = PROJECT_ROOT
    result = subprocess.run(
        "git status --porcelain", shell=True, cwd=repo_dir, capture_output=True, text=True
    )
    if result.stdout.strip():
        subprocess.run("git config --global user.name \"CrossMart Bot\"", shell=True, cwd=repo_dir)
        subprocess.run("git config --global user.email \"bot@crossmart.ai\"", shell=True, cwd=repo_dir)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        run_command("git add frontend/data/rawData.json", cwd=repo_dir, timeout=15)
        run_command("git commit -m \"auto: sync rawData " + ts + "\"", cwd=repo_dir, timeout=30)
        run_command("git push", cwd=repo_dir, timeout=60)
        print("  rawData.json pushed to GitHub")
    else:
        print("  No data changes to push")
    return True


def run_monitor():
    sep = "=" * 60
    print("\n" + sep)
    print("CrossMart Monitor - 本地触发执行")
    print("时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(sep)

    trigger = load_trigger()
    if trigger is None:
        print("trigger.json 不存在，请先在 monitor.html 上点击'立即抓取'")
        return

    if trigger.get("status") != "pending":
        print("触发器状态: " + str(trigger.get("status")) + "，无需执行")
        return

    print("检测到 pending 触发器，上次触发时间: " + str(trigger.get("triggered_at")))

    config = load_config()
    asins = config.get("asins", [])
    keywords = config.get("keywords", [])
    print("配置: " + str(len(asins)) + " 个 ASIN, " + str(len(keywords)) + " 个关键词")

    for kw_entry in keywords:
        kw = kw_entry.get("main", "").strip()
        if not kw:
            continue
        print("\n--- 关键词监控: " + kw + " ---")
        ok = run_command(
            "python -m browser.keyword_monitor \"" + kw + "\"",
            cwd=os.path.join(PROJECT_ROOT, "backend"),
            timeout=300
        )
        if not ok:
            print("  关键词 " + kw + " 执行失败，继续下一个")

    for asin_entry in asins:
        asin = asin_entry.get("main", "").strip()
        if not asin:
            continue
        print("\n--- ASIN 监控: " + asin + " ---")
        ok = run_command(
            "python -m browser.asin_monitor \"" + asin + "\"",
            cwd=os.path.join(PROJECT_ROOT, "backend"),
            timeout=300
        )
        if not ok:
            print("  ASIN " + asin + " 执行失败，继续下一个")

    print("\n--- 同步数据 ---")
    sync_and_push()

    trigger["status"] = "done"
    trigger["completed_at"] = datetime.now().isoformat()
    save_trigger(trigger)
    print("\n" + sep)
    print("监控完成！状态已更新为 done")
    print(sep)


if __name__ == "__main__":
    run_monitor()