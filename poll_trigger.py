#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
poll_trigger.py - 轮询 GitHub trigger.json
- 前端触发：写 trigger.json（包含 triggered_at + status: pending）
- poll_trigger.py 检测到新 trigger → 同步配置 → 运行 monitor → 写 status: done/failed
- 前端轮询 trigger.json 的 status 字段，显示结果
"""
import sys, os, json, time, requests, subprocess, threading, base64
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.stdout.reconfigure(encoding='utf-8')

REPO = "charlescome1995-prog/crossmart-monitor"
TRIGGER_PATH = "backend/data/trigger.json"
CONFIG_PATH = "backend/data/user_config.json"
TRIGGER_URL = f"https://api.github.com/repos/{REPO}/contents/{TRIGGER_PATH}"
CONFIG_URL = f"https://api.github.com/repos/{REPO}/contents/{CONFIG_PATH}"

GH_TOKEN = os.environ.get("GH_TOKEN", "")
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")
LOCAL_PORT = 8765

HEADERS = {
    "Authorization": f"token {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "crossmart-monitor-poll/1.0",
}

POLL_INTERVAL = 60

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data")
MONITOR_LIST_PATH = os.path.join(DATA_DIR, "monitor_list.json")
KEYWORD_LIST_PATH = os.path.join(DATA_DIR, "keyword_list.json")

os.makedirs(DATA_DIR, exist_ok=True)


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


def get_sha(url):
    """Get current SHA of a file"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.ok:
            return r.json().get("sha", "")
    except:
        pass
    return ""


def write_trigger(status, triggered_at):
    """Write status back to trigger.json"""
    try:
        sha = get_sha(TRIGGER_URL)
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


def sync_config_from_github():
    """
    从 GitHub 读取 user_config.json，同步到本地 monitor_list.json 和 keyword_list.json
    """
    if not GH_TOKEN:
        print("[WARN] GH_TOKEN not set, skip config sync")
        return False
    try:
        r = requests.get(CONFIG_URL, headers=HEADERS, timeout=10)
        if r.status_code == 404:
            print("[WARN] user_config.json not found on GitHub")
            return False
        if not r.ok:
            print(f"[WARN] failed to fetch user_config: {r.status_code}")
            return False
        data = r.json()
        content = json.loads(base64.b64decode(data['content']).decode())
        print(f"[CONFIG] Got config from GitHub: {content}")

        # 写入本地文件（scheduler.py 期望 [{"asin": "..."}, ...] 格式）
        asins_data = []
        for a in content.get('asins', []):
            if a and a.strip():
                asins_data.append({"asin": a.strip(), "keywords": "", "nickname": ""})
        with open(MONITOR_LIST_PATH, 'w', encoding='utf-8') as f:
            json.dump(asins_data, f, ensure_ascii=False, indent=2)
        print(f"[CONFIG] Wrote {len(asins_data)} asins to monitor_list.json")

        # keyword_list 格式：{keyword, note, group}
        kw_list = []
        for kw in content.get('keywords', []):
            if kw and kw.strip():
                kw_list.append({"keyword": kw.strip(), "note": "", "group": "main"})
        with open(KEYWORD_LIST_PATH, 'w', encoding='utf-8') as f:
            json.dump(kw_list, f, ensure_ascii=False, indent=2)
        print(f"[CONFIG] Wrote {len(kw_list)} keywords to keyword_list.json")

        return True
    except Exception as e:
        print(f"[ERROR] sync_config_from_github: {e}")
        return False


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
            [sys.executable, os.path.join(PROJECT_ROOT, "scheduler.py"), "--once"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600,
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


def clear_trigger():
    """Clear trigger.json after processing"""
    try:
        sha = get_sha(TRIGGER_URL)
        empty = json.dumps({"triggered": False, "status": "cleared"})
        enc = base64.b64encode(empty.encode()).decode()
        requests.put(TRIGGER_URL, headers={**HEADERS, "Content-Type": "application/json"}, json={
            "message": "clear trigger after processing",
            "content": enc,
            "sha": sha,
        })
    except Exception as e:
        print(f"[WARN] clear_trigger: {e}")


def immediate_trigger():
    print("[TRIGGER] Immediate trigger received")
    trigger = fetch_trigger()
    if not trigger:
        print("[WARN] No trigger file found")
        return
    ts = trigger["triggered_at"]

    sync_config_from_github()
    ok = run_monitor()
    write_trigger("done" if ok else "failed", ts)
    send_feishu(f"{'✅' if ok else '❌'} 监控{'完成' if ok else '失败'}，触发时间: {ts}")
    print("[TRIGGER] Done")


def start_http_server():
    print(f"[HTTP] Starting server on port {LOCAL_PORT}")
    server = HTTPServer(("127.0.0.1", LOCAL_PORT), TriggerHandler)
    server.serve_forever()


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

            sync_config_from_github()
            ok = run_monitor()
            write_trigger("done" if ok else "failed", ts)
            send_feishu(f"{'✅' if ok else '❌'} 监控{'完成' if ok else '失败'}，触发时间: {ts}")

            time.sleep(5)
            clear_trigger()
            last_seen_ts = ""
        else:
            if trigger:
                print(f"[POLL] trigger status={trigger['status']}, waiting...")
            else:
                print(f"[POLL] no trigger file")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()