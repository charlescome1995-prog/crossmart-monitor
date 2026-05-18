# -*- coding: utf-8 -*-
"""
前台选品链路 - 在卖家精灵页面显式操作
步骤：关键词选品 → 产品搜索验证 → 竞品分析 → Listing生成
"""
import sys, json, time
sys.stdout.reconfigure(encoding='utf-8')

import websocket, urllib.request, urllib.parse

# ============================================================
# CDP操作
# ============================================================
class SpriteBrowser:
    def __init__(self):
        req = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5)
        tabs = json.loads(req.read())
        
        sprite_tabs = [t for t in tabs if "sellersprite" in (t.get("url","")+t.get("title",""))]
        if sprite_tabs:
            self.tab = sprite_tabs[0]
            print(f"📌 当前页面: {self.tab.get('title','')[:60]}")
        else:
            # 打开卖家精灵
            self.tab = tabs[0]
        
        ws_url = self.tab["webSocketDebuggerUrl"]
        self.ws = websocket.create_connection(ws_url, timeout=10)
        self._msg_id = 0
    
    def cmd(self, method, params=None):
        self._msg_id += 1
        self.ws.send(json.dumps({"method": method, "id": self._msg_id, "params": params or {}}))
        resp = self.ws.recv()
        return json.loads(resp).get("result", {})
    
    def eval(self, js):
        r = self.cmd("Runtime.evaluate", {"expression": js, "returnByValue": True})
        return r.get("result", {}).get("value")
    
    def navigate(self, url, wait=2):
        print(f"\n  → 导航到: {url}")
        self.cmd("Page.navigate", {"url": url})
        time.sleep(wait)
        return self.get_url()
    
    def get_url(self):
        r = self.cmd("Runtime.evaluate", {"expression": "window.location.href", "returnByValue": True})
        return r.get("result", {}).get("value", "")
    
    def get_title(self):
        return self.eval("document.title") or ""
    
    def screenshot(self, name):
        result = self.cmd("Page.captureScreenshot", {"format": "png", "fromSurface": True})
        data = result.get("data", "")
        if data:
            path = f"C:\\Users\\OPENPC\\.openclaw\\workspace\\projects\\amazon_ai_kit\\output\\screenshots\\{name}.png"
            import base64
            with open(path, "wb") as f:
                f.write(base64.b64decode(data))
            print(f"  📸 截图已保存: {name}.png")
        else:
            print(f"  ⚠️ 截图失败")
        return data
    
    def close(self):
        self.ws.close()

# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 70)
    print("🛒 美妆个护选品链路 - 前台操作演示")
    print("   在卖家精灵网页上操作给你看完整流程")
    print("=" * 70)
    
    browser = SpriteBrowser()
    
    # Step 1: 确认在关键词选品页面
    print(f"\n{'='*70}")
    print("【Step 1】关键词选品 - 查找美妆个护产品机会关键词")
    print(f"{'='*70}")
    
    title = browser.get_title()
    url = browser.get_url()
    print(f"  当前标签: {title[:60]}")
    print(f"  当前URL: {url[:80]}")
    
    # 检查页面内容 - 看筛选条件
    js = """
(() => {
    // 获取表格行数据
    const rows = document.querySelectorAll('table tbody tr, .el-table__body tr, [class*="table"] tbody tr');
    return rows.length;
})()
"""
    rows = browser.eval(js) or 0
    print(f"\n  表格行数: {rows}")
    
    # 获取当前筛选条件显示
    js2 = """
(() => {
    // 各种可能的筛选条件显示位置
    const selectors = [
        '.el-input__inner', 'input', '.filter-item', 
        '.condition-item', '[class*="filter"]', 
        '.el-select .el-input__inner'
    ];
    const results = [];
    for (const sel of selectors) {
        const els = document.querySelectorAll(sel);
        els.forEach(el => {
            const val = el.value || el.textContent || '';
            if (val && val.length < 50) {
                results.push(val.trim());
            }
        });
    }
    // 去重
    return [...new Set(results)].slice(0, 20).join(' | ');
})()
"""
    filters = browser.eval(js2) or ""
    print(f"  当前筛选: {filters[:100]}")
    
    # 查看表格列标题
    js3 = """
(() => {
    const headers = [];
    document.querySelectorAll('th, .el-table__header th, [class*="header"] th').forEach(th => {
        const text = (th.textContent || '').trim();
        if (text) headers.push(text);
    });
    return headers.join('  |  ');
})()
"""
    headers = browser.eval(js3) or ""
    print(f"  表格列: {headers[:120]}")
    
    # 查已经选中的品类
    js4 = """
(() => {
    // 找品类选择器
    const all = document.body.innerText;
    // 找关键词筛选输入框
    const inputs = document.querySelectorAll('input[placeholder*="关键词"], input[placeholder*="search"], input[type="text"]');
    const vals = [];
    inputs.forEach(inp => {
        if (inp.value) vals.push(inp.value);
    });
    return vals.join(', ');
})()
"""
    kw_filter = browser.eval(js4) or ""
    print(f"  已输入的关键词过滤: \"{kw_filter}\"")
    
    # Step 2: 导航到产品搜索验证
    print(f"\n{'='*70}")
    print("【Step 2】产品搜索 - 验证美妆个护产品数据")
    print(f"{'='*70}")
    
    try:
        browser.navigate("https://www.sellersprite.com/v3/product-research")
        time.sleep(1)
        
        # 检查是否成功导航
        current = browser.get_url()
        print(f"  导航后URL: {current[:80]}")
        
        if "keyword-research" in current:
            print("  ⚠️ 页面未跳转（SPA单页应用），手动点击导航...")
            # 尝试通过点击侧边栏导航
            click_js = """
(() => {
    // 找选产品的链接
    const links = document.querySelectorAll('a');
    for (const a of links) {
        if (a.href && a.href.includes('product-research') && a.textContent.trim() === '选产品') {
            a.click();
            return '点击选产品';
        }
    }
    // 找任意含有"选产品"的链接或按钮
    const all = document.querySelectorAll('a, button, span, div');
    for (const el of all) {
        if (el.textContent && el.textContent.trim() === '选产品') {
            el.click();
            return '点击选产品元素';
        }
    }
    return '未找到选产品';
})()
"""
            result = browser.eval(click_js) or ""
            print(f"  点击结果: {result}")
            time.sleep(2)
            print(f"  当前URL: {browser.get_url()[:80]}")
            print(f"  当前标题: {browser.get_title()[:60]}")
        
        browser.screenshot("step2_产品搜索页")
        
    except Exception as e:
        print(f"  ❌ 导航失败: {e}")
    
    # Step 3: 关键词挖掘
    print(f"\n{'='*70}")
    print("【Step 3】关键词挖掘 - 美妆个护关键词扩展")
    print(f"{'='*70}")
    
    try:
        # 用location.assign
        browser.cmd("Runtime.evaluate", {
            "expression": "window.location.href = 'https://www.sellersprite.com/v3/keyword-miner'",
            "returnByValue": True
        })
        time.sleep(3)
        print(f"  当前URL: {browser.get_url()[:80]}")
        browser.screenshot("step3_关键词挖掘")
        
    except Exception as e:
        print(f"  ❌ 导航失败: {e}")
    
    # Step 4: 竞品分析
    print(f"\n{'='*70}")
    print("【Step 4】查竞品 - 分析对标ASIN")
    print(f"{'='*70}")
    
    try:
        browser.cmd("Runtime.evaluate", {
            "expression": "window.location.href = 'https://www.sellersprite.com/v3/competitor-lookup'",
            "returnByValue": True
        })
        time.sleep(3)
        print(f"  当前URL: {browser.get_url()[:80]}")
        browser.screenshot("step4_查竞品")
        
    except Exception as e:
        print(f"  ❌ 导航失败: {e}")
    
    # Step 5: 广告洞察
    print(f"\n{'='*70}")
    print("【Step 5】广告洞察 - 评估广告可行性")
    print(f"{'='*70}")
    
    try:
        browser.cmd("Runtime.evaluate", {
            "expression": "window.location.href = 'https://www.sellersprite.com/v3/ads-insights'",
            "returnByValue": True
        })
        time.sleep(3)
        print(f"  当前URL: {browser.get_url()[:80]}")
        browser.screenshot("step5_广告洞察")
        
    except Exception as e:
        print(f"  ❌ 导航失败: {e}")
    
    # Step 6: Listing生成器
    print(f"\n{'='*70}")
    print("【Step 6】Listing生成器 - 生成上架方案")
    print(f"{'='*70}")
    
    try:
        browser.cmd("Runtime.evaluate", {
            "expression": "window.location.href = 'https://www.sellersprite.com/v3/listing-builder'",
            "returnByValue": True
        })
        time.sleep(3)
        print(f"  当前URL: {browser.get_url()[:80]}")
        browser.screenshot("step6_Listing生成器")
        
    except Exception as e:
        print(f"  ❌ 导航失败: {e}")
    
    # Step 7: 关闭
    print(f"\n{'='*70}")
    print(f"✅ 链路操作完成")
    print(f"{'='*70}")
    
    browser.close()

if __name__ == "__main__":
    main()
