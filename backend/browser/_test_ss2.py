#!/usr/bin/env python3
import sys, os, json, time, websocket, urllib.request, base64

ss_dir = r"C:\Users\OPENPC\.openclaw\workspace\projects\amazon_ai_kit\output\screenshots"
os.makedirs(ss_dir, exist_ok=True)

tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=3).read())

# find amazon tab or use first good one
target = tabs[0]
print(f"Tab: {target.get('title','')[:30]} | {target.get('url','')[:60]}")

ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=20)
msg_id = 0

def recv_all(timeout=2):
    """Read all available messages"""
    msgs = []
    ws.settimeout(timeout)
    while True:
        try:
            msgs.append(json.loads(ws.recv()))
        except:
            break
    ws.settimeout(None)
    return msgs

def cmd(method, params=None, wait=0.5):
    global msg_id
    msg_id += 1
    ws.send(json.dumps({"method": method, "id": msg_id, "params": params or {}}))
    time.sleep(wait)
    return recv_all()

# Navigate to a page first
resp = cmd("Page.enable", wait=0.3)
resp = cmd("Page.navigate", {"url": "https://www.amazon.com"}, wait=5)
time.sleep(3)

# Now screenshot
resp = cmd("Page.captureScreenshot", {"format": "png", "fromSurface": True}, wait=3)

# Find our response
for r in resp:
    if r.get("id") == msg_id:
        data = r.get("result", {}).get("data", "")
        if data:
            path = os.path.join(ss_dir, "test_final.png")
            with open(path, "wb") as f:
                f.write(base64.b64decode(data))
            print(f"SUCCESS: {os.path.getsize(path)} bytes -> {path}")
        else:
            print(f"No data. keys: {list(r.get('result',{}).keys())}")
        break
else:
    print("No screenshot response found")
    print(f"All responses ({len(resp)}):")
    for r in resp[:5]:
        print(f"  id={r.get('id')}, method={r.get('method','?')}")

ws.close()
