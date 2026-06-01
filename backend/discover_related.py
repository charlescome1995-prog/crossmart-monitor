#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
discover_related.py
通过卖家精灵「查竞品」功能，自动发现主 ASIN 的关联竞品 ASIN 列表。
用法: python discover_related.py B09V7Z4TJG
输出: JSON 数组（每个元素 {"asin": "B0XXXXXXX", "name": "..."}），输出到 stdout
"""
import sys, os, json, time, re
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from browser.cdp_bridge import CDPBrowser
from browser.sprite_bridge import SpriteBrowser

ASIN = sys.argv[1].strip() if len(sys.argv) > 1 else ""
if not ASIN:
    print("[]")
    sys.exit(0)

def find_related():
    browser = CDPBrowser()
    browser.connect_tab(tab_url_filter="about:blank")
    if not browser.tab:
        browser.cmd("Target.createTarget", {"url": "about:blank"})
        time.sleep(0.5)
        browser.connect_tab(tab_url_filter="about:blank")

    try:
        sprite = SpriteBrowser(browser)
        # 调用卖家精灵竞品查询
        result = sprite.lookup_competitor(ASIN)
        page_text = result.get("text", "") if isinstance(result, dict) else ""

        # 从页面文本提取所有 B0 开头的 ASIN
        found = re.findall(r'B[A-Z0-9]{9,10}', page_text)
        related = []
        seen = set()
        for a in found:
            a = a.strip()
            if a != ASIN and a not in seen and len(a) == 10 and a.startswith('B0'):
                seen.add(a)
                related.append({"asin": a, "source": "competitor"})
        return related[:5]
    except Exception as e:
        print(f"  [竞品发现] 错误: {e}", file=sys.stderr)
        return []
    finally:
        try:
            browser.close()
        except:
            pass

if __name__ == "__main__":
    related = find_related()
    print(json.dumps(related, ensure_ascii=False))