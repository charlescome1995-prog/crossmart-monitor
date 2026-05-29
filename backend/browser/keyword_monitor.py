#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keyword market monitoring - rewritten
Behavior rules - all navigation via direct URL for search pages
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

# ─── Utility functions ──────────────────────────────────────────────────────────

def random_scroll(browser, times=None, min_pause=1.0, max_pause=2.0):
    """Random scroll + pause"""
    t = times if times is not None else random.randint(1, 3)
    for _ in range(t):
        amt = random.randint(300, 700)
        browser.eval("window.scrollBy(0, " + str(amt) + ")")
        time.sleep(random.uniform(min_pause, max_pause))


def random_hovers(browser, count=None):
    """Random hover over some products (simulate human reading)"""
    n = count if count is not None else random.randint(1, 3)
    js = (
        "(() => {"
        "const els = document.querySelectorAll('.s-result-item[data-component-type=\"s-search-result\"]');"
        "const picks = Array.from(els).sort(() => Math.random() - 0.5).slice(0, " + str(n) + ");"
        "picks.forEach((el, i) => {"
        "setTimeout(() => el.dispatchEvent(new MouseEvent('mouseenter', {bubbles:true}})), i * 800);"
        "});"
        "})()"
    )
    browser.eval(js)


def browse_random_asins(browser, count=2):
    """Randomly browse some ASIN pages (no data recording, just human behavior simulation)"""
    js = (
        "(() => {"
        "const links = document.querySelectorAll('a.a-link-normal[href*=\"/dp/\"]');"
        "const candidates = Array.from(links)"
        ".map(a => { try { return {href: a.href, asin: (a.href.match(/\\/dp\\/([A-Z0-9]+)/)||[])[1]}; } catch(e) { return null; }})"
        ".filter(x => x && x.asin)"
        ".sort(() => Math.random() - 0.5)"
        ".slice(0, " + str(count) + ");"
        "if (candidates.length === 0) return;"
        "candidates.forEach((item, i) => {"
        "setTimeout(() => { window.open(item.href, '_blank'); }, i * 3500);"
        "});"
        "})()"
    )
    browser.eval(js)
    time.sleep(count * 4 + 2)
    browser._refresh_tabs()
    tabs = browser._raw_tabs
    if len(tabs) > 1:
        last_tab = tabs[-1]
        try:
            browser.cmd("Target.closeTarget", {"targetId": last_tab.get("id")})
        except:
            pass
        time.sleep(1)


def wait_for_render(browser, min_sec=4, max_sec=8):
    """Wait for search results to fully render"""
    time.sleep(random.uniform(min_sec, max_sec))
    for _ in range(3):
        browser.eval("( () => { if (document.querySelector('.s-result-item')) window.__rendered = true; } )()")
        time.sleep(1)


# ─── Data extraction ──────────────────────────────────────────────────────────

def extract_asin_marks_from_page(browser):
    """
    Extract all product marks from Amazon search results page.
    Priority:
      1. Plugin bubble text "Natural #N" / "Ad #N" / "New #N" (most reliable)
      2. Plugin data-* attributes (auxiliary)
      3. DOM Sponsored marker (last resort)
    """
    js = r"""
    (() => {
        const results = [];
        const items = document.querySelectorAll('.s-result-item[data-component-type="s-search-result"]');

        items.forEach((item, idx) => {
            let markType = '';
            let rankText = '';
            let asin = '';

            const inner = item.innerText || '';

            // 1. Plugin bubble text (Chinese characters)
            if (/\u81ea\u7136\u7b2c(\d+)/.test(inner) || /\u81ea\u7136\u7b2c(\d+)\u540d/.test(inner)) {
                markType = 'natural';
                const m = inner.match(/\u81ea\u7136\u7b2c(\d+)/);
                rankText = m ? '\u81ea\u7136\u7b2c' + m[1] : '\u81ea\u7136';
            } else if (/\u5e7f\u544a\u7b2c(\d+)/.test(inner) || /\u5e7f\u544a\u7b2c(\d+)\u540d/.test(inner)) {
                markType = 'ad';
                const m = inner.match(/\u5e7f\u544a\u7b2c(\d+)/);
                rankText = m ? '\u5e7f\u544a\u7b2c' + m[1] : '\u5e7f\u544a';
            } else if (/\u65b0\u54c1\u7b2c(\d+)/.test(inner)) {
                markType = 'new';
                const m = inner.match(/\u65b0\u54c1\u7b2c(\d+)/);
                rankText = m ? '\u65b0\u54c1\u7b2c' + m[1] : '\u65b0\u54c1';
            }

            // 2. Fallback: DOM Sponsored
            if (!markType) {
                const spon = item.closest('[class*="sponsorship"], [class*="sponsored"], [data-component-type*="sponsored"]');
                if (spon) { markType = 'ad'; rankText = 'ad'; }
            }

            // ASIN from link
            const link = item.querySelector('a.a-link-normal[href*="/dp/"]');
            if (link) {
                const match = link.href.match(/\/dp\/([A-Z0-9]{10})/);
                if (match) asin = match[1];
            }

            // Title
            let title = '';
            const titleEl = item.querySelector('h2.a-size-base-plus, h2.a-size-medium, h2');
            if (titleEl) title = titleEl.innerText || '';

            // Price
            let price = '';
            const priceEl = item.querySelector('.a-price .a-offscreen, .a-price-whole');
            if (priceEl) price = priceEl.innerText || '';

            // Rating
            let rating = '';
            const ratingEl = item.querySelector('.a-icon-star-small, .a-icon-star');
            if (ratingEl) rating = ratingEl.innerText || '';

            // Reviews
            let reviews = '';
            const revEl = item.querySelector('[aria-label*="star"], .a-size-base');
            if (revEl) {
                const m = revEl.innerText.match(/([\d,]+)/);
                if (m) reviews = m[1];
            }

            if (asin) {
                results.push({ asin, type: markType || 'unknown', rank: rankText, title, price, rating, reviews });
            }
        });
        return results;
    })()
    """
    try:
        raw = browser.eval(js)
        marks = raw if isinstance(raw, list) else []
        return marks
    except Exception as e:
        print("  [extract_asin_marks] JS error: " + str(e))
        return []


