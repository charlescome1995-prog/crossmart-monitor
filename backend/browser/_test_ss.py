#!/usr/bin/env python3
import sys, os, json, time, websocket, urllib.request, base64

ss_dir = r"C:\Users\OPENPC\.openclaw\workspace\projects\amazon_ai_kit\output\screenshots"
os.makedirs(ss_dir, exist_ok=True)

tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=3).read())
print(f"Tabs: {len(tabs)}")

# 找一个普通tab（非edge:// 页面）
for t in tabs:
    url = t.get("url","")
    if not url.startswith("edge://"):
        target = t
        break
else:
    target = tabs[0]

print(f"Tab: {target.get('title','')[:30]} | {target.get('url','')[:60]}")

ws_url = target["webSocketDebuggerUrl"]
ws = websocket.create_connection(ws_url, timeout=10)
msg_id = 0

def send(method, params=None):
    global msg_id
    msg_id += 1
    ws.send(json.dumps({"method": method, "id": msg_id, "params": params or {}}))
    # Read response - might need multiple receives
    for _ in range(5):
        try:
            resp = ws.recv()
            d = json.loads(resp)
            if d.get("id") == msg_id:
                return d
        except:
            break
    return None

# 先navigate到一个普通页面
print("\nNavigating to amazon.com...")
ws.send(json.dumps({"method": "Page.enable", "id": 1}))

# Navigate
ws.send(json.dumps({"method": "Page.navigate", "id": 2, "params": {"url": "https://www.amazon.com"}}))

# 等几秒
time.sleep(4)

# 截图
print("\nScreenshot...")
ws.send(json.dumps({"method": "Page.captureScreenshot", "id": 3, "params": {"format": "png", "fromSurface": True}}))

# 收到直到看到id=3
deadline = time.time() + 10
while time.time() < deadline:
    try:
        resp = ws.recv()
        d = json.loads(resp)
        if d.get("id") == 3:
            print("Got screenshot response!")
            data = d.get("result", {}).get("data", "")
            if data:
                path = os.path.join(ss_dir, "test_working.png")
                with open(path, "wb") as f:
                    f.write(base64.b64decode(data))
                print(f"Saved: {path} ({os.path.getsize(path)} bytes)")
            else:
                print("No data in result, keys:", list(d.get("result",{}).keys()))
            break
        else:
            print(f"Other message: id={d.get('id')}, method={d.get('method','?')}")
    except:
        break

ws.close()
print("\nDone")
