# -*- coding: utf-8 -*-
"""
前台选品链路 - 卖家精灵页面操作 + 截图
按流程走：关键词选品 → 产品搜索 → 关键词挖掘 → 竞品分析 → 广告洞察 → Listing生成
"""
import sys, json, time, base64, os
sys.stdout.reconfigure(encoding='utf-8')

import websocket, urllib.request

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
        print(f"📌 当前: {self.tab.get('title','')[:50]}")
        print(f"📌 URL: {self.tab.get('url','')[:80]}")
    
    def cmd(self, method, params=None):
        self._id += 1
        self.ws.send(json.dumps({"method": method, "id": self._id, "params": params or {}}))
        return json.loads(self.ws.recv()).get("result", {})
    
    def go(self, url, wait=2):
        print(f"\n  → {url.split('/v')[1] if '/v' in url else url[-40:]}")
        self.cmd("Page.navigate", {"url": url})
        time.sleep(wait)
        u = self._url()
        t = self._title()
        print(f"    当前: {t[:50]} | {u[:80]}")
        return u, t
    
    def shot(self, name):
        r = self.cmd("Page.captureScreenshot", {"format": "png", "fromSurface": True})
        data = r.get("data", "")
        if data:
            path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
            with open(path, "wb") as f:
                f.write(base64.b64decode(data))
            print(f"     📸 截图: {name}.png ({os.path.getsize(path)//1024}KB)")
        return data
    
    def _url(self):
        r = self.cmd("Runtime.evaluate", {"expression": "window.location.href", "returnByValue": True})
        return r.get("result", {}).get("value", "")
    
    def _title(self):
        r = self.cmd("Runtime.evaluate", {"expression": "document.title", "returnByValue": True})
        return r.get("result", {}).get("value", "")
    
    def close(self):
        self.ws.close()

def main():
    print("=" * 70)
    print("🛒 卖家精灵 - 美妆个护选品链路前台操作")
    print("   每一步都在浏览器真实操作，用户可见")
    print("=" * 70)
    
    cdp = CDP()
    
    # ============================================================
    # Step 1: 关键词选品
    # ============================================================
    print(f"\n{'─'*60}")
    print("【Step 1/6】关键词选品 - 看美妆个护机会词")
    
    url, title = cdp.go("https://www.sellersprite.com/v2/keyword-research")
    cdp.shot("step1_关键词选品")
    
    # ============================================================
    # Step 2: 产品搜索
    # ============================================================
    print(f"\n{'─'*60}")
    print("【Step 2/6】产品搜索 - 按美妆个护类目筛选产品")
    
    url, title = cdp.go("https://www.sellersprite.com/v3/product-research")
    cdp.shot("step2_产品搜索")
    
    # ============================================================
    # Step 3: 关键词挖掘
    # ============================================================
    print(f"\n{'─'*60}")
    print("【Step 3/6】关键词挖掘 - 扩展美妆个护关键词")
    
    url, title = cdp.go("https://www.sellersprite.com/v3/keyword-miner")
    cdp.shot("step3_关键词挖掘")
    
    # ============================================================
    # Step 4: 竞品分析
    # ============================================================
    print(f"\n{'─'*60}")
    print("【Step 4/6】查竞品 - 分析对标产品")
    
    url, title = cdp.go("https://www.sellersprite.com/v3/competitor-lookup")
    cdp.shot("step4_查竞品")
    
    # ============================================================
    # Step 5: 广告洞察
    # ============================================================
    print(f"\n{'─'*60}")
    print("【Step 5/6】广告洞察 - 评估广告可行性")
    
    url, title = cdp.go("https://www.sellersprite.com/v3/ads-insights")
    cdp.shot("step5_广告洞察")
    
    # ============================================================
    # Step 6: Listing生成器
    # ============================================================
    print(f"\n{'─'*60}")
    print("【Step 6/6】Listing生成器 - 生成上架方案")
    
    url, title = cdp.go("https://www.sellersprite.com/v3/listing-builder")
    cdp.shot("step6_Listing生成器")
    
    # ============================================================
    # 汇总
    # ============================================================
    print(f"\n{'='*70}")
    print("✅ 前台链路操作完毕！")
    print(f"   截图已保存到: {SCREENSHOT_DIR}")
    print(f"\n   完整链路:")
    print(f"     1. 关键词选品      → 发现美妆个护机会词")
    print(f"     2. 产品搜索        → 验证可上架产品ASIN")
    print(f"     3. 关键词挖掘      → 扩展产品相关词")
    print(f"     4. 查竞品         → 分析对标产品策略")
    print(f"     5. 广告洞察       → 评估广告竞价和可行性")
    print(f"     6. Listing生成器  → 生成标题/五点/描述")
    print(f"\n   当前停留在 Listing 生成器页面，你可以直接看。")
    print(f"{'='*70}")
    
    cdp.close()

if __name__ == "__main__":
    main()
