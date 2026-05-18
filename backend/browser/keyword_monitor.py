#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词市场监控主入口
"""
import sys, os, json, random
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from browser.cdp_bridge import CDPBrowser
from browser.amazon_browser import AmazonBrowser
from browser.sprite_bridge import SpriteBrowser
from browser.snapshot_storage import save_keyword_snapshot
from browser.human_timer import get_daily_plan


def check_keyword(keyword, use_sprite=True):
    print(f"\n{'='*70}")
    print(f"🔍 关键词市场: {keyword}")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

    screenshot_paths = []
    amazon_data = {}
    sprite_data = {}

    browser = CDPBrowser()

    # 亚马逊前台
    print(f"\n{'='*50}")
    print("📦 亚马逊前台: 搜索浏览")
    print(f"{'='*50}")
    try:
        amazon = AmazonBrowser(browser)
        amazon.full_keyword_check(keyword)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        from browser.cdp_bridge import SCREENSHOT_DIR as ss_dir
        for f in os.listdir(ss_dir):
            if keyword.replace(" ", "_")[:20] in f and ts[:8] in f:
                screenshot_paths.append(os.path.join(ss_dir, f))

        result_count = browser.get_text(".a-section.a-spacing-small.a-spacing-top-small span")
        amazon_data["result_count"] = (result_count or "").strip()[:100]
    except Exception as e:
        print(f"  ⚠️ 亚马逊部分失败: {e}")

    # 卖家精灵
    if use_sprite:
        print(f"\n{'='*50}")
        print("📊 卖家精灵: 关键词数据")
        print(f"{'='*50}")
        try:
            browser.open_new_tab("https://www.sellersprite.com")
            sprite = SpriteBrowser(browser)
            kw_data = sprite.search_keyword(keyword)
            sprite_data = kw_data
        except Exception as e:
            print(f"  ⚠️ 卖家精灵失败: {e}")

    browser.close()

    save_keyword_snapshot(keyword, {"keyword": keyword, "amazon": amazon_data, "sprite": sprite_data, "screenshots": screenshot_paths})

    print(f"\n{'='*70}")
    print(f"✅ 关键词检查完成: {keyword}")
    print(f"{'='*70}")
    return {"keyword": keyword}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="关键词监控")
    parser.add_argument("keyword", nargs="?", help="关键词")
    parser.add_argument("--no-sprite", action="store_true")
    args = parser.parse_args()

    if not args.keyword:
        print("python browser/keyword_monitor.py 'keyword here'")
        sys.exit(1)

    check_keyword(args.keyword, use_sprite=not args.no_sprite)
