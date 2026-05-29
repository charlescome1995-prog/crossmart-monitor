#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词市场监控 - 修复版
关键修复：
1. 不再创建空白标签页（Target.createTarget 会导致连接到错误的标签页）
2. 直接用 navigate() 复用当前标签页导航到搜索页
3. 插件标记格式：自然位：第1页第1位（从 innerText 中提取）
"""
import time
import random
import sys
import os
import re
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser.human_timer import human_pause, read_pause, think_pause


# ─── 工具函数 ──────────────────────────────────────────────────────────────

def random_scroll(browser, times=None, min_pause=1.0, max_pause=2.0):
    t = times if times is not None else random.randint(1, 3)
    for _ in range(t):
        amt = random.randint(300, 700)
        browser.eval("window.scrollBy(0, " + str(amt) + ")")
        time.sleep(random.uniform(min_pause, max_pause))


def random_hovers(browser, count=None):
    n = count if count is not None else random.randint(1, 3)
    browser.eval(
        "((n) => {"
        "const els = document.querySelectorAll('.s-result-item[data-component-type=\"s-search-result\"]');"
        "const picks = Array.from(els).sort(() => Math.random() - 0.5).slice(0, n);"
        "picks.forEach((el, i) => {"
        "setTimeout(() => el.dispatchEvent(new MouseEvent('mouseenter', {bubbles:true})), i * 800);"
        "});"
        "})(" + str(n) + ")"
    )


def wait_for_render(browser, min_sec=4, max_sec=8):
    time.sleep(random.uniform(min_sec, max_sec))


# ─── 数据提取 ──────────────────────────────────────────────────────────

def extract_asin_marks_from_page(browser):
    """
    从亚马逊搜索结果页提取所有商品标记。
    插件格式（从 innerText 中提取）：
      自然位：第1页第1位  →  type = "natural"
      广告位：第1页第2位  →  type = "ad"
      新品位：第1页第1位  →  type = "new"
    """
    js = r"""
    (function() {
        var results = [];
        var items = document.querySelectorAll('.s-result-item[data-component-type="s-search-result"]');

        for (var i = 0; i < items.length; i++) {
            (function(item) {
                var markType = '';
                var rankText = '';
                var asin = '';

                var inner = item.innerText || '';

                // 卖家精灵插件格式：自然位：第1页第1位
                var naturalMatch = inner.match(/\u81ea\u7136\u4f4d[：:]\u7b2c(\d+)\u9875\u7b2c(\d+)\u4f4d/);
                var adMatch = inner.match(/\u5e7f\u544a\u4f4d[：:]?\u7b2c(\d+)\u9875\u7b2c(\d+)\u4f4d/);
                var newMatch = inner.match(/\u65b0\u54c1\u4f4d[：:]?\u7b2c(\d+)\u9875\u7b2c(\d+)\u4f4d/);

                if (naturalMatch) {
                    markType = 'natural';
                    rankText = '\u81ea\u7136\u4f4d\uff1a\u7b2c' + naturalMatch[1] + '\u9875\u7b2c' + naturalMatch[2] + '\u4f4d';
                } else if (adMatch) {
                    markType = 'ad';
                    rankText = '\u5e7f\u544a\u4f4d\uff1a\u7b2c' + adMatch[1] + '\u9875\u7b2c' + adMatch[2] + '\u4f4d';
                } else if (newMatch) {
                    markType = 'new';
                    rankText = '\u65b0\u54c1\u4f4d\uff1a\u7b2c' + newMatch[1] + '\u9875\u7b2c' + newMatch[2] + '\u4f4d';
                } else {
                    var spon = item.closest('[class*="sponsorship"], [class*="sponsored"], [data-component-type*="sponsored"]');
                    if (spon) {
                        markType = 'ad';
                        rankText = 'ad';
                    }
                }

                var link = item.querySelector('a.a-link-normal[href*="/dp/"]');
                if (link) {
                    var match = link.href.match(/\/dp\/([A-Z0-9]{10})/);
                    if (match) asin = match[1];
                }

                var titleEl = item.querySelector('h2.a-size-base-plus, h2.a-size-medium, h2');
                var title = titleEl ? (titleEl.innerText || '') : '';

                var priceEl = item.querySelector('.a-price .a-offscreen, .a-price-whole');
                var price = priceEl ? (priceEl.innerText || '') : '';

                var ratingEl = item.querySelector('.a-icon-star-small, .a-icon-star');
                var rating = ratingEl ? (ratingEl.innerText || '') : '';

                var reviews = '';
                var revEl = item.querySelector('[aria-label*="star"], .a-size-base');
                if (revEl) {
                    var m = revEl.innerText.match(/([\d,]+)/);
                    if (m) reviews = m[1];
                }

                if (asin) {
                    results.push({ asin: asin, type: markType || 'unknown', rank: rankText, title: title, price: price, rating: rating, reviews: reviews });
                }
            })(items[i]);
        }
        return results;
    })()
    """
    try:
        raw = browser.eval(js)
        return raw if isinstance(raw, list) else []
    except Exception as e:
        print("  [extract_asin_marks] JS error: " + str(e))
        return []


def group_and_pick_top5(marks):
    """
    从所有标记结果中精选 Top5 ASIN：
      优先级：natural_top1 > ad_top1 > new_natural_top1 > new_ad_top1 > natural_other
    同类型按排名数字排序。
    """
    natural = [m for m in marks if m.get("type") == "natural"]
    ad = [m for m in marks if m.get("type") == "ad"]
    new_list = [m for m in marks if m.get("type") == "new"]
    other = [m for m in marks if m.get("type") not in ("natural", "ad", "new")]

    def rank_num(m):
        t = m.get("rank", "")
        if not t:
            return 999
        nums = re.findall(r"\d+", t)
        return int(nums[-1]) if nums else 999

    natural.sort(key=rank_num)
    ad.sort(key=rank_num)
    new_list.sort(key=rank_num)

    selected = []
    seen = set()

    def pick(src, label):
        for m in src:
            if m.get("asin") not in seen:
                m["_label"] = label
                selected.append(m)
                seen.add(m.get("asin"))
                return

    pick(natural[:1], "natural_top1")
    pick(ad[:1], "ad_top1")
    pick(new_list[:1], "new_natural_top1")
    pick(ad[1:2], "new_ad_top1")
    pick(natural[1:2], "natural_other")

    # 填充剩余位置（避免重复）
    all_pool = natural + ad + new_list + other
    for m in all_pool:
        if m.get("asin") not in seen and len(selected) < 5:
            m["_label"] = "fill"
            selected.append(m)
            seen.add(m.get("asin"))

    return selected[:5]


# ─── 主搜索流程 ─────────────────────────────────────────────────────────

def do_keyword_search(browser, keyword):
    """搜索关键词，模拟人类行为"""
    sep = "=" * 60
    print("\n" + sep)
    print("Keyword market: " + keyword)
    print(sep)

    # ── 1. 直接导航到搜索页（navigate 会自动处理 WebSocket 重连） ──
    search_url = "https://www.amazon.com/s?k=" + keyword.replace(" ", "+") + "&ref=nb_sb_noss"
    print("  Navigating to: " + search_url)
    browser.navigate(search_url, wait_min=2, wait_max=4)
    wait_s = random.uniform(6, 10)
    print("  Waiting " + str(int(wait_s)) + "s for Seller Sprite plugin to render...")
    time.sleep(wait_s)

    # ── 3. 随机滚动 ────────────────────────────────────
    random_scroll(browser, times=random.randint(1, 2))
    human_pause(2, 5)

    # ── 4. 随机悬停 ────────────────────────────────────
    random_hovers(browser, count=random.randint(1, 3))

    # ── 5. 回到搜索结果页 ──────────────────────────────
    browser._refresh_tabs()
    for t in browser._raw_tabs:
        if "amazon.com/s" in t.get("url", "") and "view-source" not in t.get("url", ""):
            browser.connect_tab(tab_index=browser._raw_tabs.index(t))
            break

    random_scroll(browser, times=2)
    wait_for_render(browser, min_sec=2, max_sec=4)
    human_pause(2, 5)

    # ── 6. 提取数据 ────────────────────────────────────
    print("  Extracting search result data...")
    marks = extract_asin_marks_from_page(browser)
    print("  Found " + str(len(marks)) + " product results")
    for m in marks[:5]:
        t = m.get("type", "")
        a = m.get("asin", "")
        title = str(m.get("title", "")[:40])
        print("     [" + t.ljust(15) + "] " + a + " | " + title)

    top_asins = group_and_pick_top5(marks)
    print("  Top5 ASINs:")
    for a in top_asins:
        print("     [" + str(a.get("type", "")).ljust(20) + "] " + a.get("asin", "") + " | " + a.get("price", ""))

    return marks, top_asins


# ─── 入口 ──────────────────────────────────────────────────────────────

def check_keyword(keyword):
    """关键词监控主函数"""
    from browser.amazon_browser import CDPBrowser

    browser = CDPBrowser()

    marks = []
    top_asins = []
    sep = "=" * 60

    try:
        marks, top_asins = do_keyword_search(browser, keyword)
    except Exception as e:
        print("  Amazon search failed: " + str(e))
        import traceback
        traceback.print_exc()
        marks, top_asins = [], []

    snapshot = {
        "keyword": keyword,
        "timestamp": datetime.now().isoformat(),
        "result_count": len(marks),
        "top_asins": [
            {
                "asin": a.get("asin", ""),
                "type": a.get("type", ""),
                "rank": a.get("rank", ""),
                "title": a.get("title", ""),
                "price": a.get("price", ""),
                "rating": a.get("rating", ""),
                "reviews": a.get("reviews", ""),
            }
            for a in top_asins
        ],
        "raw_marks": [
            {"asin": a.get("asin", ""), "type": a.get("type", ""), "rank": a.get("rank", "")}
            for a in marks[:50]
        ]
    }

    # 保存快照
    _data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _snap_dir = os.path.join(_data_dir, "data", "processed", "kw_" + keyword.replace(" ", "_").replace("/", "_"))
    os.makedirs(_snap_dir, exist_ok=True)
    _ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    _snap_file = os.path.join(_snap_dir, "snapshot_" + _ts + ".json")
    with open(_snap_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    latest_file = os.path.join(_snap_dir, "latest.json")
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    browser.close()

    print("\n" + sep)
    print("Keyword [" + keyword + "] check done, found " + str(len(top_asins)) + " target ASINs")
    print(sep)

    return snapshot


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Keyword market monitoring")
    parser.add_argument("keyword", nargs="?", help="Keyword")
    args = parser.parse_args()

    if not args.keyword:
        print("Usage: python keyword_monitor.py 'batana oil'")
        sys.exit(1)

    check_keyword(args.keyword)