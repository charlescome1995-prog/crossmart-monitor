#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轮询 GitHub trigger.json 的脚本
- 每 60 秒检查 GitHub trigger.json 有没有新触发
- 同时暴露本地 HTTP 接口（:8765/trigger），收到请求立即执行 monitor
- 执行完发飞书通知，然后清空 GitHub trigger.json
"""
import sys, os, json, time, requests, subprocess, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.stdout.reconfigure(encoding='utf-8')

REPO = "charlescome1995-prog/crossmart-monitor"
TRIGGER_PATH = "backend/data/trigger.json"
TRIGGER_URL = f"https://api.github.com/repos/{REPO}/contents/{TRIGGER_PATH}"
LOCAL_TIMESTAMP_FILE = os.path.join(os.path.dirname(__file__), "data", "last_trigger_timestamp.txt")

GH_TOKEN = os.environ.get("GH_TOKEN", "")
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")
LOCAL_PORT = 8765

HEADERS = {
    "Authorization": f"token {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "crossmart-monitor-poll/1.0",
}

POLL_INTERVAL = 60


class TriggerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/trigger":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            # 异步触发，不卡住 HTTP 服务器
            threading.Thread(target=immediate_trigger, daemon=True).start()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[HTTP] {format % args}")


def immediate_trigger():
    """立即触发 monitor（不等轮询）"""
    print("[TRIGGER] Immediate trigger received")
    ok = run_monitor()
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    send_feishu(f"{'✅' if ok else '❌'} 监控{'完成' if ok else '失败'}，触发时间: {ts}")
    # 清空 GitHub trigger.json（忽略失败）
    trigger = fetch_trigger_from_github()
    if trigger:
        clear_trigger_on_github(trigger["sha"])
    print("[TRIGGER] Done")


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
            capture_output=True, text=True, timeout=600,
            env={**os.environ, "GH_TOKEN": GH_TOKEN, "FEISHU_WEBHOOK": FEISHU_WEBHOOK}
        )
        print(f"[MONITOR] done, returncode={result.returncode}")
        if result.stdout:
            print(f"[MONITOR stdout] {result.stdout[:500]}")
        if result.returncode != 0 and result.stderr:
            print(f"[MONITOR stderr] {result.stderr[:500]}")
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


def start_http_server():
    print(f"[HTTP] Starting server on port {LOCAL_PORT}")
    server = HTTPServer(("127.0.0.1", LOCAL_PORT), TriggerHandler)
    server.serve_forever()


def main():
    print(f"[POLL] Starting, interval={POLL_INTERVAL}s, repo={REPO}")
    # 启动 HTTP 服务器（独立线程）
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

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