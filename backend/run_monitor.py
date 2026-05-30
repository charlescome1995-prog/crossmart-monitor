#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_monitor.py - 跨境电商 ASIN 监控系统入口
用法：
  python backend/run_monitor.py
"""
import os
import sys
import json
import time
import subprocess
import urllib.request
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data")
TRIGGER_FILE = os.path.join(DATA_DIR, "trigger.json")
CONFIG_FILE = os.path.join(DATA_DIR, "user_config.json")
REPO = "charlescome1995-prog/crossmart-monitor"


def gh_fetch_json(path):
    """从 GitHub API 下载 JSON（绕过CDN缓存）"""
    api_url = "https://api.github.com/repos/" + REPO + "/contents/" + path
    req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            import base64
            data = json.loads(r.read())
            content = base64.b64decode(data["content"]).decode("utf-8")
            return json.loads(content)
    except Exception as e:
        print("  fetch " + path + " error: " + str(e))
        return None


def load_trigger():
    return gh_fetch_json("backend/data/trigger.json")


def load_config():
    data = gh_fetch_json("backend/data/user_config.json")
    if data is None:
        return {"asins": [], "keywords": []}
    return data


def _safe_print(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('gbk', errors='replace').decode('gbk'))


def run_command(cmd_list, cwd=None, timeout=600):
    print("  Running: " + ' '.join(cmd_list))
    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['CDP_PORT'] = '9225'
        python_dir = os.path.dirname(sys.executable)
        env['PATH'] = python_dir + os.pathsep + env.get('PATH', '')
        if 'SYSTEMROOT' not in env:
            env['SYSTEMROOT'] = os.environ.get('SYSTEMROOT', r'C:\WINDOWS')
        result = subprocess.run(
            cmd_list, shell=False, cwd=cwd or PROJECT_ROOT,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout, env=env
        )
        if result.stdout:
            _safe_print(result.stdout[-2000:])
        if result.returncode != 0 and result.stderr:
            _safe_print("  STDERR: " + result.stderr[-500:])
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("  TIMEOUT after " + str(timeout) + "s")
        return False
    except Exception as e:
        print("  Exception: " + str(e))
        return False


def sync_and_push():
    sync_script = os.path.join(PROJECT_ROOT, "backend", "sync_monitor_data.py")
    if not os.path.exists(sync_script):
        print("  sync_monitor_data.py not found, skip sync")
        return True
    ok = run_command([sys.executable, sync_script], timeout=120)
    if not ok:
        print("  sync failed")
        return False
    repo_dir = PROJECT_ROOT
    subg = subprocess.run("git config --global user.name \"CrossMart Bot\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    subg = subprocess.run("git config --global user.email \"bot@crossmart.ai\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    result = subprocess.run("git status --porcelain", shell=True, cwd=repo_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.stdout.strip():
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        run_command(["git", "add", "frontend/data/rawData.json", "backend/data/keyword_related_asins.json"], cwd=repo_dir, timeout=15)
        run_command(["git", "commit", "-m", "auto: sync rawData " + ts], cwd=repo_dir, timeout=30)
        push_ok = run_command(["git", "push"], cwd=repo_dir, timeout=60)
        if not push_ok:
            print("  push rejected, force-push...")
            run_command(["git", "push", "-f"], cwd=repo_dir, timeout=60)
        print("  rawData.json + keyword_related_asins.json pushed")
    else:
        print("  No data changes to push")
    return True


def push_trigger_done(trigger):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TRIGGER_FILE, "w", encoding="utf-8") as f:
        json.dump(trigger, f, ensure_ascii=False, indent=2)
    repo_dir = PROJECT_ROOT
    subprocess.run("git config --global user.name \"CrossMart Bot\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run("git config --global user.email \"bot@crossmart.ai\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run("git add " + TRIGGER_FILE, shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run("git commit -m \"auto: trigger done\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    pr = subprocess.run("git push", shell=True, cwd=repo_dir, timeout=60, encoding="utf-8", errors="replace")
    if pr.returncode != 0:
        print("  force-pushing trigger...")
        subprocess.run("git push -f", shell=True, cwd=repo_dir, timeout=60, encoding="utf-8", errors="replace")
    print("  trigger.json pushed")


def run_monitor():
    sep = "=" * 60
    print("\n" + sep)
    print("CrossMart Monitor - 本地触发执行")
    print("时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(sep)

    trigger = load_trigger()
    if trigger is None:
        print("trigger.json 读取失败，请检查网络和仓库配置")
        return

    if trigger.get("status") != "pending":
        print("触发器状态: " + str(trigger.get("status")) + "，无需执行")
        return

    print("检测到 pending 触发器，上次触发: " + str(trigger.get("triggered_at")))

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
            [sys.executable, "-m", "browser.keyword_monitor", kw],
            cwd=os.path.join(PROJECT_ROOT, "backend"),
            timeout=300
        )
        if not ok:
            print("  关键词 " + kw + " 执行失败，继续")

    for asin_entry in asins:
        asin = asin_entry.get("main", "").strip()
        if not asin:
            continue
        print("\n--- ASIN 监控: " + asin + " ---")
        ok = run_command(
            [sys.executable, "-m", "browser.asin_monitor", asin],
            cwd=os.path.join(PROJECT_ROOT, "backend"),
            timeout=300
        )
        if not ok:
            print("  ASIN " + asin + " 执行失败，继续")

    print("\n--- 同步数据 ---")
    sync_and_push()

    trigger["status"] = "done"
    trigger["completed_at"] = datetime.now().isoformat()
    push_trigger_done(trigger)
    print("\n" + sep)
    print("监控完成！")
    print(sep)


if __name__ == "__main__":
    run_monitor()
