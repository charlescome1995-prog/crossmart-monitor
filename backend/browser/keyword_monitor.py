#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keyword market monitoring - Full version
Key fixes:
1. Each keyword search uses an independent new tab (avoids session state confusion)
2. After navigate, wait up to 15s for Seller Sprite plugin markers to appear
3. Keyword related ASINs use keep-old logic (cached in keyword_related_asins.json)
"""
import time
import random
import sys
import os
import re
import json
import websocket
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser.human_timer import human_pause, read_pause, think_pause


# --- Tool Functions ---

def random_scroll(browser, times=None, min_pause=0.3, max_pause=0.8):
    t = times if times is not None else random.randint(1, 2)
    for _ in range(t):
        amt = random.randint(300, 700)
        browser.eval("window.scrollBy(0, " + str(amt) + ")")
        time.sleep(random.uniform(min_pause, max_pause))


def random_hovers(browser, count=None):
    n = count if count is not None else random.randint(1, 2)
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


def wait_for_plugin_markers(browser, timeout=15):
    """Wait for Seller Sprite plugin markers (polling every 2s, max timeout seconds)"""
    start = time.time()
    while time.time() - start < timeout:
        result = browser.eval("""
            (function() {
                var markerCount = 0;
                var items = document.querySelectorAll('.s-result-item[data-component-type="s-search-result"]');
                for (var i = 0; i < items.length; i++) {
                    var inner = items[i].innerText || '';
                    if (inner.indexOf('\u81ea\u7136\u4f4d') >= 0 || inner.indexOf('\u5e7f\u544a\u4f4d') >= 0) {
                        markerCount++;
                    }
                }
                return markerCount;
            })()
        """)
        if result and result > 0:
            print("  [plugin] Detected " + str(result) + " marked products (appeared after " + str(round(time.time() - start, 1)) + "s)")
            return True
        time.sleep(1)
    print("  [plugin] Timeout, using pure DOM results")
    return False


# --- Data Extraction ---

def extract_asin_marks_from_page(browser):
    """
    Extract all product marks from Amazon search results page.
    Plugin format (from innerText):
      natural position: type = "natural"
      ad position: type = "ad"
      new product position: type = "new"
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

                var imgEl = item.querySelector('img.s-image');
                var mainImage = imgEl ? (imgEl.src || '') : '';

                if (asin) {
                    results.push({ asin: asin, type: markType || 'unknown', rank: rankText, title: title, price: price, rating: rating, reviews: reviews, main_image: mainImage });
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
    Pick up to 5 ASINs from all marked results:
      Priority: natural_top1-3 > ad_top1 > new_natural_top1 > unknown_top1
    Deduplicated. Stop when 5 collected.
    Falls back to 'unknown' type if natural/ad/new don't fill all 5 slots.
    """
    natural = [m for m in marks if m.get("type") == "natural"]
    ad = [m for m in marks if m.get("type") == "ad"]
    new_list = [m for m in marks if m.get("type") == "new"]
    unknown = [m for m in marks if m.get("type") == "unknown"]

    def rank_num(m):
        t = m.get("rank", "")
        if not t:
            return 999
        nums = re.findall(r"\d+", t)
        return int(nums[-1]) if nums else 999

    natural.sort(key=rank_num)
    ad.sort(key=rank_num)
    new_list.sort(key=rank_num)
    unknown.sort(key=rank_num)

    selected = []
    seen = set()

    for pool, label in [
        (natural[:3], "natural_top"),
        (ad[:1], "ad_top"),
        (new_list[:1], "new_natural_top"),
        (unknown[:1], "unknown_top"),
    ]:
        for m in pool:
            if m.get("asin") not in seen:
                m["_label"] = label
                selected.append(m)
                seen.add(m.get("asin"))
                if len(selected) >= 5:
                    break
        if len(selected) >= 5:
            break

    return selected[:5]


def group_and_pick_top3(marks):
    """
    Pick up to 3 ASINs from all marked results:
      Priority: natural_top1 > ad_top1 > new_natural_top1
    Deduplicated. Stop when 3 collected.
    """
    natural = [m for m in marks if m.get("type") == "natural"]
    ad = [m for m in marks if m.get("type") == "ad"]
    new_list = [m for m in marks if m.get("type") == "new"]

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

    for pool, label in [(natural[:1], "natural_top1"), (ad[:1], "ad_top1"), (new_list[:1], "new_natural_top1")]:
        for m in pool:
            if m.get("asin") not in seen:
                m["_label"] = label
                selected.append(m)
                seen.add(m.get("asin"))
                break
        if len(selected) >= 3:
            break

    return selected[:3]

def _kw_rel_path(keyword):
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    safe = keyword.replace(" ", "_").replace("/", "_")
    return os.path.join(data_dir, "keyword_related_asins.json")


def load_kw_related_asins(keyword):
    """Load cached keyword related ASINs (keep-old, never auto-reset)"""
    path = _kw_rel_path(keyword)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            all_data = json.load(f)
        return all_data.get(keyword, [])
    except:
        return []


def save_kw_related_asins(keyword, asins):
    """Save keyword related ASINs (only on first run, keep-old on subsequent)"""
    path = _kw_rel_path(keyword)
    all_data = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        except:
            pass
    all_data[keyword] = asins
    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)


# --- Main Search Flow ---

def do_keyword_search(browser, keyword):
    """Search keyword with human behavior simulation"""
    sep = "=" * 60
    print("\n" + sep)
    print("Keyword market: " + keyword)
    print(sep)

    # 1. Save main tab WS, create independent new tab
    print("  Opening new tab...")
    main_ws = browser.ws
    main_tab = browser.tab

    result = browser.cmd("Target.createTarget", {"url": "about:blank"})
    new_tab_id = result.get("targetId")
    time.sleep(1.5)
    browser._refresh_tabs()

    # Connect new tab WS directly (bypass connect_tab which always uses index=0)
    new_tab = None
    for t in browser._raw_tabs:
        if t.get("id") == new_tab_id:
            new_tab = t
            break
    if not new_tab:
        raise RuntimeError("Cannot create new tab")

    ws_url = new_tab.get("webSocketDebuggerUrl")
    if browser.ws:
        try:
            browser.ws.close()
        except:
            pass
    browser.ws = websocket.create_connection(ws_url, timeout=15)
    browser.tab = new_tab
    print("  New tab WS connected")

    # 2. Navigate to search page
    search_url = "https://www.amazon.com/s?k=" + keyword.replace(" ", "+") + "&ref=nb_sb_noss"
    print("  Navigating to: " + search_url)
    browser.navigate(search_url, wait_min=2, wait_max=4)

    # 3. Wait for plugin markers (up to 15s)
    print("  Waiting for Seller Sprite plugin markers...")
    plugin_found = wait_for_plugin_markers(browser, timeout=30)

    # 3.5 Wait extra 10s for page to fully stabilize after plugin markers appear
    print("  等待10秒页面稳定...")
    time.sleep(10)

    # 4. Human behavior simulation
    random_scroll(browser, times=random.randint(1, 2))
    human_pause(2, 5)
    random_hovers(browser, count=random.randint(1, 2))

    # 5. Extract data
    print("  Extracting search result data...")
    marks = extract_asin_marks_from_page(browser)
    print("  Found " + str(len(marks)) + " product results (plugin=" + str(plugin_found) + ")")
    for m in marks[:5]:
        t = m.get("type", "")
        a = m.get("asin", "")
        title = str(m.get("title", "")[:40])
        print("     [" + t.ljust(15) + "] " + a + " | " + title)

    top_asins = group_and_pick_top5(marks)
    print("  Top3 ASINs:")
    for a in top_asins:
        print("     [" + str(a.get("type", "")).ljust(20) + "] " + a.get("asin", "") + " | " + a.get("price", ""))

    # 6. Close new tab, restore main tab
    try:
        browser.cmd("Target.closeTarget", {"targetId": new_tab_id})
    except:
        pass
    browser._refresh_tabs()

    # Restore main tab WS
    if main_ws:
        try:
            main_ws.close()
        except:
            pass
    if main_tab:
        ws_url = main_tab.get("webSocketDebuggerUrl")
        if ws_url:
            browser.ws = websocket.create_connection(ws_url, timeout=15)
            browser.tab = main_tab

    return marks, top_asins


# --- Entry Point ---

def check_keyword(keyword):
    """Keyword monitoring main function"""
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

    # ── 数据有效性检查：无效时不写入快照 ──
    if not marks and not top_asins:
        print("  ⚠️ 关键词搜索无结果，跳过快照保存")
        return

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
                "main_image": a.get("main_image", ""),
            }
            for a in top_asins
        ],
        "raw_marks": [
            {"asin": a.get("asin", ""), "type": a.get("type", ""), "rank": a.get("rank", "")}
            for a in marks[:50]
        ]
    }

    # Save snapshot
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

    # Keyword related ASINs: save on first run (keep-old)
    existing = load_kw_related_asins(keyword)
    if not existing:
        asins_to_save = [{"asin": a.get("asin", ""), "name": a.get("title", "")[:60]} for a in top_asins]
        save_kw_related_asins(keyword, asins_to_save)
        print("  [kw_rel] First run, saved " + str(len(asins_to_save)) + " related ASINs")
    else:
        print("  [kw_rel] Already cached " + str(len(existing)) + " related ASINs (keep-old)")

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
