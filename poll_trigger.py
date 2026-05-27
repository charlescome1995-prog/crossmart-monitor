#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轮询 GitHub trigger.json 的脚本
- 前端触发：写 trigger.json（包含 triggered_at + status: pending）
- poll_trigger.py 检测到新 trigger → 运行 monitor → 写 status: done/failed
- 前端轮询 trigger.json 的 status 字段，显示结果
"""
import sys, os, json, time, requests, subprocess, threading, base64
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.stdout.reconfigure(encoding='utf-8')

REPO = "charlescome1995-prog/crossmart-monitor"
TRIGGER_PATH = "backend/data/trigger.json"
TRIGGER_URL = f"https://api.github.com/repos/{REPO}/contents/{TRIGGER_PATH}"

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
            threading.Thread(target=immediate_trigger, daemon=True).start()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[HTTP] {format % args}")


def get_sha():
    """Get current SHA of trigger.json"""
    try:
        r = requests.get(TRIGGER_URL, headers=HEADERS, timeout=10)
        if r.ok:
            return r.json().get("sha", "")
    except:
        pass
    return ""


def write_trigger(status, triggered_at):
    """Write status back to trigger.json"""
    try:
        sha = get_sha()
        data = {"triggered_at": triggered_at, "status": status}
        enc = base64.b64encode(json.dumps(data).encode()).decode()
        r = requests.put(TRIGGER_URL, headers={**HEADERS, "Content-Type": "application/json"}, json={
            "message": f"set trigger status to {status}",
            "content": enc,
            "sha": sha,
        })
        return r.ok
    except Exception as e:
        print(f"[ERROR] write_trigger: {e}")
        return False


def immediate_trigger():
    print("[TRIGGER] Immediate trigger received")
    trigger = fetch_trigger()
    if not trigger:
        print("[WARN] No trigger file found")
        return
    ts = trigger["triggered_at"]
    ok = run_monitor()
    write_trigger("done" if ok else "failed", ts)
    send_feishu(f"{'✅' if ok else '❌'} 监控{'完成' if ok else '失败'}，触发时间: {ts}")
    print("[TRIGGER] Done")


def fetch_trigger():
    """Fetch trigger.json content"""
    if not GH_TOKEN:
        print("[WARN] GH_TOKEN not set")
        return None
    try:
        r = requests.get(TRIGGER_URL, headers=HEADERS, timeout=10)
        if r.status_code == 404:
            return None
        if r.ok:
            data = r.json()
            content = json.loads(base64.b64decode(data['content']).decode())
            return {
                "triggered_at": content.get("triggered_at", ""),
                "status": content.get("status", ""),
                "sha": data.get("sha", ""),
            }
    except Exception as e:
        print(f"[ERROR] fetch_trigger: {e}")
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


def start_http_server():
    print(f"[HTTP] Starting server on port {LOCAL_PORT}")
    server = HTTPServer(("127.0.0.1", LOCAL_PORT), TriggerHandler)
    server.serve_forever()


def clear_trigger():
    """Clear trigger.json after processing"""
    try:
        sha = get_sha()
        empty = json.dumps({"triggered": False, "status": "cleared"})
        enc = base64.b64encode(empty.encode()).decode()
        requests.put(TRIGGER_URL, headers={**HEADERS, "Content-Type": "application/json"}, json={
            "message": "clear trigger after processing",
            "content": enc,
            "sha": sha,
        })
    except Exception as e:
        print(f"[WARN] clear_trigger: {e}")


def main():
    print(f"[POLL] Starting, interval={POLL_INTERVAL}s, repo={REPO}")
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    last_seen_ts = ""

    while True:
        trigger = fetch_trigger()

        if trigger and trigger["status"] == "pending" and trigger["triggered_at"] != last_seen_ts:
            ts = trigger["triggered_at"]
            print(f"[TRIGGER] New trigger at {ts}")
            last_seen_ts = ts

            ok = run_monitor()
            write_trigger("done" if ok else "failed", ts)
            send_feishu(f"{'✅' if ok else '❌'} 监控{'完成' if ok else '失败'}，触发时间: {ts}")

            time.sleep(5)  # 给前端留出时间读取状态
            clear_trigger()
            last_seen_ts = ""  # 重置，允许下次触发
        else:
            if trigger:
                print(f"[POLL] trigger status={trigger['status']}, waiting...")
            else:
                print(f"[POLL] no trigger file")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()