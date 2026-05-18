# -*- coding: utf-8 -*-
"""
产品搜索 - 选择推荐模式 + 提取美妆个护数据
避开复杂的类目级联，用推荐模式筛选
"""
import sys, json, time, base64, os
sys.stdout.reconfigure(encoding="utf-8")
import websocket, urllib.request

SCREENSHOT_DIR = r"C:\Users\OPENPC\.openclaw\workspace\projects\amazon_ai_kit\output\screenshots"

req = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5)
tabs = json.loads(req.read())
sprite_tabs = [t for t in tabs if "sellersprite" in (t.get("url","")+t.get("title",""))]
tab = sprite_tabs[0]
ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=10)

_id = 0
def send(m, p=None):
    global _id; _id += 1
    ws.send(json.dumps({"method": m, "id": _id, "params": p or {}}))
    return json.loads(ws.recv()).get("result", {})

def shot(name):
    r = send("Page.captureScreenshot", {"format": "png", "fromSurface": True})
    d = r.get("data", "")
    if d:
        p = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        with open(p, "wb") as f:
            f.write(base64.b64decode(d))
        print(f"     📸 {name}.png")

def go(url, t=3):
    send("Page.navigate", {"url": url})
    time.sleep(t)
    r = send("Runtime.evaluate", {"expression": "document.title", "returnByValue": True})
    return r.get("result", {}).get("value", "")

def eval_js(js):
    r = send("Runtime.evaluate", {"expression": js, "returnByValue": True})
    return r.get("result", {}).get("value")

print("=" * 60)
print("产品搜索 - 用推荐模式筛选美妆个护")
print("=" * 60)

# 1. 确保在产品搜索页
go("https://www.sellersprite.com/v3/product-research")
print(f"\n【1】已进入产品搜索页")

# 2. 看左侧导航树能否展开类目
print(f"\n【2】找左侧类目树")
js_tree = """
() => {
    // 在左侧导航中找类目
    const leftNav = document.querySelector('[class*="left"], [class*="sidebar"], [class*="tree"], .el-tree, nav');
    if (!leftNav) return "无左侧导航";
    
    // 找所有可见的导航项
    const nodes = leftNav.querySelectorAll('[class*="node"], [class*="item"], li, a, span');
    const items = [];
    nodes.forEach(n => {
        const t = (n.textContent||"").trim();
        if(t && t.length < 30 && n.offsetParent !== null) {
            items.push(t);
        }
    });
    return JSON.stringify([...new Set(items)].slice(0, 40));
}
"""
items_raw = eval_js(js_tree)
if items_raw:
    items = json.loads(items_raw) if isinstance(items_raw, str) else items_raw
    print(f"  左侧导航项 ({len(items)}):")
    for t in items[:20]:
        print(f"    {t}")

# 3. 查看"推荐模式"中的选项
print(f"\n【3】推荐模式选项")
js_modes = """
() => {
    // 推荐模式区域
    const modes = [];
    document.querySelectorAll('[class*="recommend"], [class*="mode"], [class*="pattern"]').forEach(el => {
        const items = el.querySelectorAll('span, a, div, button');
        items.forEach(item => {
            const t = (item.textContent||"").trim();
            if(t && t.length < 25 && t.length > 2 && item.offsetParent !== null) {
                modes.push(t);
            }
        });
    });
    return JSON.stringify([...new Set(modes)].slice(0, 30));
}
"""
modes_raw = eval_js(js_modes)
if modes_raw:
    modes = json.loads(modes_raw) if isinstance(modes_raw, str) else modes_raw
    print(f"  推荐模式 ({len(modes)}):")
    for m in modes:
        print(f"    {m}")

