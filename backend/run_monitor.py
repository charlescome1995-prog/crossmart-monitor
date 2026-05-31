#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_monitor.py - 璺ㄥ鐢靛晢 ASIN 鐩戞帶绯荤粺鍏ュ彛
甯﹀弽妫€娴嬮殢鏈哄寲锛?  - 鏃堕棿绐楀彛鍐呴殢鏈哄欢杩熷惎鍔?  - 70% 鎵ц姒傜巼锛堟ā鎷熶汉绫绘儼鎬э級
  - ASIN/鍏抽敭璇嶉『搴忔墦涔?  - 鎵ц鍓嶅厛娴忚鏃犲叧椤甸潰
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

# 榛樿鏃堕棿绐楀彛閰嶇疆锛堟棤 schedule 閰嶇疆鏃朵娇鐢級
DEFAULT_SCHEDULE = {
    "morning": {
        "anchor": "06:20",
        "window_start": "06:20",
        "window_end": "07:20",
        "jitter_max_minutes": 30,
        "run_probability": 1.0
    },
    "midday": {
        "anchor": "06:30",
        "window_start": "06:30",
        "window_end": "07:30",
        "jitter_max_minutes": 30,
        "run_probability": 1.0
    },
    "evening": {
        "anchor": "06:40",
        "window_start": "06:40",
        "window_end": "07:40",
        "jitter_max_minutes": 30,
        "run_probability": 1.0
    }
}


def gh_fetch_json(path):
    """浠?GitHub API 涓嬭浇 JSON锛堢粫杩嘋DN缂撳瓨锛?""
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
    """妫€鏌ュ綋鍓嶆椂闂存槸鍚﹀湪绐楀彛鍐咃紙鏃堕棿鏍煎紡 HH:MM锛?""
    now = datetime.now()
    current_min = now.hour * 60 + now.minute
    start_parts = window_start.split(":")
    end_parts = window_end.split(":")
    start_min = int(start_parts[0]) * 60 + int(start_parts[1])
    end_min = int(end_parts[0]) * 60 + int(end_parts[1])
    return start_min <= current_min <= end_min


def wait_random(max_minutes, label=""):
    """闅忔満绛夊緟锛堟ā鎷熶汉绫讳笉纭畾鎰燂級"""
    wait = random.randint(0, max_minutes)
    if wait > 0:
        print(f"  [{label}] 闅忔満绛夊緟 {wait} 鍒嗛挓...")
        time.sleep(wait * 60)


