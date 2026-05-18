#!/usr/bin/env python3
"""可见化演示"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_bridge import CDPBrowser

b = CDPBrowser()
b.connect_tab(tab_index=0)

print("=" * 50)
print("🖥️  看浏览器！我在操作了")
print("=" * 50)
time.sleep(1)

# 1. 搜一个关键词
print("\n[1] 搜索 'beauty nail oil' ...")
time.sleep(0.5)
b.navigate("https://www.amazon.com/s?k=beauty+nail+oil")
time.sleep(2)

# 2. 打开一个ASIN详情页
print("\n[2] 打开商品详情...")
time.sleep(0.5)
b.navigate("https://www.amazon.com/dp/B0DCX7628T")
time.sleep(2)

# 3. 提取标题
print("\n[3] 提取数据...")
title = b.eval("document.querySelector('#productTitle')?.textContent?.trim() || 'N/A'")
price = b.eval("document.querySelector('.a-price-whole')?.textContent?.trim() || 'N/A'")
print(f"  标题: {title[:60]}")
print(f"  价格: ${price}")

print("\n✅ 看到了吗？浏览器在自动导航和提取数据")
b.close()
