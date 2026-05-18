# -*- coding: utf-8 -*-
"""查看产品搜索页面的下拉选项"""
import sys, json, time
sys.stdout.reconfigure(encoding="utf-8")
import websocket, urllib.request

req = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5)
tabs = json.loads(req.read())
tab = [t for t in tabs if "sellersprite" in (t.get("url","")+t.get("title",""))][0]
ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=10)

_id = 0
def send(m, p=None):
    global _id; _id += 1
    ws.send(json.dumps({"method": m, "id": _id, "params": p or {}}))
    return json.loads(ws.recv()).get("result", {})

def js(expr):
    r = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    return r.get("result", {}).get("value")

# 当前下拉选项
items = js("""() => {
    const items = [];
    document.querySelectorAll('[class*="option"], [class*="item"]').forEach(o => {
        if (o.offsetParent !== null) {
            const t = (o.textContent||"").trim();
            if(t && t.length<40) items.push(t);
        }
    });
    return items.slice(0, 40);
}""") or []
print(f"下拉可见选项 ({len(items)}):")
for i, t in enumerate(items):
    print(f"  [{i}] {t}")

# 按类目分类 - 显示beauty相关
beauty = [t for t in items if any(k in t.lower() for k in ["beauty","personal","skin","hair","cosmetic","fragrance","makeup","nail","tool","groom","health"])]
print(f"\n美妆相关: {beauty}")

# 搜索面板每个筛选器标签
labels = js("""() => {
    const labels = [];
    document.querySelectorAll('.el-form-item__label, label, [class*="form"] label').forEach(l => {
        const t = (l.textContent||"").trim();
        if(t && t.length<20 && l.offsetParent!==null) labels.push(t);
    });
    return [...new Set(labels)];
}""") or []
print(f"\n筛选标签: {labels}")

# 按钮
btns = js("""() => {
    const s = new Set();
    document.querySelectorAll('button,.el-button,a.btn').forEach(b => {
        const t = (b.textContent||"").trim();
        if(t && t.length<25 && b.offsetParent!==null) s.add(t);
    });
    return Array.from(s);
}""") or []
print(f"\n按钮: {btns}")

# 看有没有查询按钮
all_text = js("document.body.innerText.substring(0, 500)")
print(f"\n页面文本前500字:\n{all_text}")

ws.close()
