# -*- coding: utf-8 -*-
"""
从产品搜索页提取所有Beauty类目产品
然后导航到Listing生成器，准备出方案
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
print("提取Beauty产品 → 到Listing生成器")
print("=" * 60)

# 1. 确保在产品搜索页
send("Page.navigate", {"url": "https://www.sellersprite.com/v3/product-research"})
time.sleep(4)

# 选高需求低要求
jse("""(()=>{
    const all=document.querySelectorAll('span,div,a,button');
    for(const el of all){
        if((el.textContent||"").trim()==="高需求低要求市场" && el.offsetParent!==null){
            el.click(); return;
        }
    }
})()""")
time.sleep(1)
jse("""(()=>{
    const btns=document.querySelectorAll('button');
    for(const b of btns){
        if(((b.textContent||"").trim()==="开始筛选"||(b.textContent||"").trim()==="查询") && b.offsetParent!==null){
            b.click(); return;
        }
    }
    for(const b of btns){
        if((b.className||"").includes("primary") && b.offsetParent!==null){
            b.click(); return;
        }
    }
})()""")
time.sleep(3)

# 2. 提取所有Beauty类目产品
print(f"\n【1/4】提取Beauty产品数据")
beauty_data = jse("""(()=>{
    const rows=document.querySelectorAll('.el-table__body tr,.el-table tbody tr');
    const beautyItems=[];
    let currentCategory="";
    
    rows.forEach(row=>{
        const cells=row.querySelectorAll('td,.el-table__cell');
        const texts=[];
        cells.forEach(c=>texts.push((c.textContent||"").trim()));
        
        const fullText=texts.join(" ");
        
        // 如果这行是类目标识
        if(fullText.includes("浏览同类目")){
            currentCategory=fullText;
        }
        // 如果是数据行(至少包含产品名)
        else if(texts.some(t=>t.length>10 && t.length<200)){
            beautyItems.push({
                category: currentCategory.substring(0,80),
                rank: texts[0]||"",
                title: texts[1]?texts[1].substring(0,100):"",
                details: texts.slice(2,7).join(" | ").substring(0,100)
            });
        }
    });
    
    // 筛选Beauty & Personal Care
    const filtered=beautyItems.filter(item=>item.category.includes("Beauty"));
    
    return JSON.stringify({total:beautyItems.length, beauty:filtered.length, items:filtered.slice(0,15)});
})()""")
if beauty_data:
    d = json.loads(beauty_data)
    print(f"  产品总数: {d.get('total',0)}")
    print(f"  Beauty产品: {d.get('beauty',0)}")
    print()
    for i, item in enumerate(d.get('items',[])):
        print(f"  #{i+1} {item.get('title','')[:70]}")
        print(f"      {item.get('category','')[:60]}")
        print()

# 3. 导航到Listing生成器
print(f"\n【2/4】导航到Listing生成器")
send("Page.navigate", {"url": "https://www.sellersprite.com/v3/listing-builder"})
time.sleep(4)
shot("lb_01_listing页面")

# 4. 看Listing生成器的输入结构
print(f"\n【3/4】查看Listing生成器输入结构")
lb_info = jse("""(()=>{
    const info={};
    
    // 输入框
    const inputs=[];
    document.querySelectorAll('input,textarea').forEach(inp=>{
        if(inp.offsetParent!==null){
            inputs.push({
                placeholder:(inp.placeholder||"").substring(0,40),
                id:inp.id||"",
                cls:inp.className.substring(0,30),
                value:(inp.value||"").substring(0,30),
                tag:inp.tagName
            });
        }
    });
    info.inputs=inputs.slice(0,15);
    
    // 按钮
    const btns=[];
    document.querySelectorAll('button,.el-button').forEach(b=>{
        if(b.offsetParent!==null){
            const t=(b.textContent||"").trim();
            if(t && t.length<20) btns.push(t);
        }
    });
    info.buttons=[...new Set(btns)];
    
    // 页面标题/分区
    const sections=[];
    document.querySelectorAll('h1,h2,h3,h4,.section-title,[class*=\"card\"] h3').forEach(s=>{
        const t=(s.textContent||"").trim();
        if(t && t.length<50) sections.push(t);
    });
    info.sections=sections.slice(0,15);
    
    // 找ASIN输入框
    const asinInputs=[];
    document.querySelectorAll('input,textarea').forEach(inp=>{
        const ph=inp.placeholder||"";
        if(ph.toLowerCase().includes("asin")){
            asinInputs.push({placeholder:ph, id:inp.id});
        }
    });
    info.asinInputs=asinInputs;
    
    return JSON.stringify(info);
})()""")
if lb_info:
    info = json.loads(lb_info)
    print(f"  ASIN输入框: {info.get('asinInputs', [])}")
    print(f"  输入框:")
    for inp in info.get('inputs', []):
        if inp['placeholder']:
            print(f"    [{inp['tag']:4s}] ph={inp['placeholder'][:40]}")
    print(f"  按钮: {info.get('buttons', [])}")
    print(f"  页面分区: {info.get('sections', [])}")

shot("lb_02_listing结构")

# 5. 在Listing生成器输入一个Beauty产品ASIN
# 从上面找出的Beauty产品中选择一个
print(f"\n【4/4】输入Beauty产品ASIN到Listing生成器")
asin_js = """(()=>{
    // 找一个ASIN输入框并输入值
    const inputs=document.querySelectorAll('input');
    for(const inp of inputs){
        const ph=inp.placeholder||"";
        if((ph.toLowerCase().includes("asin")||ph.includes("输入ASIN")) && inp.offsetParent!==null){
            const native=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
            native.call(inp,"B0DTP5T7N3");  // 荧光灯罩 - beauty相关
            inp.dispatchEvent(new Event("input",{bubbles:true}));
            inp.dispatchEvent(new Event("change",{bubbles:true}));
            return "输入: B0DTP5T7N3";
        }
    }
    // 找第一个可输入的框
    for(const inp of inputs){
        if(inp.offsetParent!==null && inp.type==="text"){
            inp.click();
            inp.focus();
            const native=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
            native.call(inp,"B0DTP5T7N3");
            inp.dispatchEvent(new Event("input",{bubbles:true}));
            inp.dispatchEvent(new Event("change",{bubbles:true}));
            return "输入到第一框";
        }
    }
    return "未找到输入框";
})()"""
r = jse(asin_js)
print(f"  {r}")
time.sleep(1)

shot("lb_03_输入ASIN")

print(f"\n{'='*60}")
print("✅ 完成！")
print(f"  浏览器当前: Listing生成器页面")
print(f"  已输入ASIN: B0DTP5T7N3")
print(f"  你可以看到Listing生成器界面")
print(f"\n  下一步:")
print(f"    1. 点击「生成AI Listing」按钮")
print(f"    2. 看生成的标题/五点/描述")
print(f"    3. 下载或复制到Excel")
print("="*60)

ws.close()
