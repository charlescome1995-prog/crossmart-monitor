import sys, os, json, websocket, random, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

EDGE_PORT = 9225

def _edge_running_on(port):
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3)
        tabs = json.loads(req.read())
        return True, tabs
    except:
        return False, []

ok, tabs = _edge_running_on(EDGE_PORT)
amazon_tab = None
for t in tabs:
    if "amazon.com/dp" in t.get("url", ""):
        amazon_tab = t
        break

ws_url = amazon_tab["webSocketDebuggerUrl"]
ws = websocket.create_connection(ws_url, timeout=10)

def cmd_raw(method, params=None):
    req_id = random.randint(1, 99999)
    msg = json.dumps({"id": req_id, "method": method, "params": params or {}})
    ws.send(msg)
    results = []
    for _ in range(30):
        raw = ws.recv()
        if raw:
            resp = json.loads(raw)
            results.append(resp)
    return results

js = "(function(){var el=document.querySelector('#productTitle');return el?'FOUND':'NOT_FOUND';})()"
resps = cmd_raw("Runtime.evaluate", {"expression": js, "returnByValue": True, "awaitPromise": True, "timeoutMs": 15000})
for r in resps:
    print(f"msg_id={r.get('id')} method={r.get('method')} result_keys={list(r.get('result',{}).keys()) if 'result' in r else 'N/A'}")

ws.close()