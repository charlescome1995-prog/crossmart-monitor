#!/usr/bin/env python3
import sys, os, time, json
sys.stdout.reconfigure(encoding='utf-8')
_backend = r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend"
sys.path.insert(0, _backend)
from browser.cdp_bridge import CDPBrowser

browser = CDPBrowser()
browser.connect_tab(tab_url_filter="about:blank")
if not browser.tab:
    browser.cmd("Target.createTarget", {"url": "about:blank"})
    time.sleep(1)
    browser.connect_tab(tab_url_filter="about:blank")

TEST_ASIN = "B09542G9ZN"

browser.navigate("https://www.sellersprite.com/v3/competitor-lookup", wait_min=3, wait_max=6)
time.sleep(5)

# 输入ASIN
browser.eval("""
(function(){
    var inputs = document.querySelectorAll('input');
    for (var i = 0; i < inputs.length; i++) {
        if ((inputs[i].placeholder || '').includes('ASIN')) {
            inputs[i].focus();
            inputs[i].value = '';
            var t = 'B09542G9ZN';
            for (var j = 0; j < t.length; j++) {
                inputs[i].value += t[j];
                inputs[i].dispatchEvent(new Event('input', {bubbles: true}));
            }
            return inputs[i].value;
        }
    }
})()
""")

time.sleep(0.5)

# 点"立即查询"
browser.eval("""
(function(){
    var btns = document.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {
        if ((btns[i].textContent || '').trim() === '立即查询') {
            btns[i].click();
            return 'clicked';
        }
    }
})()
""")

# 每2秒检查一次数据就绪
print("等待数据加载...")
for i in range(20):
    time.sleep(2)
    rows = browser.eval("""
    (function(){
        var rows = document.querySelectorAll('.el-table__body tr');
        return rows.length;
    })()
    """)
    print(f"  {i*2}s: {rows} rows")
    if rows >= 5:
        print("  数据已就绪!")
        break

# 获取完整表格数据（用更好的解析）
print("\n=== 完整竞品数据表格 ===")
table_data = browser.eval("""
(function(){
    var rows = document.querySelectorAll('.el-table__body tr');
    var result = [];
    for (var i = 0; i < rows.length; i++) {
        var cells = rows[i].querySelectorAll('td');
        if (cells.length === 0) continue;
        var rowData = {
            rank: i + 1,
            cells: Array.from(cells).map(function(c){return (c.textContent||'').trim();})
        };
        result.push(rowData);
    }
    return JSON.stringify(result);
})()
""")
data = json.loads(table_data)
for row in data[:5]:
    print(f"Row {row['rank']}: {row['cells']}")

# 分析每列含义
print("\n=== 分析每列内容 ===")
first_row = data[0]['cells'] if data else []
for i, cell in enumerate(first_row):
    print(f"  Col {i}: {repr(cell[:40])}")

browser.close()