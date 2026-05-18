# -*- coding: utf-8 -*-
"""检查卖家精灵页面状态"""
import sys, json, time
sys.stdout.reconfigure(encoding='utf-8')

import websocket, urllib.request

# 连CDP
req = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5)
tabs = json.loads(req.read())

# 找卖家精灵
sprite_tabs = [t for t in tabs if "sellersprite" in (t.get("url","") + t.get("title",""))]
if not sprite_tabs:
    print("❌ 未找到卖家精灵页面")
    sys.exit(1)

print(f"全部标签页: {len(tabs)}")
print(f"卖家精灵标签: {len(sprite_tabs)}\n")

for t in sprite_tabs:
    print(f"  title: {t.get('title','')[:50]}")
    print(f"  url:   {t.get('url','')[:90]}")
    print()

# 取第一个
tab = sprite_tabs[0]
ws_url = tab["webSocketDebuggerUrl"]
ws = websocket.create_connection(ws_url, timeout=10)

def cmd(method, params=None):
    msg_id = int(time.time() * 10000) % 1000000
    data = {"method": method, "id": msg_id, "params": params or {}}
    ws.send(json.dumps(data))
    resp = ws.recv()
    return json.loads(resp).get("result", {})

# 获取所有可点击的导航链接
js = """
(() => {
    const items = [];
    
    // 侧边栏菜单
    document.querySelectorAll('a, [role="menuitem"], .menu-item, .nav-item, li a').forEach(el => {
        const href = el.href || el.getAttribute('href') || '';
        const text = (el.textContent || el.innerText || '').trim().substring(0, 35);
        if (text && href && !href.startsWith('javascript:') && href.includes('sellersprite')) {
            const short = href.replace('https://www.sellersprite.com', '');
            if (!items.some(i => i.href === short)) {
                items.push({text, href: short});
            }
        }
    });
    
    // 顶部导航
    document.querySelectorAll('nav a, header a, .navbar a, .top-nav a').forEach(el => {
        const href = el.href || el.getAttribute('href') || '';
        const text = (el.textContent || el.innerText || '').trim().substring(0, 35);
        if (text && href && !href.startsWith('javascript:') && href.includes('sellersprite')) {
            const short = href.replace('https://www.sellersprite.com', '');
            if (!items.some(i => i.href === short)) {
                items.push({text, href: short});
            }
        }
    });
    
    return JSON.stringify(items);
})()
"""

result = cmd("Runtime.evaluate", {
    "expression": js,
    "returnByValue": True
})

items = json.loads(result.get("result", {}).get("value", "[]"))
print(f"\n=== 卖家精灵导航菜单 ({len(items)}项) ===")
print(f"{'功能名称':30s} URL路径")
print("-" * 60)
for item in sorted(items, key=lambda x: x["href"]):
    print(f"  {item['text']:30s} {item['href']}")

# 检查当前页面
current_url = tab.get("url", "")
print(f"\n当前页面: {current_url[:90]}")

# 提取美妆个护相关网址
print(f"\n\n美妆个护链路URL清单:")
urls = {
    "关键词选品": "https://www.sellersprite.com/v2/keyword-research",
    "产品搜索": "https://www.sellersprite.com/v3/product-research",
    "关键词挖掘": "https://www.sellersprite.com/v3/keyword-miner",
    "关键词反查": "https://www.sellersprite.com/v3/keyword-reverse",
    "广告洞察": "https://www.sellersprite.com/v3/ads-insights",
    "查流量来源": "https://www.sellersprite.com/v3/reversing",
    "查竞品": "https://www.sellersprite.com/v3/competitor-lookup",
    "Listing生成器": "https://www.sellersprite.com/v3/listing-builder",
    "市场分析": "https://www.sellersprite.com/v3/market-analysis",
}
for name, url in urls.items():
    print(f"  {name:15s} → {url}")

ws.close()