# 4. 找"高需求低要求市场"这个模式（适合美妆个护low bar）
print(f"\n【4】点击第一个推荐模式")
js_click_mode = """
() => {
    // 找所有可见的推荐模式选项并点第一个
    const all = document.querySelectorAll('span, a, div, button');
    const candidates = ["高需求低要求市场","低价长尾选品","潜力单变体","研发新品榜"];
    for (const target of candidates) {
        for (const el of all) {
            if ((el.textContent||"").trim() === target && el.offsetParent !== null) {
                el.click();
                return "选择了: " + target;
            }
        }
    }
    // 任意可见选项
    for (const el of all) {
        const t = (el.textContent||"").trim();
        if (t.length > 3 && t.length < 15 && el.offsetParent !== null && el.tagName === "SPAN") {
            el.click();
            return "点击: " + t;
        }
    }
    return "未找到可点击选项";
}
"""
result = eval_js(js_click_mode)
print(f"  结果: {result}")
time.sleep(2)

shot("ps_04_选择推荐模式后")

# 5. 现在找"查询"按钮
print(f"\n【5】找并点击查询/搜索按钮")
js_query = """
() => {
    // 找所有可见文本含"查询"或"搜索"的元素
    const all = document.querySelectorAll('button, span, a, div');
    for (const el of all) {
        const t = (el.textContent||"").trim();
        if (t.includes("查询") && el.offsetParent !== null) {
            el.click();
            return "点击: " + t;
        }
    }
    // 找第一个蓝色主要按钮
    const btns = document.querySelectorAll('button.el-button--primary, .el-button--primary');
    for (const btn of btns) {
        if (btn.offsetParent !== null) {
            btn.click();
            return "点击主按钮: " + ((btn.textContent||"").trim());
        }
    }
    return "未找到查询按钮";
}
"""
result = eval_js(js_query)
print(f"  结果: {result}")
time.sleep(3)

shot("ps_05_查询结果")

# 6. 提取表格数据
print(f"\n【6】提取产品数据")
js_data = """
() => {
    const result = {columns: [], rows: [], count: 0};
    
    // 表头
    const headers = document.querySelectorAll('.el-table__header th, table th');
    result.columns = Array.from(headers).map(th => (th.textContent||"").trim()).filter(Boolean);
    
    // 数据行
    const rows = document.querySelectorAll('.el-table__body tr, tbody tr');
    const data = [];
    rows.forEach(row => {
        const cells = row.querySelectorAll('td, .el-table__cell');
        const rowData = [];
        cells.forEach(cell => {
            rowData.push((cell.textContent||"").trim().substring(0, 60));
        });
        if (rowData.length > 0 && rowData.some(c => c.length > 2)) {
            data.push(rowData);
        }
    });
    result.rows = data.slice(0, 20);
    result.count = data.length;
    
    // 当前筛选条件
    const filterTexts = [];
    document.querySelectorAll('.el-tag, [class*="filter-tag"]').forEach(t => {
        const txt = (t.textContent||"").trim();
        if(txt) filterTexts.push(txt.substring(0, 30));
    });
    result.filters = filterTexts.slice(0, 10);
    
    return JSON.stringify(result);
}
"""
data_raw = eval_js(js_data)
if data_raw:
    data = json.loads(data_raw) if isinstance(data_raw, str) else data_raw
    print(f"  列 ({len(data.get('columns',[]))}): {data.get('columns', [])}")
    print(f"  数据行: {data.get('count', 0)}")
    for r in data.get('rows', [])[:8]:
        print(f"    {[c for c in r[:6]]}")
    print(f"  筛选条件: {data.get('filters', [])}")

# 7. 如果没有数据，那是选了什么类目下
print(f"\n【7】当前页面内容摘要")
js_text = "document.body.innerText.substring(0, 1000)"
text = eval_js(js_text)
if text:
    lines = text.split("\n")
    # 找表格区域
    for i, line in enumerate(lines):
        if any(k in line for k in ["产品","ASIN","BSR","销量","价格","评分","评论"]):
            print(f"  [{i}] {line[:80]}")
    print("  ...")
    for i in range(max(0, len(lines)-5), len(lines)):
        if lines[i].strip():
            print(f"  [{i}] {lines[i][:80]}")

shot("ps_06_最终状态")

ws.close()
print(f"\n{'='*60}")
print("产品搜索页面分析完成")
print(f"截图目录: {SCREENSHOT_DIR}")
