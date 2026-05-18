#!/usr/bin/env python3
import sys, json, time, websocket, urllib.request

tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=3).read())
target = None
for t in tabs:
    if "amazon.com" in t.get("url",""):
        target = t; break
if not target: target = tabs[0]

print(f"Tab: {target.get('title','')[:30]}")

ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=10)
msg_id = 0

def cmd(method, params=None):
    global msg_id
    msg_id += 1
    ws.send(json.dumps({"method": method, "id": msg_id, "params": params or {}}))
    # simple recv with timeout
    for _ in range(3):
        try:
            ws.settimeout(5)
            r = json.loads(ws.recv())
            if r.get("id") == msg_id:
                return r.get("result", {})
        except:
            pass
    return None

# Test DOM extraction
result = cmd("Runtime.evaluate", {"expression": "document.title", "returnByValue": True})
print(f"Title: {result}")

result = cmd("Runtime.evaluate", {"expression": "document.querySelector('#productTitle')?.textContent?.trim() || 'N/A'", "returnByValue": True})
print(f"Product title: {result}")

result = cmd("Runtime.evaluate", {"expression": "document.querySelector('.a-price-whole')?.textContent?.trim() || 'N/A'", "returnByValue": True})
print(f"Price: {result}")

result = cmd("Runtime.evaluate", {"expression": "document.querySelector('#acrPopover .a-size-base')?.textContent?.trim() || 'N/A'", "returnByValue": True})
print(f"Rating: {result}")

result = cmd("Runtime.evaluate", {"expression": "document.querySelector('#acrCustomerReviewText')?.textContent?.trim() || 'N/A'", "returnByValue": True})
print(f"Reviews: {result}")

ws.close()
