#!/usr/bin/env python3
"""从Edge收藏夹打开卖家精灵已保存的搜索"""
import sys, os, time, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_bridge import CDPBrowser

b = CDPBrowser()

# 先看看收藏夹在哪
b.connect_tab()
b.navigate("edge://bookmarks/")
time.sleep(2)

# 在读收藏夹之前，先看看seller sprite相关标签
bookmarks = b.eval("""
(() => {
    const items = document.querySelectorAll('[url], a, .url');
    const results = [];
    for (const el of items) {
        const url = el.getAttribute('url') || el.href || el.textContent;
        if (url && url.includes('sellersprite')) {
            results.push(url.substring(0, 120));
        }
    }
    return JSON.stringify(results.slice(0, 10));
})()
""")
if bookmarks:
    bm = json.loads(bookmarks)
    print("Bookmarks found:", len(bm))
    for b in bm:
        print(f"  {b}")
else:
    print("No bookmarks found via DOM")
    # 直接读书签文件
    bm_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Bookmarks")
    if os.path.exists(bm_path):
        with open(bm_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        roots = data.get("roots", {})
        def walk(node, depth=0):
            results = []
            if isinstance(node, dict):
                url = node.get("url", "")
                if "sellersprite" in url:
                    results.append(url[:120])
                for child in node.get("children", []):
                    results.extend(walk(child, depth+1))
            return results
        urls = walk(roots)
        print(f"\n书签文件中找到 {len(urls)} 个卖家精灵链接:")
        for u in urls:
            print(f"  {u}")
    else:
        print(f"书签文件不存在: {bm_path}")

b.close()
