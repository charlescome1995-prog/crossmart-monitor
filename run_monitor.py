#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速监控测试 - 抓取单个ASIN的完整数据"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')

_backend = r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend"
sys.path.insert(0, _backend)

import browser.cdp_bridge as cdp
cdp.EDGE_PORT = 9225
cdp._USER_SET_PORT = 9225

import importlib
import browser.asin_monitor as am
importlib.reload(am)

asin = sys.argv[1] if len(sys.argv) > 1 else "B017PCGABI"
print(f"\n=== 测试 ASIN: {asin} ===")

browser = cdp.CDPBrowser()
browser.connect_tab(tab_url_filter=asin)

# Wait for page
for i in range(30):
    r = browser.eval("(function(){var el=document.querySelector('#productTitle');return el&&el.textContent.trim()?{ok:true}:{ok:false};})()")
    if r and r.get('ok'):
        print(f"Page ready ({i+1}s)")
        break
    time.sleep(1)
else:
    print("Page never ready, trying anyway...")

time.sleep(3)  # Wait for plugin

# Extract Amazon data
amazon_data = am.extract_asin_data(browser)
print(f"\n[Amazon Data]")
print(f"  title: {amazon_data.get('title','')[:60]}")
print(f"  price: {amazon_data.get('price','')}")
print(f"  rating: {amazon_data.get('rating','')}")
print(f"  review_count: {amazon_data.get('review_count','')}")

# Extract plugin data (now handles clicking the product query button internally)
print(f"\n[Plugin Data] 提取中（需点击插件按钮）...")
plugin_data = am.extract_sprite_plugin_data(browser)
if plugin_data:
    print(f"[Plugin Data] 获取到 {len(plugin_data)} 个字段")
    for k in ['plugin_version', 'lqs', 'sales_30d_parent', 'revenue_30d', 'variant_count', 'launch_date', 'gross_margin', 'total_keywords']:
        v = plugin_data.get(k)
        if v:
            print(f"  {k}: {v}")
else:
    print("[Plugin Data] 未检测到数据")

# Merge plugin data into amazon_data
if plugin_data:
    for k, v in plugin_data.items():
        amazon_data['sprite_' + k] = v

# Check which sprite_ fields are present
sprite_fields = [k for k in amazon_data.keys() if k.startswith('sprite_')]
print(f"\n[sprite_ fields in amazon_data]: {sprite_fields}")

# Save snapshot
from browser.snapshot_storage import save_asin_snapshot
save_asin_snapshot(asin, amazon_data)

browser.close()
print("\n=== 完成 ===")