#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_monitor.py - 跨境电商 ASIN 监控系统入口
带反检测随机化：
  - 时间窗口内随机延迟启动
  - 70% 执行概率（模拟人类惰性）
  - ASIN/关键词顺序打乱
  - 执行前先浏览无关页面
"""
import os
import sys
import json
import time
import random
import subprocess
import urllib.request
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data")
TRIGGER_FILE = os.path.join(DATA_DIR, "trigger.json")
CONFIG_FILE = os.path.join(DATA_DIR, "user_config.json")
REPO = "charlescome1995-prog/crossmart-monitor"

# 默认时间窗口配置（无 schedule 配置时使用）
DEFAULT_SCHEDULE = {
    "morning": {
        "anchor": "05:00",
        "window_start": "05:00",
        "window_end": "06:00",
        "jitter_max_minutes": 30,
        "run_probability": 0.7
    },
    "midday": {
        "anchor": "11:00",
        "window_start": "11:00",
        "window_end": "12:00",
        "jitter_max_minutes": 30,
        "run_probability": 0.7
    },
    "evening": {
        "anchor": "21:00",
        "window_start": "21:00",
        "window_end": "22:00",
        "jitter_max_minutes": 30,
        "run_probability": 0.7
    }
}


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
        return {"asins": [], "keywords": [], "schedule": DEFAULT_SCHEDULE}
    return data


def _safe_print(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('gbk', errors='replace').decode('gbk'))


def now_in_window(window_start, window_end):
    """检查当前时间是否在窗口内（时间格式 HH:MM）"""
    now = datetime.now()
    current_min = now.hour * 60 + now.minute
    start_parts = window_start.split(":")
    end_parts = window_end.split(":")
    start_min = int(start_parts[0]) * 60 + int(start_parts[1])
    end_min = int(end_parts[0]) * 60 + int(end_parts[1])
    return start_min <= current_min <= end_min


def wait_random(max_minutes, label=""):
    """随机等待（模拟人类不确定感）"""
    wait = random.randint(0, max_minutes)
    if wait > 0:
        print(f"  [{label}] 随机等待 {wait} 分钟...")
        time.sleep(wait * 60)


def should_run(slot_config):
    """掷骰子：是否真正执行"""
    prob = slot_config.get("run_probability", 1.0)
    roll = random.random()
    execute = roll < prob
    print(f"  掷骰子结果: {roll:.3f} {'>= ' if not execute else '< '}{prob:.1f} → {'执行' if execute else '跳过'}")
    return execute


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
    subprocess.run("git config --global user.name \"CrossMart Bot\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run("git config --global user.email \"bot@crossmart.ai\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
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


def browse_unrelated_pages():
    """Phase 0: 浏览无关页面，模拟人类行为"""
    print("  [Phase 0] 人类行为模拟：先逛几个无关页面...")
    urls = [
        "https://www.amazon.com",
        "https://www.amazon.com/gp/bestsellers/",
    ]
    random.shuffle(urls)
    for url in urls[:2]:
        print(f"  浏览: {url}")
        # 模拟人类行为：随机等待 3-8 秒
        time.sleep(random.randint(3, 8))


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
    schedule = config.get("schedule", DEFAULT_SCHEDULE)
    print("配置: " + str(len(asins)) + " 个 ASIN, " + str(len(keywords)) + " 个关键词")

    # ---- 确定当前时间段 ----
    now = datetime.now()
    current_slot = None
    current_time_str = now.strftime("%H:%M")

    # 找当前时间落在哪个窗口
    for slot_name, slot_cfg in schedule.items():
        ws = slot_cfg["window_start"]
        we = slot_cfg["window_end"]
        ws_min = int(ws.split(":")[0]) * 60 + int(ws.split(":")[1])
        we_min = int(we.split(":")[0]) * 60 + int(we.split(":")[1])
        cur_min = now.hour * 60 + now.minute
        if ws_min <= cur_min <= we_min:
            current_slot = slot_name
            break

    if current_slot is None:
        print("当前时间 " + current_time_str + " 不在任何执行窗口内，退出")
        return

    slot_config = schedule[current_slot]
    print(f"\n当前窗口: {current_slot} ({slot_config['window_start']}-{slot_config['window_end']})")

    # ---- 掷骰子：是否执行 ----
    if not should_run(slot_config):
        print("本次不执行（随机跳过）")
        return

    # ---- 随机延迟 ----
    jitter_max = slot_config.get("jitter_max_minutes", 30)
    wait_random(jitter_max, label=current_slot)

    # ---- Phase 0: 人类行为模拟 ----
    browse_unrelated_pages()

    # ---- 打乱顺序 ----
    random.shuffle(keywords)
    random.shuffle(asins)

    # ---- Phase A: 关键词监控 ----
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
        # 抓取间隔随机化
        time.sleep(random.randint(15, 40))

    # ---- Phase B: ASIN 监控 ----
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
        # 抓取间隔随机化
        time.sleep(random.randint(20, 50))

    # ---- Phase C: 同步推送 ----
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