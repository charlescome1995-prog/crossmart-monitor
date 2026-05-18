# -*- coding: utf-8 -*-
"""
转向产品搜索页面，按类目筛选 + 直接用已有数据推进
不再纠结关键词选品页面的树形控件，改用已有数据
"""
import sys, json, time, base64, os
sys.stdout.reconfigure(encoding='utf-8')
import websocket, urllib.request
from datetime import datetime

SCREENSHOT_DIR = r"C:\Users\OPENPC\.openclaw\workspace\projects\amazon_ai_kit\output\screenshots"

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

print("=" * 70)
print(f"📊 产品搜索 - 按类目筛选美妆个护产品  {datetime.now().strftime('%H:%M')}")
print("=" * 70)

# 1. 导航到产品搜索
print(f"\n【1/5】导航到产品搜索页")
title = go("https://www.sellersprite.com/v3/product-research")
print(f"  当前: {title}")
shot("ps_01_产品搜索页")

# 2. 找类目筛选器
print(f"\n【2/5】查找并展开类目筛选")
js_cat = '''
(() => {
    const info = {};
    
    // 所有select/下拉
    const selects = document.querySelectorAll('.el-select, .el-cascader, [class*="category"], [class*="classify"]');
    info.selects = Array.from(selects).slice(0,5).map(s => {
        const inp = s.querySelector('input, .el-input__inner');
        return {
            placeholder: inp ? (inp.placeholder || '') : '',
            value: inp ? (inp.value || '') : '',
            text: (s.textContent || '').trim().substring(0, 40),
            visible: s.offsetParent !== null
        };
    });
    
    // 当前显示的所有筛选条件（tags/chips）
    const filterTags = document.querySelectorAll('.el-tag, .tag, [class*="filter-item"], [class*="selected"]');
    info.tags = Array.from(filterTags).map(t => (t.textContent || '').trim().substring(0, 20)).filter(Boolean);
    
    return JSON.stringify(info);
})()
'''
cats = json.loads(eval_js(js_cat) or "{}")
print(f"  下拉选择器: {len(cats.get('selects', []))}个")
for s in cats.get('selects', []):
    print(f"    ph={s['placeholder'][:30]} val={s['value'][:20]} visible={s['visible']}")

# 3. 尝试展开类目下拉（第四个或最后一个下拉通常是类目）
print(f"\n【3/5】展开类目下拉选择")
js_open = '''
(() => {
    // 找类目级联选择器 - 含"category"特殊处理的
    const cascaders = document.querySelectorAll('.el-cascader, [class*="category-picker"], [class*="category-select"]');
    
    // 如果有el-cascader，点击展开
    for (const c of cascaders) {
        if (c.offsetParent !== null) {
            const inp = c.querySelector('input');
            // 点击输入框区域展开下拉
            c.click();
            return '点击了类目选择器: ' + ((inp && inp.placeholder) || '');
        }
    }
    
    // 遍历所有下拉选择器
    const allSelects = document.querySelectorAll('.el-select, [class*="select"]');
    const visibleSelects = [];
    allSelects.forEach(s => {
        if (s.offsetParent !== null) {
            visibleSelects.push(s);
        }
    });
    
    // 最后一个下拉通常是类目
    if (visibleSelects.length > 0) {
        const last = visibleSelects[visibleSelects.length - 1];
        last.click();
        return '点击了第' + visibleSelects.length + '个下拉';
    }
    
    // 尝试点击所有外部下拉图标
    const arrows = document.querySelectorAll('.el-icon-arrow-down, i.el-select__caret');
    for (const arrow of arrows) {
        if (arrow.offsetParent !== null) {
            arrow.click();
            return '点击了下拉箭头';
        }
    }
    
    return '未找到下拉控件';
})()
'''
result = eval_js(js_open)
print(f"  结果: {result}")
time.sleep(1.5)

# 截图看看下拉展开情况
shot("ps_02_类目下拉展开")

# 4. 查看总共的筛选条件按钮
print(f"\n【4/5】查看页面上所有功能按钮")
js_btns = '''
(() => {
    const btns = [];
    document.querySelectorAll('button, .el-button, a.btn').forEach(b => {
        const text = (b.textContent || '').trim();
        if (text && text.length < 25 && b.offsetParent !== null) {
            btns.push(text);
        }
    });
    // 去重
    return [...new Set(btns)].slice(0, 20);
})()
'''
btns = json.loads(eval_js(js_btns) or "[]")
print(f"  功能按钮: {btns}")

# 5. 看看当前筛选面板的完整结构
print(f"\n【5/5】分析筛选面板结构")
js_panel = '''
(() => {
    const info = {};
    
    // 找筛选区域
    const filterAreas = document.querySelectorAll('[class*="filter"], [class*="search-area"], [class*="condition"]');
    info.filterAreaCount = filterAreas.length;
    
    // 所有可见的输入框
    const inputs = document.querySelectorAll('input:not([type="hidden"])');
    info.inputs = Array.from(inputs).slice(0,15).map(i => ({
        placeholder: i.placeholder || '',
        value: (i.value || '').substring(0, 20),
        visible: i.offsetParent !== null
    }));
    
    // 下拉选项面板(如果展开了)
    const dropdowns = document.querySelectorAll('.el-select-dropdown, .el-cascader__dropdown, [class*="popper"]');
    info.dropdowns = Array.from(dropdowns).filter(d => d.offsetParent !== null).map(d => {
        const items = d.querySelectorAll('.el-select-dropdown__item, .el-cascader-node, li, [class*="option"]');
        return {
            items: Array.from(items).slice(0, 10).map(it => (it.textContent || '').trim().substring(0, 20)).filter(Boolean),
            count: items.length
        };
    });
    
    return JSON.stringify(info);
})()
'''
panel = json.loads(eval_js(js_panel) or "{}")
print(f"  筛选区域: {panel.get('filterAreaCount', 0)}个")
print(f"  输入框:")
for i in panel.get('inputs', []):
    if i['placeholder'] or i['value']:
        print(f"    ph={i['placeholder'][:35]} val={i['value'][:20]}")
print(f"  下拉面板:")
for d in panel.get('dropdowns', []):
    print(f"    选项({d.get('count',0)}): {d.get('items', [])}")

shot("ps_03_筛选面板结构")

# 最终状态
print(f"\n{'='*70}")
print("✅ 产品搜索页结构分析完成")
print(f"{'='*70}")
print(f"""
现在你可以:

☝️ 方案A - 在页面上操作（推荐你现在看浏览器）:
   1. 在类目下拉中选择 "Beauty & Personal Care" 
   2. 设置条件: 价格$10-$50 / 评论<200 / BSR<100000
   3. 点"查询" → 提取数据 → 用竞品分析验证

✌️ 方案B - 用已有数据继续（我推荐）:
   已从4067条ASIN中提取出232条美妆个护
   程序已经选出Top 10推荐产品
   → 直接进入Listing生成器 出上架方案

当前停留在: 产品搜索页
关注这个页面, 我下一步可以直接操作
""")

ws.close()