def group_and_pick_top5(marks):
    """
    Select the most representative Top5 ASINs from all marked results:
      Priority: natural_top1 > ad_top1 > new_natural_top1 > new_ad_top1 > natural_other
    Within same type, sort by rank number.
    """
    natural = [m for m in marks if m.get("type") == "natural"]
    ad = [m for m in marks if m.get("type") == "ad"]
    new_list = [m for m in marks if m.get("type") == "new"]
    other = [m for m in marks if m.get("type") not in ("natural", "ad", "new")]

    def rank_num(m):
        t = m.get("rank", "")
        if not t:
            return 999
        m2 = re.search(r"\d+", t)
        return int(m2.group()) if m2 else 999

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

    # Fill remaining slots (avoid duplicates)
    all_pool = natural + ad + new_list + other
    for m in all_pool:
        if m.get("asin") not in seen and len(selected) < 5:
            m["_label"] = "fill"
            selected.append(m)
            seen.add(m.get("asin"))

    return selected[:5]


# ─── Main search flow ─────────────────────────────────────────────────────────

def do_keyword_search(browser, keyword):
    """Search keyword on Amazon, simulate human behavior"""
    sep = "=" * 60
    print("\n" + sep)
    print("Keyword market: " + keyword)
    print(sep)

    # ── 1. Open Amazon (force new blank tab) ─────────────────────
    print("\n  Opening Amazon...")
    browser.cmd("Target.createTarget", {"url": "about:blank"})
    time.sleep(1.5)
    browser.connect_tab(tab_url_filter="about:blank")
    if not browser.tab:
        browser.cmd("Target.createTarget", {"url": "about:blank"})
        time.sleep(1.5)
        browser.connect_tab(tab_url_filter="about:blank")

    # ── 2. Navigate directly to search page (most reliable) ────────
    search_url = "https://www.amazon.com/s?k=" + keyword.replace(" ", "+") + "&ref=nb_sb_noss"
    print("  Search URL: " + search_url)
    browser.navigate(search_url, wait_min=2, wait_max=4)
    wait_s = random.uniform(6, 10)
    print("  Waiting " + str(int(wait_s)) + "s for Seller Sprite plugin to render...")
    time.sleep(wait_s)

    # ── 3. Random scroll ──────────────────────────────────────────
    random_scroll(browser, times=random.randint(1, 2))
    human_pause(2, 5)

    # ── 4. Random hover ───────────────────────────────────────────
    random_hovers(browser, count=random.randint(1, 3))

    # ── 5. Randomly browse other ASINs ───────────────────────────
    print("  Browsing other products (no record)...")
    browse_random_asins(browser, count=random.randint(1, 2))
    human_pause(2, 5)

    # ── 6. Back to search results ──────────────────────────────────
    browser._refresh_tabs()
    for t in browser._raw_tabs:
        if "amazon.com/s" in t.get("url", ""):
            browser.connect_tab(tab_index=browser._raw_tabs.index(t))
            break

    random_scroll(browser, times=2)
    wait_for_render(browser, min_sec=2, max_sec=4)
    human_pause(2, 5)

    # ── 7. Extract data ────────────────────────────────────────────
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


# ─── Entry point ──────────────────────────────────────────────────────────────

def check_keyword(keyword):
    """Keyword monitoring main function"""
    from browser.amazon_browser import CDPBrowser

    browser = CDPBrowser()

    marks = []
    top_asins = []

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