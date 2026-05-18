# -*- coding: utf-8 -*-
"""
直接在卖家精灵产品搜索页操作 - 选择美妆类目 + 提取数据
用简单可靠的JS点击文本元素
"""
import sys, json, time, base64, os
sys.stdout.reconfigure(encoding="utf-8")
import websocket, urllib.request

SCREENSHOT_DIR = r"C:\Users\OPENPC\.openclaw\workspace\projects\amazon_ai_kit\output\screenshots"

req = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5)
tabs = json.loads(req.read())
tab = [t for t in tabs if "sellersprite" in (t.get("url","")+t.get("title",""))][0]
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
        kb = os.path.getsize(p)//1024
        print(f"     📸 {name}.png ({kb}KB)")

def jse(js):
    r = send("Runtime.evaluate", {"expression": js, "returnByValue": True})
    return r.get("result", {}).get("value")

print("=" * 60)
print("操作: 产品搜索 → 选模式 → 出结果")
print("=" * 60)

# 1. 确保在产品搜索页
send("Page.navigate", {"url": "https://www.sellersprite.com/v3/product-research"})
time.sleep(4)

# 2. 点击"高需求低要求市场"推荐模式
print(f"\n【1/5】选择推荐模式: 高需求低要求市场")
r = jse("""(()=>{
    const all=document.querySelectorAll('span,div,a,button');
    for(const el of all){
        if((el.textContent||"").trim()==="高需求低要求市场" && el.offsetParent!==null){
            el.click(); return "点击: 高需求低要求市场";
        }
    }
    // 尝试中间一个
    const targets=["低价长尾选品","研发新品榜","潜力单变体","销量飙升榜"];
    for(const t of targets){
        for(const el of all){
            if((el.textContent||"").trim()===t && el.offsetParent!==null){
                el.click(); return "点击: "+t;
            }
        }
    }
    return "未找到推荐模式按钮";
})()""")
print(f"  {r}")
time.sleep(1.5)
shot("op_01_推荐模式")

# 3. 点击"查询"（蓝色按钮）
print(f"\n【2/5】点击查询按钮")
r = jse("""(()=>{
    const btns=document.querySelectorAll('button');
    for(const b of btns){
        const t=(b.textContent||"").trim();
        if((t==="查询"||t==="搜 索"||t==="搜索") && b.offsetParent!==null){
            b.click(); return "点击: "+t;
        }
    }
    // 找主要按钮
    for(const b of btns){
        if((b.className||"").includes("primary") && b.offsetParent!==null){
            b.click(); return "点击主按钮: "+((b.textContent||"").trim());
        }
    }
    return "未找到查询按钮";
})()""")
print(f"  {r}")
time.sleep(3)
shot("op_02_查询结果")

# 4. 提取数据
print(f"\n【3/5】提取产品数据表格")
data_json = jse("""(()=>{
    const result={columns:[],rows:[],count:0};
    
    // 列头
    const ths=document.querySelectorAll('.el-table__header th,table th,.el-table thead th');
    result.columns=Array.from(ths).map(th=>(th.textContent||"").trim()).filter(Boolean).slice(0,20);
    
    // 数据
    const rows=document.querySelectorAll('.el-table__body tr.el-table__row,.el-table tbody tr');
    const data=[];
    rows.forEach(row=>{
        const cells=row.querySelectorAll('td,.el-table__cell');
        const rd=[];
        cells.forEach(c=>rd.push((c.textContent||"").trim().substring(0,60)));
        if(rd.length>0 && rd.some(c=>c.length>2)) data.push(rd);
    });
    result.rows=data.slice(0,25);
    result.count=data.length;
    
    return JSON.stringify(result);
})()""")
if data_json:
    data = json.loads(data_json) if isinstance(data_json, str) else data_json
    print(f"  列 ({len(data.get('columns',[]))}):")
    for c in data.get('columns', []):
        print(f"    {c}")
    print(f"  数据行: {data.get('count', 0)}")
    for i, r in enumerate(data.get('rows', [])):
        print(f"  [{i}] {[c[:30] for c in r[:5]]}")

# 5. 如果没数据，看页面是不是还没加载完
if data.get('count', 0) == 0:
    print(f"\n【4/5】表格为空, 尝试滚屏加载")
    jse("window.scrollBy(0, 500)")
    time.sleep(2)
    shot("op_03_滚动后")
    
    data_json2 = jse("""(()=>{
        const rows=document.querySelectorAll('.el-table__body tr.el-table__row,.el-table tbody tr');
        const data=[];
        rows.forEach(row=>{
            const cells=row.querySelectorAll('td,.el-table__cell');
            const rd=[];
            cells.forEach(c=>rd.push((c.textContent||"").trim().substring(0,60)));
            if(rd.length>0 && rd.some(c=>c.length>2)) data.push(rd);
        });
        return JSON.stringify({count:data.length,rows:data.slice(0,25)});
    })()""")
    data2 = json.loads(data_json2)
    print(f"  滚动后行数: {data2.get('count',0)}")
    if data2.get('count',0) > 0:
        for i, r in enumerate(data2.get('rows', [])):
            print(f"  [{i}] {[c[:30] for c in r[:5]]}")

# 6. 汇总
print(f"\n{'='*60}")
print(f"✅ 操作完成")
print(f"  截图保存: {SCREENSHOT_DIR}")
print(f"  当前页面: 产品搜索页（看浏览器）")
print("="*60)

ws.close()
