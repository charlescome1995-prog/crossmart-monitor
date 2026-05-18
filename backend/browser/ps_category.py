# -*- coding: utf-8 -*-
"""
产品搜索 - 选择Beauty类目 → 筛选 → 提取美妆个护ASIN
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
        print(f"     📸 {name}.png")

def jse(js):
    r = send("Runtime.evaluate", {"expression": js, "returnByValue": True})
    return r.get("result", {}).get("value")

print("=" * 60)
print("筛选 Beauty & Personal Care 类目")
print("=" * 60)

# 1. 进入产品搜索页
send("Page.navigate", {"url": "https://www.sellersprite.com/v3/product-research"})
time.sleep(4)

# 2. 选「高需求低要求市场」模式
print(f"\n【1/6】选推荐模式")
r = jse("""(()=>{
    const all=document.querySelectorAll('span,div,a,button');
    for(const el of all){
        if((el.textContent||"").trim()==="高需求低要求市场" && el.offsetParent!==null){
            el.click(); return "ok";
        }
    }
    return "not found";
})()""")
print(f"  {r}")
time.sleep(1)

# 3. 找类目选择器并展开
print(f"\n【2/6】展开类目选择")
r = jse("""(()=>{
    // 类目选择器通常是一个el-cascader或有placeholder="选择类目"
    const inputs=document.querySelectorAll('input');
    for(const inp of inputs){
        if(inp.placeholder==="不限" && inp.offsetParent!==null){
            // 点击输入框展开类目
            inp.focus();
            inp.click();
            return "点击类目输入框: "+inp.placeholder;
        }
    }
    // 找包含"选择品类"的文字
    const all=document.querySelectorAll('span,div,label');
    for(const el of all){
        const t=(el.textContent||"").trim();
        if((t.includes("选择品类")||t.includes("选择类目")) && el.offsetParent!==null){
            el.click();
            return "点击: "+t.substring(0,20);
        }
    }
    return "未找到类目选择器";
})()""")
print(f"  {r}")
time.sleep(1.5)
shot("ps_cat_01_类目展开")

# 4. 在展开的类目下拉中找 Beauty & Personal Care
print(f"\n【3/6】查看类目下拉选项")
items = jse("""(()=>{
    const items=[];
    // 查找所有弹出的层级选项
    document.querySelectorAll('.el-cascader-menu__item, .el-cascader-node, [class*="option"]').forEach(el=>{
        if(el.offsetParent!==null){
            const t=(el.textContent||"").trim().substring(0,40);
            if(t && t.length>2) items.push(t);
        }
    });
    return JSON.stringify([...new Set(items)].slice(0,50));
})()""")
if items:
    item_list = json.loads(items)
    print(f"  选项 ({len(item_list)}个):")
    for t in item_list:
        print(f"    {t}")

# 5. 找Beauty关键词并点击
print(f"\n【4/6】选择 Beauty & Personal Care")
r = jse("""(()=>{
    const all=document.querySelectorAll('span,div,.el-cascader-menu__item,.el-cascader-node,[class*="option"]');
    
    // 精准匹配
    const targets=["Beauty & Personal Care","Beauty","Personal Care","Beauty & Health"];
    for(const t of targets){
        for(const el of all){
            if((el.textContent||"").trim()===t && el.offsetParent!==null){
                el.click();
                return "选择了: "+t;
            }
        }
    }
    // 包含匹配
    for(const el of all){
        const txt=(el.textContent||"").trim();
        if(txt.includes("Beauty") && el.offsetParent!==null){
            el.click();
            return "选择了: "+txt.substring(0,30);
        }
    }
    return "未找到Beauty类目";
})()""")
print(f"  {r}")
time.sleep(1)

shot("ps_cat_02_选Beauty")

# 6. 点击筛选/查询
print(f"\n【5/6】开始筛选")
r = jse("""(()=>{
    const btns=document.querySelectorAll('button');
    for(const b of btns){
        const t=(b.textContent||"").trim();
        if((t==="查询"||t==="开始筛选") && b.offsetParent!==null){
            b.click(); return "点击: "+t;
        }
    }
    for(const b of btns){
        if((b.className||"").includes("primary") && b.offsetParent!==null){
            b.click(); return "点击主按钮";
        }
    }
    return "not found";
})()""")
print(f"  {r}")
time.sleep(3)

shot("ps_cat_03_筛选结果")

# 7. 提取Beauty类目数据
print(f"\n【6/6】提取美妆个护数据")
data = jse("""(()=>{
    const rows=document.querySelectorAll('.el-table__body tr.el-table__row,.el-table tbody tr');
    const data=[];
    rows.forEach(row=>{
        const cells=row.querySelectorAll('td,.el-table__cell');
        const rd=[];
        cells.forEach(c=>rd.push((c.textContent||"").trim().substring(0,80)));
        if(rd.length>0 && rd.some(c=>c.length>2 && c.length<200)) data.push(rd);
    });
    return JSON.stringify({count:data.length,rows:data.slice(0,20)});
})()""")
if data:
    d = json.loads(data)
    print(f"  数据行: {d.get('count',0)}")
    for i, r in enumerate(d.get('rows',[])):
        # 提取产品名称
        name = ""
        for c in r:
            if len(c) > 10 and len(c) < 100:
                name = c
                break
        print(f"  [{i}] {name[:60]}")

# 8. 最终汇总
print(f"\n{'='*60}")
print("✅ Beauty类目筛选完成")
print(f"  当前页面: 产品搜索 (筛选了Beauty)")
print(f"  截图: {SCREENSHOT_DIR}")
print(f"\n  如果数据出来了，下一步:")
print(f"    → 导出ASIN列表 → 查竞品页验证 → 广告洞察")
print(f"    → 最终到Listing生成器出上架方案")
print("="*60)

ws.close()
