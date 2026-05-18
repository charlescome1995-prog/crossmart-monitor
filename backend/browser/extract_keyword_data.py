# -*- coding: utf-8 -*-
"""
操作关键词选品页面：选择数据源→搜索美妆词→提取数据
"""
import sys, json, time, base64, os
sys.stdout.reconfigure(encoding='utf-8')
import websocket, urllib.request

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
        kb = os.path.getsize(p)//1024
        print(f"     📸 {name}.png ({kb}KB)")

def eval_js(js):
    r = send("Runtime.evaluate", {"expression": js, "returnByValue": True})
    return r.get("result", {}).get("value")

print("=" * 70)
print("操作: 关键词选品 - 数据源切换 + 提取美妆词表格")
print("=" * 70)

# 0. 确保在关键词选品页
url = eval_js("window.location.href")
if "keyword-research" not in (url or ""):
    print("导航到关键词选品页...")
    send("Page.navigate", {"url": "https://www.sellersprite.com/v2/keyword-research"})
    time.sleep(3)

print(f"\n【1】当前页面: {eval_js('document.title')}")
shot("kw_00_初始状态")

# 1. 找数据源切换控件
print(f"\n【2】找数据源切换面板")
js_src = '''
(() => {
    // 找数据源/词库切换
    const all = document.body.innerText;
    // 数据源区域 - 找"关键词词库"等文本附近
    const dataSources = [];
    document.querySelectorAll('[class*="source"], [class*="data"], [class*="tab"], [class*="库"]').forEach(el => {
        const text = (el.textContent || '').trim().substring(0, 20);
        if (text && text.length > 1 && el.offsetParent !== null) {
            const rect = el.getBoundingClientRect();
            dataSources.push({text, tag: el.tagName, cls: el.className.substring(0,30), 
                            x: rect.x, y: rect.y, w: rect.width, h: rect.height});
        }
    });
    return JSON.stringify(dataSources.slice(0, 30));
})()
'''
srcs = json.loads(eval_js(js_src) or "[]")
print(f"  找到 {len(srcs)} 个可见控件")
for s in srcs:
    print(f"    [{s['tag']:4s}] \"{s['text'][:25]:25s}\" cls={s['cls']}")

# 2. 找"全部关键词"选项
print(f"\n【3】查找并点击数据源选择")
js_pick = '''
(() => {
    // 找全部关键词 / 所有关键词 选项并点击
    const targets = ['全部关键词', '关键词词库', 'ABA数据', '自定义词库'];
    for (const target of targets) {
        const all = document.querySelectorAll('span, div, a, label, .el-radio__label, .el-checkbox__label');
        for (const el of all) {
            if ((el.textContent || '').trim() === target && el.offsetParent !== null) {
                el.click();
                return '点击:' + target;
            }
        }
    }
    // 找包含"关键词"的tab
    const tabs = document.querySelectorAll('[class*="tab"]');
    for (const tab of tabs) {
        if ((tab.textContent || '').trim().includes('关键词') && tab.offsetParent !== null) {
            tab.click();
            return '点击tab:' + tab.textContent.trim().substring(0,20);
        }
    }
    return '未找到';
})()
'''
result = eval_js(js_pick)
print(f"  结果: {result}")
time.sleep(1.5)

shot("kw_01_数据源选择")

# 3. 输入具体美妆关键词
print(f"\n【4】在搜索框中输入美妆关键词")
js_search = '''
(() => {
    // 找可输入关键词的输入框
    const inputs = document.querySelectorAll('input');
    for (const inp of inputs) {
        const ph = inp.placeholder || '';
        if (ph.includes('包含关键词') || ph.includes('输入关键词') || ph.includes('搜索')) {
            if (inp.offsetParent !== null) {
                // 清除现有内容
                inp.value = '';
                const native = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                native.call(inp, 'press on nails nail polish');
                inp.dispatchEvent(new Event('input', {bubbles: true}));
                inp.dispatchEvent(new Event('change', {bubbles: true}));
                return '输入到:' + ph;
            }
        }
    }
    return '未找到搜索输入框';
})()
'''
result = eval_js(js_search)
print(f"  结果: {result}")
time.sleep(1)

shot("kw_02_输入美甲关键词")

