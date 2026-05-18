"""Playwright - 出单词反查指定ASIN"""
import json,time,re
from playwright.sync_api import sync_playwright

TARGET = "B00DYMYRX2"
print(f"目标ASIN: {TARGET}")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    pages = [pg for ctx in browser.contexts for pg in ctx.pages]
    target = None
    for pg in pages:
        if "reverse.search" in pg.url:
            target = pg
            break
    if not target:
        target = browser.new_page()
        target.goto("https://www.sellersprite.com/v2/aba/reverse/search", wait_until="domcontentloaded", timeout=15000)
        time.sleep(5)
    
    print(f"页面: {target.title()}")
    
    # 填ASIN到input[25]
    target.evaluate("""
    (asin) => {
        var inps = document.querySelectorAll('input');
        var inp = inps[25];
        if (!inp) return;
        inp.focus();
        inp.scrollIntoView({behavior:'smooth',block:'center'});
        var ns = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        ns.call(inp, asin);
        inp.dispatchEvent(new Event('input', {bubbles: true}));
        inp.dispatchEvent(new Event('change', {bubbles: true}));
    }
    """, TARGET)
    time.sleep(1)
    
    # 点立即查询
    target.evaluate("""
    () => {
        var btns = document.querySelectorAll('button');
        for (var b of btns) {
            if ((b.textContent || '').trim().includes('立即查询')) {
                b.click();
                return;
            }
        }
    }
    """)
    print("已提交查询")
    time.sleep(10)
    
    # 提取结果关键词
    data = target.evaluate("""
    () => {
        // 找结果区域的表格行
        var rows = document.querySelectorAll('tr');
        var result = [];
        rows.forEach(function(row) {
            var cells = row.querySelectorAll('td');
            var rowData = [];
            cells.forEach(function(cell) {
                var t = cell.textContent.trim();
                if (t) rowData.push(t.substring(0, 100));
            });
            if (rowData.length > 1) result.push(rowData);
        });
        return JSON.stringify({rows: result.length, data: result.slice(0, 30)});
    }
    """)
    
    if data:
        d = json.loads(data)
        print(f"表格行: {d.get('rows',0)}")
        rows = d.get('data', [])
        for i, row in enumerate(rows[:10]):
            print(f"  [{i}] {' | '.join(row[:5])[:150]}")
        
        # 关键词通常在第二列
        keywords = []
        for row in rows:
            if len(row) >= 2:
                kw = row[1].strip()
                if re.match(r'^[a-z][a-z\s]{2,30}$', kw, re.I) and len(kw) > 3:
                    keywords.append(kw)
        if keywords:
            print(f"\n✅ 关键词列表: {keywords[:10]}")
        else:
            print("\n没有找到关键词")
    
    # fallback: 直接拿页面文本
    text = target.inner_text("body") or ""
    print(f"\n页面文本: {len(text)} 字符")
    # 找关键词形状的文字
    words = re.findall(r'\b[a-z][a-z\s]{2,25}[a-z]\b', text, re.I)
    unique_words = list(dict.fromkeys([w.lower() for w in words]))
    print(f"可能的关键词: {unique_words[:15]}")

    browser.close()
