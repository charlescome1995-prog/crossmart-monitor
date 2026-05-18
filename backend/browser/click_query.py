# -*- coding: utf-8 -*-
"""在关键词选品页面上找查询按钮并点击"""
import sys, json, time
sys.stdout.reconfigure(encoding='utf-8')
import websocket, urllib.request

req = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5)
tabs = json.loads(req.read())
sprite_tabs = [t for t in tabs if "sellersprite" in (t.get("url","")+t.get("title",""))]
tab = sprite_tabs[0]
ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=10)

_id = 0
def send(m, p=None):
    global _id
    _id += 1
    ws.send(json.dumps({"method": m, "id": _id, "params": p or {}}))
    return json.loads(ws.recv()).get("result", {})

# 1. 找所有按钮
js = '''
(() => {
    const results = [];
    const candidates = [];
    
    // 查所有 A/BUTTON/SPAN 有文字的
    document.querySelectorAll('button, a, span, div, i, [role="button"]').forEach(el => {
        const text = (el.textContent || '').trim();
        const cls = el.className || '';
        const tag = el.tagName;
        const visible = el.offsetParent !== null;
        if (visible && text.length > 0 && text.length < 15) {
            candidates.push({text, tag, cls: cls.substring(0,30), visible});
        }
    });
    
    // 按可见性+文字排序
    const visibleBtns = candidates.filter(c => c.visible);
    
    // 识别可能是查询按钮的: 文字包含"查"或"搜"或"query"或"search"
    const queryBtns = visibleBtns.filter(c => 
        c.text.includes('查询') || c.text.includes('搜索') || 
        c.text.toLowerCase().includes('search') || c.text.toLowerCase().includes('query') ||
        c.text === '立即查询'
    );
    
    if (queryBtns.length > 0) {
        return JSON.stringify({type: 'found_query', buttons: queryBtns.slice(0,10)});
    }
    
    // 否则返回所有可见按钮
    return JSON.stringify({type: 'all_visible', buttons: visibleBtns.slice(0,30)});
})()
'''
result = send("Runtime.evaluate", {"expression": js, "returnByValue": True})
data = json.loads(result.get("result", {}).get("value", "{}"))
print(f"类型: {data.get('type', '?')}")
print(f"按钮数: {len(data.get('buttons', []))}")
for b in data.get("buttons", []):
    print(f"  [{b['tag']:4s}] \"{b['text']:15s}\" cls={b['cls']}")

# 2. 如果没找到查询，很可能查询按钮在下一行或隐藏
# 直接在页面文本中搜索
test_js = '''
(() => {
    const body = document.body.innerText || '';
    const lines = body.split('\\n').filter(l => l.trim());
    // 找"查询"或"搜索"附近
    const results = [];
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('查询') || lines[i].includes('搜索')) {
            results.push({
                line: lines[i].trim().substring(0, 50),
                before: (lines[i-1] || '').trim().substring(0, 30),
                after: (lines[i+1] || '').trim().substring(0, 30)
            });
        }
    }
    return JSON.stringify(results.slice(0, 10));
})()
'''
result2 = send("Runtime.evaluate", {"expression": test_js, "returnByValue": True})
texts = json.loads(result2.get("result", {}).get("value", "[]"))
print(f"\n页面中包含\"查询\"或\"搜索\"的文本:")
for t in texts:
    print(f"  line: {t.get('line','')[:50]}")
    if t.get('before'): print(f"  prev: {t['before']}")
    if t.get('after'): print(f"  next: {t['after']}")

# 3. 检查左侧面板的搜索框区域
panel_js = '''
(() => {
    // 包含关键词输入框的父级
    const inputs = document.querySelectorAll('input');
    const panels = [];
    inputs.forEach(inp => {
        if ((inp.placeholder || '').includes('包含关键词')) {
            // 找父容器中的其他元素
            let parent = inp.parentElement;
            for (let i = 0; i < 5 && parent; i++) {
                const siblings = parent.querySelectorAll('button, a, .el-button, [class*="btn"]');
                siblings.forEach(s => {
                    if (s !== inp && (s.textContent || '').trim()) {
                        panels.push({
                            text: (s.textContent || '').trim().substring(0, 20),
                            tag: s.tagName,
                            cls: s.className.substring(0, 30),
                            visible: s.offsetParent !== null
                        });
                    }
                });
                parent = parent.parentElement;
            }
        }
    });
    return JSON.stringify(panels.slice(0, 10));
})()
'''
result3 = send("Runtime.evaluate", {"expression": panel_js, "returnByValue": True})
nearby = json.loads(result3.get("result", {}).get("value", "[]"))
print(f"\n包含关键词输入框附近的按钮:")
for n in nearby:
    print(f"  [{n['tag']:4s}] \"{n['text']:15s}\" cls={n['cls']} visible={n.get('visible',False)}")

# 4. 尝试点击左侧查询区域的查询图标或按钮
# 直接找class含 btn 或 button 且可见的
click_js = '''
(() => {
    // 找可见的查询按钮 - 检查每个元素
    const all = document.querySelectorAll('*');
    for (const el of all) {
        const text = (el.textContent || '').trim();
        if ((text === '查询' || text === '搜索' || text === 'Search') && el.offsetParent !== null) {
            el.click();
            return '点击: ' + text + ' (' + el.tagName + ')';
        }
    }
    // 找包含"查"字且可见的图标或按钮
    for (const el of all) {
        const text = (el.textContent || '').trim();
        if ((text === '查' || text === '搜' || text.includes('查询') || text.includes('搜索')) && el.offsetParent !== null && el.children.length === 0) {
            el.click();
            return '点击文字: ' + text + ' (' + el.tagName + ')';
        }
    }
    // 找第一个是i标签的查询图标
    const icons = document.querySelectorAll('i.el-icon-search, i[class*="search"], i[class*="query"], svg[class*="search"]');
    for (const icon of icons) {
        if (icon.offsetParent !== null) {
            icon.click();
            return '点击搜索图标';
        }
    }
    return '没有找到查询按钮';
})()
'''
result4 = send("Runtime.evaluate", {"expression": click_js, "returnByValue": True})
click_result = result4.get("result", {}).get("value", "")
print(f"\n尝试点击查询按钮: {click_result}")
time.sleep(2)

# 5. 截图
result5 = send("Page.captureScreenshot", {"format": "png", "fromSurface": True})
data = result5.get("data", "")
if data:
    import base64
    path = r"C:\Users\OPENPC\.openclaw\workspace\projects\amazon_ai_kit\output\screenshots\点击查询后.png"
    with open(path, "wb") as f:
        f.write(base64.b64decode(data))
    print(f"截图: {path}")

ws.close()