def should_run(slot_config):
    """鎺烽瀛愶細鏄惁鐪熸鎵ц"""
    prob = slot_config.get("run_probability", 1.0)
    roll = random.random()
    execute = roll < prob
    print(f"  鎺烽瀛愮粨鏋? {roll:.3f} {'>= ' if not execute else '< '}{prob:.1f} 鈫?{'鎵ц' if execute else '璺宠繃'}")
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
    """Phase 0: 娴忚鏃犲叧椤甸潰锛屾ā鎷熶汉绫昏涓?""
    print("  [Phase 0] 浜虹被琛屼负妯℃嫙锛氬厛閫涘嚑涓棤鍏抽〉闈?..")
    urls = [
        "https://www.amazon.com",
        "https://www.amazon.com/gp/bestsellers/",
    ]
    random.shuffle(urls)
    for url in urls[:2]:
        print(f"  娴忚: {url}")
        # 妯℃嫙浜虹被琛屼负锛氶殢鏈虹瓑寰?3-8 绉?        time.sleep(random.randint(3, 8))


def run_monitor():
    sep = "=" * 60
    print("\n" + sep)
    print("CrossMart Monitor - 鏈湴瑙﹀彂鎵ц")
    print("鏃堕棿: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(sep)

    trigger = load_trigger()
    if trigger is None:
        print("trigger.json 璇诲彇澶辫触锛岃妫€鏌ョ綉缁滃拰浠撳簱閰嶇疆")
        return

    if trigger.get("status") != "pending":
        print("瑙﹀彂鍣ㄧ姸鎬? " + str(trigger.get("status")) + "锛屾棤闇€鎵ц")
        return

    print("妫€娴嬪埌 pending 瑙﹀彂鍣紝涓婃瑙﹀彂: " + str(trigger.get("triggered_at")))

    config = load_config()
    asins = config.get("asins", [])
    keywords = config.get("keywords", [])
    schedule = config.get("schedule", DEFAULT_SCHEDULE)
    print("閰嶇疆: " + str(len(asins)) + " 涓?ASIN, " + str(len(keywords)) + " 涓叧閿瘝")

    # ---- 纭畾褰撳墠鏃堕棿娈?----
    now = datetime.now()
    current_slot = None
    current_time_str = now.strftime("%H:%M")

    # 鎵惧綋鍓嶆椂闂磋惤鍦ㄥ摢涓獥鍙?    for slot_name, slot_cfg in schedule.items():
        ws = slot_cfg["window_start"]
        we = slot_cfg["window_end"]
        ws_min = int(ws.split(":")[0]) * 60 + int(ws.split(":")[1])
        we_min = int(we.split(":")[0]) * 60 + int(we.split(":")[1])
        cur_min = now.hour * 60 + now.minute
        if ws_min <= cur_min <= we_min:
            current_slot = slot_name
            break

    if current_slot is None:
        print("[BYPASS] 寮哄埗鎵ц妯″紡")
        current_slot = "morning"

    slot_config = schedule[current_slot]
    print(f"\n褰撳墠绐楀彛: {current_slot} ({slot_config['window_start']}-{slot_config['window_end']})")

    # ---- 鎺烽瀛愶細鏄惁鎵ц ----
    if not should_run(slot_config):
        print("鏈涓嶆墽琛岋紙闅忔満璺宠繃锛?)
        return

    # ---- 闅忔満寤惰繜 ----
    jitter_max = slot_config.get("jitter_max_minutes", 30)
    wait_random(jitter_max, label=current_slot)

    # ---- Phase 0: 浜虹被琛屼负妯℃嫙 ----
    browse_unrelated_pages()

    # ---- 鎵撲贡椤哄簭 ----
    random.shuffle(keywords)
    random.shuffle(asins)

    # ---- Phase A: 鍏抽敭璇嶇洃鎺?----
    for kw_entry in keywords:
        kw = kw_entry.get("main", "").strip()
        if not kw:
            continue
        print("\n--- 鍏抽敭璇嶇洃鎺? " + kw + " ---")
        ok = run_command(
            [sys.executable, "-m", "browser.keyword_monitor", kw],
            cwd=os.path.join(PROJECT_ROOT, "backend"),
            timeout=300
        )
        if not ok:
            print("  鍏抽敭璇?" + kw + " 鎵ц澶辫触锛岀户缁?)
        # 鎶撳彇闂撮殧闅忔満鍖?        time.sleep(random.randint(15, 40))

    # ---- Phase B: ASIN 鐩戞帶锛堜富ASIN + 鍏宠仈绔炲搧锛?---
    for asin_entry in asins:
        # 鎶撲富ASIN
        main_asin = asin_entry.get("main", "").strip()
        if main_asin:
            print("\n--- ASIN 鐩戞帶: " + main_asin + " ---")
            ok = run_command(
                [sys.executable, "-m", "browser.asin_monitor", main_asin],
                cwd=os.path.join(PROJECT_ROOT, "backend"),
                timeout=300
            )
            if not ok:
                print("  ASIN " + main_asin + " 鎵ц澶辫触锛岀户缁?)
            time.sleep(random.randint(20, 50))

        # 鎶撳叧鑱旂珵鍝丄SIN
        related_list = asin_entry.get("related", [])
        for rel_asin in related_list:
            rel_asin = rel_asin.strip()
            if not rel_asin:
                continue
            print("\n--- 鍏宠仈绔炲搧: " + rel_asin + " ---")
            ok = run_command(
                [sys.executable, "-m", "browser.asin_monitor", rel_asin],
                cwd=os.path.join(PROJECT_ROOT, "backend"),
                timeout=300
            )
            if not ok:
                print("  鍏宠仈ASIN " + rel_asin + " 鎵ц澶辫触锛岀户缁?)
            time.sleep(random.randint(20, 50))

    # ---- Phase C: 鍚屾鎺ㄩ€?----
    print("\n--- 鍚屾鏁版嵁 ---")
    sync_and_push()

    trigger["status"] = "done"
    trigger["completed_at"] = datetime.now().isoformat()
    push_trigger_done(trigger)
    print("\n" + sep)
    print("鐩戞帶瀹屾垚锛?)
    print(sep)


if __name__ == "__main__":
    run_monitor()