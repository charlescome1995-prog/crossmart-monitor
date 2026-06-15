# -*- coding: utf-8 -*-
"""
卖家精灵关键词选品 - 搜索美妆个护并导出数据
1. 在关键词选品页面搜索美妆个护关键词
2. 提取搜索结果表格数据
3. 保存为可用于编程分析的JSON
"""
import sys, json, time, base64, os
sys.stdout.reconfigure(encoding='utf-8')

import websocket, urllib.request
from datetime import datetime

SCREENSHOT_DIR = r"C:\Users\OPENPC\.openclaw\workspace\projects\amazon_ai_kit\output\screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

class CDP:
    def __init__(self):
        req = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5)
        tabs = json.loads(req.read())
        sprite_tabs = [t for t in tabs if "sellersprite" in (t.get("url","")+t.get("title",""))]
        self.tab = sprite_tabs[0] if sprite_tabs else tabs[0]
        ws_url = self.tab["webSocketDebuggerUrl"]
        self.ws = websocket.create_connection(ws_url, timeout=10)
        self._id = 0
    
    def cmd(self, method, params=None):
        self._id += 1
        self.ws.send(json.dumps({"method": method, "id": self._id, "params": params or {}}))
        return json.loads(self.ws.recv()).get("result", {})
    
    def go(self, url, wait=3):
        self.cmd("Page.navigate", {"url": url})
        time.sleep(wait)
        r = self.cmd("Runtime.evaluate", {"expression": "document.title", "returnByValue": True})
        return r.get("result", {}).get("value", "")
    
    def shot(self, name):
        r = self.cmd("Page.captureScreenshot", {"format": "png", "fromSurface": True})
        data = r.get("data", "")
        if data:
            path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
            with open(path, "wb") as f:
                f.write(base64.b64decode(data))
            print(f"     📸 {name}.png")
    
    def eval(self, js):
        r = self.cmd("Runtime.evaluate", {"expression": js, "returnByValue": True})
        return r.get("result", {}).get("value")
    
    def close(self):
        self.ws.close()


