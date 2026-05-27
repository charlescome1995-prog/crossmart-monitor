#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轮询 GitHub trigger.json 的脚本
每分钟检查一次 GitHub 上 backend/data/trigger.json 是否有新触发
有的话执行本地 monitor，然后发飞书通知
"""
import sys, os, json, time, requests, subprocess

sys.stdout.reconfigure(encoding='utf-8')

REPO = "charlescome1995-prog/crossmart-monitor"
TRIGGER_PATH = "backend/data/trigger.json"
TRIGGER_URL = f"https://api.github.com/repos/{REPO}/contents/{TRIGGER_PATH}"
LOCAL_TIMESTAMP_FILE = os.path.join(os.path.dirname(__file__), "data", "last_trigger_timestamp.txt")

GH_TOKEN = os.environ.get("GH_TOKEN", "")
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")

HEADERS = {
    "Authorization": f"token {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "crossmart-monitor-poll/1.0",
}

POLL_INTERVAL = 60


def get_local_timestamp():
    try:
        if os.path.exists(LOCAL_TIMESTAMP_FILE):
            with open(LOCAL_TIMESTAMP_FILE, "r") as f:
                return f.read().strip()
    except:
        pass
    return ""


def save_local_timestamp(ts):
    os.makedirs(os.path.dirname(LOCAL_TIMESTAMP_FILE), exist_ok=True)
    with open(LOCAL_TIMESTAMP_FILE, "w") as f:
        f.write(ts)


def fetch_trigger_from_github():
    if not GH_TOKEN:
        print("[WARN] GH_TOKEN not set")
        return None
    try:
        r = requests.get(TRIGGER_URL, headers=HEADERS, timeout=10)
        if r.status_code == 404:
            return None
        if r.ok:
            data = r.json()
            content = json.loads(__import__('base64').b64decode(data['content']))
            return {
                "content": content,
                "timestamp": content.get("timestamp", ""),
                "sha": data.get("sha", ""),
            }
    except Exception as e:
        print(f"[ERROR] fetch_trigger_from_github: {e}")
    return None


def run_monitor():
    print("[INFO] Running monitor...")
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "scheduler.py"), "--once"],
            capture_output=True, text=True, timeout=600
        )
        print(f"[MONITOR] done, returncode={result.returncode}")
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] run_monitor: {e}")
        return False


def send_feishu(message):
    if not FEISHU_WEBHOOK:
        print("[WARN] FEISHU_WEBHOOK not set")
        return
    try:
        requests.post(FEISHU_WEBHOOK, json={"msg_type": "text", "content": {"text": message}}, timeout=10)
    except Exception as e:
        print(f"[ERROR] send_feishu: {e}")


def clear_trigger_on_github(sha):
    try:
        empty_content = json.dumps({"triggered": False, "cleared": True})
        enc = __import__('base64').b64encode(empty_content.encode()).decode()
        r = requests.put(TRIGGER_URL, headers={**HEADERS, "Content-Type": "application/json"}, json={
            "message": "clear trigger after processing",
            "content": enc,
            "sha": sha,
        })
        return r.ok
    except Exception as e:
        print(f"[ERROR] clear_trigger_on_github: {e}")
        return False


def main():
    print(f"[POLL] Starting, interval={POLL_INTERVAL}s, repo={REPO}")
    while True:
        last_ts = get_local_timestamp()
        trigger = fetch_trigger_from_github()

        if trigger and trigger["content"].get("triggered") and trigger["timestamp"] != last_ts:
            ts = trigger["timestamp"]
            print(f"[TRIGGER] New trigger at {ts}")

            ok = run_monitor()
            send_feishu(f"{'✅' if ok else '❌'} 监控{'完成' if ok else '失败'}，触发时间: {ts}")
            save_local_timestamp(ts)
            clear_trigger_on_github(trigger["sha"])
        else:
            print(f"[POLL] No new trigger (last={last_ts})")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()