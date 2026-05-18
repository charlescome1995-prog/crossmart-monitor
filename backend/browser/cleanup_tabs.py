#!/usr/bin/env python3
"""清理冗余标签页"""
import sys, os, json, time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_bridge import CDPBrowser

b = CDPBrowser()
b.connect_tab(tab_index=0)

print(f"\n当前 {len(b._raw_tabs)} 个标签页")

# 列出所有
for i, t in enumerate(b._raw_tabs):
    url = t.get("url","")[:50]
    title = t.get("title","")[:30]
    print(f"  #{i}: [{title}] {url}")

# 关不要的
keep_urls = ["amazon.com", "sellersprite.com", "pixso.cn", "127.0.0.1:18802", "edge://newtab", "chrome-extension"]
closed = 0
for t in b._raw_tabs:
    url = t.get("url","")
    title = t.get("title","")
    tid = t.get("id","")
    if "Service Worker" in title:
        b.cmd("Target.closeTarget", {"targetId": tid})
        closed += 1
        continue
    keep = any(k in url for k in keep_urls)
    if not keep and url and not url.startswith("chrome-extension"):
        b.cmd("Target.closeTarget", {"targetId": tid})
        closed += 1
        time.sleep(0.2)

print(f"\n关闭了 {closed} 个")
time.sleep(1)

b._refresh_tabs()
print(f"剩余 {len(b._raw_tabs)} 个")
for i, t in enumerate(b._raw_tabs):
    print(f"  #{i}: {t.get('title','')[:30]} | {t.get('url','')[:60]}")

b.close()