def main():
    print("=" * 70)
    print("美妆个护选品 - 关键词选品操作")
    print(f"时间: {datetime.now().strftime('%H:%M')}")
    print("=" * 70)
    
    cdp = CDP()
    
    # 1. 到关键词选品页面
    print(f"\n【步骤1】导航到关键词选品")
    cdp.go("https://www.sellersprite.com/v2/keyword-research")
    
    # 2. 查看当前页面的表格数据 - 已有的词库
    print(f"\n【步骤2】提取当前美妆个护词库数据")
    
    js_extract = """
(() => {
    // 提取当前表格数据
    const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr, table tbody tr');
    const data = [];
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td, .el-table__cell');
        const rowData = [];
        cells.forEach(cell => {
            const text = (cell.textContent || '').trim().substring(0, 80);
            rowData.push(text);
        });
        if (rowData.length > 0) {
            data.push(rowData);
        }
    });
    
    // 获取列标题
    const headers = [];
    document.querySelectorAll('.el-table__header-wrapper th, table th').forEach(th => {
        const text = (th.textContent || '').trim();
        if (text) headers.push(text);
    });
    
    return JSON.stringify({headers, rows: data.slice(0, 30)});
})()
"""
    table_data = json.loads(cdp.eval(js_extract) or '{"headers":[],"rows":[]}')
    print(f"  列标题 ({len(table_data.get('headers',[]))}): {table_data['headers']}")
    print(f"  数据行: {len(table_data.get('rows',[]))} 行")
    
    for r in table_data['rows'][:5]:
        print(f"    {r}")
    
    # 3. 在搜索结果中找"美容"关键词的表格数据
    # 当前页面是词库管理列表，需要查看已有词库
    print(f"\n【步骤3】查看可用的美妆个护词库")
    
    js_scan = """
(() => {
    // 扫描页面内容找美妆个护相关词
    const body = document.body.innerText || '';
    const searchTerms = ['nail', 'skin', 'hair', 'beauty', 'makeup', 'face', 'body', 'lash', 'brow', 'lip', 'serum'];
    const found = [];
    searchTerms.forEach(term => {
        if (body.toLowerCase().includes(term)) {
            found.push(term);
        }
    });
    
    // 找存在的词库列表
    const lists = [];
    document.querySelectorAll('.el-table__body tr, [class*="list-item"]').forEach(el => {
        const text = (el.textContent || '').trim().substring(0, 100);
        if (text) lists.push(text);
    });
    
    return JSON.stringify({found, lists: lists.slice(0, 20)});
})()
"""
    scan = json.loads(cdp.eval(js_scan) or '{"found":[],"lists":[]}')
    print(f"  页面中匹配的美妆词: {scan.get('found', [])}")
    
    # 4. 尝试搜索美妆个护关键词
    print(f"\n【步骤4】在搜索框搜索美妆个护词")
    
    # 先看有没有搜索输入框  
    js_find_search = """
(() => {
    // 找搜索输入框
    const allInputs = document.querySelectorAll('input');
    const searchInputs = [];
    allInputs.forEach(inp => {
        const ph = inp.placeholder || '';
        const val = inp.value || '';
        if (ph.includes('搜索') || ph.includes('search') || ph.includes('关键词') || ph.includes('key')) {
            searchInputs.push({
                placeholder: ph,
                value: val.substring(0, 20),
                id: inp.id,
                cls: inp.className.substring(0, 50),
                isVisible: inp.offsetParent !== null
            });
        }
    });
    return JSON.stringify(searchInputs);
})()
"""
    search_inputs = json.loads(cdp.eval(js_find_search) or "[]")
    print(f"  搜索输入框: {len(search_inputs)}个")
    for inp in search_inputs:
        print(f"    placeholder={inp['placeholder']} visible={inp['isVisible']}")
    
    cdp.shot("stepA_美妆词搜索前")
    
    # 5. 打开一个新词库搜索
    # 去找"新建"按钮
    print(f"\n【步骤5】新建美妆个护词库搜索")
    
    js_click_new = """
(() => {
    // 找"新建"或"新词库"按钮
    const btnTexts = ['新建', '新词库', 'New', '+'];
    const allEls = document.querySelectorAll('button, a, span, div, [role="button"]');
    
    for (const el of allEls) {
        const text = (el.textContent || '').trim();
        if (btnTexts.some(t => text === t || text.includes(t))) {
            const isBtn = el.tagName === 'BUTTON' || el.getAttribute('role') === 'button' || 
                         el.classList.contains('el-button') || el.tagName === 'A';
            if (isBtn && text.length < 5) {
                el.click();
                return '点击:' + text;
            }
        }
    }
    return '未找到新建按钮';
})()
"""
    result = cdp.eval(js_click_new)
    print(f"  点击结果: {result}")
    time.sleep(2)
    
    cdp.shot("stepB_新建词库弹窗")
    
    # 6. 看弹窗里有什么
    print(f"\n【步骤6】查看弹窗/搜索面板")
    
    js_modal = """
(() => {
    // 找弹窗或新增面板
    const dialogs = document.querySelectorAll('.el-dialog, .el-drawer, .modal, [class*="dialog"], [class*="modal"], [class*="overlay"]');
    const info = [];
    
    dialogs.forEach(d => {
        const visible = d.offsetParent !== null;
        if (visible) {
            const text = (d.textContent || '').trim().substring(0, 300);
            const inputs = d.querySelectorAll('input');
            const btns = d.querySelectorAll('button');
            info.push({
                visible,
                text: text.substring(0, 200),
                inputs: Array.from(inputs).map(i => i.placeholder || i.type).filter(Boolean),
                buttons: Array.from(btns).map(b => (b.textContent || '').trim()).filter(Boolean)
            });
        }
    });
    
    return JSON.stringify(info);
})()
"""
    modals = json.loads(cdp.eval(js_modal) or "[]")
    print(f"  弹窗: {len(modals)}个")
    for m in modals:
        print(f"    text: {m.get('text','')[:120]}")
        print(f"    inputs: {m.get('inputs', [])}")
        print(f"    buttons: {m.get('buttons', [])}")
    
    # 7. 如果有关键词输入框，输入"nail"搜索美甲关键词
    print(f"\n【步骤7】输入美妆个护关键词搜索")
    
    # 找搜索输入框并输入
    js_search_nail = """
(() => {
    // 在所有输入框中找可输入的
    const inputs = document.querySelectorAll('input:not([type="hidden"]):not([type="checkbox"])');
    for (const inp of inputs) {
        const ph = inp.placeholder || '';
        if ((ph.includes('搜索') || ph.includes('search') || ph.includes('关键') || ph.includes('key')) && inp.offsetParent !== null) {
            // 模拟输入
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeInputValueSetter.call(inp, 'nail beauty skincare');
            inp.dispatchEvent(new Event('input', { bubbles: true }));
            inp.dispatchEvent(new Event('change', { bubbles: true }));
            return '输入到: ' + ph;
        }
    }
    
    // 如果找不到搜索框, 看弹窗里的输入框
    const dialogs = document.querySelectorAll('.el-dialog[style*="display"], [class*="dialog"][style*="block"]');
    for (const d of dialogs) {
        const inputs = d.querySelectorAll('input');
        for (const inp of inputs) {
            if (inp.offsetParent !== null) {
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeInputValueSetter.call(inp, 'nail beauty skincare');
                inp.dispatchEvent(new Event('input', { bubbles: true }));
                inp.dispatchEvent(new Event('change', { bubbles: true }));
                return '输入到弹窗: ' + (inp.placeholder || '');
            }
        }
    }
    
    return '无可输入框';
})()
"""
    result = cdp.eval(js_search_nail)
    print(f"  输入结果: {result}")
    time.sleep(1)
    
    cdp.shot("stepC_输入搜索词")
    
    # 8. 点搜索/查询按钮
    print(f"\n【步骤8】点击查询/搜索按钮")
    
    js_click_search = """
(() => {
    // 找"查询"或"搜索"按钮
    const btns = document.querySelectorAll('button, a, span, [role="button"]');
    for (const btn of btns) {
        const text = (btn.textContent || '').trim();
        if (text === '搜索' || text === '查询' || text === 'Search' || text === '立即查询') {
            if (btn.offsetParent !== null) {
                btn.click();
                return '点击:' + text;
            }
        }
    }
    // 如果找不到，找弹窗中的确定按钮
    const dialogs = document.querySelectorAll('.el-dialog[style*="block"], .dialog[style*="block"]');
    for (const d of dialogs) {
        const btns = d.querySelectorAll('button, .el-button');
        for (const btn of btns) {
            const text = (btn.textContent || '').trim();
            if (text) {
                btn.click();
                return '点击弹窗:' + text;
            }
        }
    }
    return '未找到查询按钮';
})()
"""
    result = cdp.eval(js_click_search)
    print(f"  点击结果: {result}")
    time.sleep(3)
    
    cdp.shot("stepD_搜索结果")
    
    # 9. 提取搜索结果
    print(f"\n【步骤9】提取搜索结果数据")
    
    js_results = """
(() => {
    // 提取所有可见表格数据
    const table = document.querySelector('.el-table__body, table, [class*="table"]');
    if (!table) return JSON.stringify({message: '未找到表格'});
    
    const rows = table.querySelectorAll('tr');
    const data = [];
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td, .el-table__cell');
        const rowData = [];
        cells.forEach(cell => {
            const text = (cell.textContent || '').trim().substring(0, 100);
            rowData.push(text);
        });
        if (rowData.length > 0) {
            data.push(rowData);
        }
    });
    
    // 列数
    const headers = [];
    document.querySelectorAll('.el-table__header-wrapper th, .el-table__header th, table th').forEach(th => {
        const text = (th.textContent || '').trim();
        if (text) headers.push(text);
    });
    
    return JSON.stringify({
        headers,
        rowCount: data.length,
        rows: data.slice(0, 20)
    });
})()
"""
    results = json.loads(cdp.eval(js_results) or '{"headers":[],"rowCount":0,"rows":[]}')
    print(f"  表头 ({len(results.get('headers',[]))}): {results['headers']}")
    print(f"  数据行: {results.get('rowCount', 0)}")
    
    for r in results.get('rows', [])[:5]:
        print(f"    {r}")
    
    # 汇总
    print(f"\n{'='*70}")
    print("✅ 关键词选品操作完成")
    print(f"{'='*70}")
    
    loaded = results.get('rowCount', 0) > 0 or len(table_data.get('rows', [])) > 0
    if loaded:
        print(f"\n  已提取到 {results.get('rowCount', 0)} 行数据")
        print(f"  数据可用 -> 进入产品搜索验证ASIN")
        print(f"\n  下一阶段: 我在产品搜索页面按类目筛选")
    else:
        print(f"\n  页面数据未加载（需要先选择词库）")
        print(f"  建议: 在浏览器上手动选一个美妆个护词库")
        print(f"         然后我再提取数据")
    
    print(f"\n  当前停留: 关键词选品页面")
    print(f"  截图: {SCREENSHOT_DIR}")
    
    cdp.close()

if __name__ == "__main__":
    main()