# 4. 找并点击查询按钮
print(f"\n【5】查找查询按钮")
js_btn = '''
(() => {
    // 遍历所有可见元素找"查询"或"立即查询"
    const all = document.querySelectorAll('*');
    for (const el of all) {
        const text = (el.textContent || '').trim();
        if ((text === '查询' || text.includes('立即查询') || text.includes('开始搜索')) && el.offsetParent !== null && el.children.length === 0) {
            // 点击父级button
            let parent = el.parentElement;
            while (parent && parent.tagName !== 'BUTTON' && parent.tagName !== 'A') {
                parent = parent.parentElement;
                if (!parent || parent === document.body) break;
            }
            if (parent && (parent.tagName === 'BUTTON' || parent.tagName === 'A')) {
                parent.click();
                return '点击按钮:' + parent.textContent.trim().substring(0,20);
            }
            el.click();
            return '点击文字:' + text;
        }
    }
    // 找el-button类型的查询按钮
    const btns = document.querySelectorAll('button.el-button, button.btn, a.el-button');
    for (const btn of btns) {
        const text = (btn.textContent || '').trim();
        if ((text === '查询' || text === '搜 索' || text === '确定') && btn.offsetParent !== null) {
            btn.click();
            return '点击:' + text;
        }
    }
    // 最后尝试：找所有button的文本
    const allBtns = document.querySelectorAll('button');
    for (const btn of allBtns) {
        const text = (btn.textContent || '').trim();
        if (text.includes('查询') && btn.offsetParent !== null) {
            btn.click();
            return '点击:' + text;
        }
    }
    return '未找到查询按钮';
})()
'''
result = eval_js(js_btn)
print(f"  结果: {result}")
time.sleep(3)

shot("kw_03_查询后")

# 5. 提取表格数据
print(f"\n【6】提取数据表格")
js_table = '''
(() => {
    // 提取所有可见表格数据
    const tables = document.querySelectorAll('.el-table, table, [class*="table"]');
    const data = [];
    
    tables.forEach(table => {
        // 只处理可见的
        if (table.offsetParent === null) return;
        
        // 提取列头
        const headers = [];
        table.querySelectorAll('th, .el-table__header th').forEach(th => {
            const text = (th.textContent || '').trim();
            if (text) headers.push(text);
        });
        
        // 提取行
        const rows = [];
        table.querySelectorAll('tr.el-table__row, tbody tr').forEach(row => {
            const cells = [];
            row.querySelectorAll('td, .el-table__cell').forEach(cell => {
                cells.push((cell.textContent || '').trim().substring(0, 100));
            });
            if (cells.length > 0) rows.push(cells);
        });
        
        data.push({headers, rowCount: rows.length, rows: rows.slice(0, 30)});
    });
    
    return JSON.stringify(data);
})()
'''
tables = json.loads(eval_js(js_table) or "[]")
print(f"  表格数量: {len(tables)}")
for t in tables:
    print(f"    列: {t.get('headers', [])[:15]}")
    print(f"    行: {t.get('rowCount', 0)}")
    for r in t.get('rows', [])[:5]:
        print(f"      {r[:5]}")
    if t.get('rows', []):
        print(f"      ... (更多)")

# 6. 如果没表格，看页面主要内容
if not any(t.get('rowCount', 0) > 0 for t in tables):
    print(f"\n【7】表格为空，查看当前页面内容")
    js_content = '''
(() => {
    const body = document.body.innerText || '';
    const lines = body.split('\\n').filter(l => l.trim());
    // 找表格区域相关的行
    const tableLines = [];
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line && (['#', '关键词', '月搜索', '月购买', '需供比', '品牌', 'ASIN', '竞品'].some(h => line.includes(h)))) {
            tableLines.push({index: i, text: line.substring(0, 80)});
            // 后面连续几行
            for (let j = 1; j <= 5; j++) {
                if (lines[i+j]) {
                    tableLines.push({index: i+j, text: lines[i+j].trim().substring(0, 80)});
                }
            }
            break;
        }
    }
    // 如果没有找到，直接显示前20行
    if (tableLines.length === 0) {
        for (let i = 0; i < Math.min(20, lines.length); i++) {
            tableLines.push({index: i, text: lines[i].trim().substring(0, 80)});
        }
    }
    return JSON.stringify(tableLines.slice(0, 30));
})()
'''
content = json.loads(eval_js(js_content) or "[]")
print(f"  页面主要内容:")
for line in content:
    print(f"    {line.get('text', '')}")

# 7. 如果没有数据，看看是不是需要先选择词库
print(f"\n【8】检查是否需要先选左侧词库")
js_left = '''
(() => {
    // 左侧面板 - 词库树
    const leftPanel = document.querySelector('[class*="left"], [class*="sidebar"], [class*="tree"], [class*="nav"]');
    if (leftPanel) {
        const items = leftPanel.querySelectorAll('[class*="node"], [class*="item"], li, .el-tree-node');
        return items.length > 0 ? '左侧有' + items.length + '个选项' : '左侧无选项';
    }
    return '未检测到左侧面板';
})()
'''
result = eval_js(js_left)
print(f"  检测: {result}")

shot("kw_04_最终状态")

ws.close()
print(f"\n{'='*70}")
print("操作完成")
