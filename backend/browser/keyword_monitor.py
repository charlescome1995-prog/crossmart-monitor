#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词市场监控 - 重写版
行为规则 - 所有跳转用 click()，不在地址栏输 URL
"""

import time
import random
import sys
import os
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser.human_timer import human_pause, read_pause, think_pause

# ─── 工具函数 ──────────────────────────────────────────────────────────────

def random_scroll(browser, times=None, min_pause=1.0, max_pause=2.0):
    """随机滚动 + 停顿"""
    t = times if times is not None else random.randint(1, 3)
    for _ in range(t):
        amt = random.randint(300, 700)
        browser.eval("window.scrollBy(0, " + str(amt) + ")")
        time.sleep(random.uniform(min_pause, max_pause))


def random_hovers(browser, count=None):
    """随机悬停到一些商品上（模拟人类阅读）"""
    n = count if count is not None else random.randint(1, 3)
    js = """
    (() => {
        const els = document.querySelectorAll('.s-result-item[data-component-type="s-search-result"]');
        const picks = Array.from(els).sort(() => Math.random() - 0.5).slice(0, """ + str(n) + """);
        picks.forEach((el, i) => {
            setTimeout(() => el.dispatchEvent(new MouseEvent('mouseenter', {bubbles:true}})), i * 800);
        });
    })()
    """
    browser.eval(js)


def browse_random_asins(browser, count=2):
    """随机逛一些 ASIN 页面（不记录数据，只模拟人类行为）"""
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
    """等待搜索结果完全渲染"""
    time.sleep(random.uniform(min_sec, max_sec))
    for _ in range(3):
        browser.eval("( () => { if (document.querySelector('.s-result-item')) window.__rendered = true; } )()")
        time.sleep(1)


# ─── 数据提取 ─────────────────────────────────────────────────────────────

def extract_asin_marks_from_page(browser):
    """
    从亚马逊搜索结果页提取所有商品标记。
    优先级：
      1. 插件气泡文字 "自然第N" / "广告第N" / "新品第N"（最可靠）
      2. 插件 data-* 属性（辅助）
      3. DOM Sponsored 标识（最后兜底）
    """
    js = r"""
    (() => {
        const results = [];
        const items = document.querySelectorAll('.s-result-item[data-component-type="s-search-result"]);

        items.forEach((item, idx) => {
            // 1. 优先：从插件气泡读取自然/广告/新品标记
            const bubbles = item.querySelectorAll('[class*="browse-madge-text"],
                                                  [class*="madge-text"],
                                                  [class*="natural"],
                                                  [class*="advertisement"]);
            let markType = '';
            let rankText = '';
            let asin = '';

            // 读插件气泡文字
            const allText = item.innerText || '';
            if (/\u81ea\u7136\u7b2c(\d+)/.test(allText) || /\u81ea\u7136\u7b2c(\d+)\u540d/.test(allText)) {
                markType = 'natural';
                const m = allText.match(/\u81ea\u7136\u7b2c(\d+)/);
                rankText = m ? '\u81ea\u7136\u7b2c' + m[1] : '\u81ea\u7136';
            } else if (/\u5e7f\u544a\u7b2c(\d+)/.test(allText) || /\u5e7f\u544a\u7b2c(\d+)\u540d/.test(allText)) {
                markType = 'ad';
                const m = allText.match(/\u5e7f\u544a\u7b2c(\d+)/);
                rankText = m ? '\u5e7f\u544a\u7b2c' + m[1] : '\u5e7f\u544a';
            } else if (/\u65b0\u54c1\u7b2c(\d+)/.test(allText)) {
                markType = 'new';
                const m = allText.match(/\u65b0\u54c1\u7b2c(\d+)/);
                rankText = m ? '\u65b0\u54c1\u7b2c' + m[1] : '\u65b0\u54c1';
            }

            // 2. 兜底：DOM Sponsored
            if (!markType) {
                const spon = item.closest('[class*="sponsorship"], [class*="sponsored"], [data-component-type*="sponsored"]');
                if (spon) { markType = 'ad'; rankText = 'ad'; }
            }

            // ASIN
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
    从所有标记结果中选出最有代表性的 Top5 ASIN：
      优先级：natural_top1 > ad_top1 > new_natural_top1 > new_ad_top1 > natural_other
    同类型内按 rank 数字排序。
    """
    natural = [m for m in marks if m.get("type") == "natural"]
    ad = [m for m in marks if m.get("type") == "ad"]
    new = [m for m in marks if m.get("type") == "new"]
    other = [m for m in marks if m.get("type") not in ("natural", "ad", "new")]

    def rank_num(m):
        t = m.get("rank", "")
        if not t:
            return 999
        m2 = re.search(r"\d+", t)
        return int(m2.group()) if m2 else 999

    natural.sort(key=rank_num)
    ad.sort(key=rank_num)
    new.sort(key=rank_num)

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
    pick(new[:1], "new_natural_top1")
    pick(ad[1:2], "new_ad_top1")
    pick(natural[1:2], "natural_other")

    # 最后补满 5 个（尽量不重复）
    all_pool = natural + ad + new + other
    for m in all_pool:
        if m.get("asin") not in seen and len(selected) < 5:
            m["_label"] = "natural_other"
            selected.append(m)
            seen.add(m.get("asin"))

    return selected[:5]


# ─── 主搜索流程 ───────────────────────────────────────────────────────────

def do_keyword_search(browser, keyword):
    """在亚马逊上搜索关键词，模拟人类行为"""
    sep = "=" * 60
    print("\n" + sep)
    print("🔍 关键词市场: " + keyword)
    print(sep)

    # ── 1. 打开亚马逊（强制新空白标签页） ─────────────────────
    print("\n  🌐 打开亚马逊...")
    browser.cmd("Target.createTarget", {"url": "about:blank"})
    time.sleep(1.5)
    browser.connect_tab(tab_url_filter="about:blank")
    if not browser.tab:
        browser.cmd("Target.createTarget", {"url": "about:blank"})
        time.sleep(1.5)
        browser.connect_tab(tab_url_filter="about:blank")

    browser.navigate("https://www.amazon.com/", wait_min=2, wait_max=4)
    wait_s = random.uniform(5, 8)
    print("  ⏳ 等待 " + str(int(wait_s)) + "s（检查网络和账号登录）...")
    time.sleep(wait_s)

    # ── 2. 搜索关键词 ────────────────────────────────────────
    print("  🔍 在搜索框输入: " + keyword)
    time.sleep(random.uniform(1, 2))
    browser.click_element("#twotabsearchtextbox")
    human_pause(1, 3)

    # 清空输入框
    browser.eval(
        "(() => { const inp = document.querySelector('#twotabsearchtextbox');"
        "if (inp) { inp.value = ''; inp.dispatchEvent(new Event('input', {bubbles:true}})); }})()"
    )
    human_pause(0.5, 1.5)

    # 逐字输入
    for ch in keyword:
        js_input = (
            "(() => {"
            "const inp = document.querySelector('#twotabsearchtextbox');"
            "if (inp) {"
            "inp.focus();"
            "const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
            "setter.call(inp, inp.value + " + repr(ch) + ");"
            "inp.dispatchEvent(new Event('input', {bubbles:true}}));"
            "}})()"
        )
        browser.eval(js_input)
        time.sleep(random.uniform(0.08, 0.25))
        human_pause(0.05, 0.2)

    human_pause(0.5, 1.5)
    browser.click_element("#nav-search-submit-text, #nav-search-submit-button, input[type='submit'][aria-label]")
    print("  ⏳ 等待搜索结果渲染（给卖家精灵插件留时间）...")
    wait_for_render(browser, min_sec=4, max_sec=8)

    # ── 3. 随机滚动 ───────────────────────────────────────────
    random_scroll(browser, times=random.randint(1, 2))
    human_pause(2, 5)

    # ── 4. 随机悬停 ───────────────────────────────────────────
    random_hovers(browser, count=random.randint(1, 3))

    # ── 5. 随机浏览其他 ASIN ──────────────────────────────────
    print("  🚶 随机浏览其他商品（不记录）...")
    browse_random_asins(browser, count=random.randint(1, 2))
    human_pause(2, 5)

    # ── 6. 回到搜索结果页 ─────────────────────────────────────
    browser._refresh_tabs()
    for t in browser._raw_tabs:
        if "amazon.com/s" in t.get("url", ""):
            browser.connect_tab(tab_index=browser._raw_tabs.index(t))
            break

    random_scroll(browser, times=2)
    wait_for_render(browser, min_sec=2, max_sec=4)
    human_pause(2, 5)

    # ── 7. 提取数据 ─────────────────────────────────────────────
    print("  📊 提取搜索结果数据...")
    marks = extract_asin_marks_from_page(browser)
    print("  ℹ️ 共找到 " + str(len(marks)) + " 个商品结果")
    for m in marks[:5]:
        print("     [" + str(m.get("type", "")).ljust(15) + "] " + m.get("asin", "") + " | " + str(m.get("title", "")[:40]))

    top_asins = group_and_pick_top5(marks)
    print("  🎯 Top5 ASIN:")
    for a in top_asins:
        print("     [" + str(a.get("type", "")).ljust(20) + "] " + a.get("asin", "") + " | " + a.get("price", ""))

    return marks, top_asins


# ─── 主入口 ────────────────────────────────────────────────────────────────

def check_keyword(keyword):
    """关键词监控主函数"""
    from browser.amazon_browser import CDPBrowser

    browser = CDPBrowser()

    marks = []
    top_asins = []

    try:
        marks, top_asins = do_keyword_search(browser, keyword)
    except Exception as e:
        print("  ⚠️ 亚马逊搜索失败: " + str(e))
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
    _data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    _snap_dir = os.path.join(_data_dir, "processed", "kw_" + keyword.replace(" ", "_").replace("/", "_"))
    os.makedirs(_snap_dir, exist_ok=True)
    _ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    _snap_file = os.path.join(_snap_dir, "snapshot_" + _ts + ".json")
    import json
    with open(_snap_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    # 写 latest.json
    latest_file = os.path.join(_snap_dir, "latest.json")
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    browser.close()

    print("\n" + sep)
    print("✅ 关键词 [" + keyword + "] 检查完成，找到 " + str(len(top_asins)) + " 个目标 ASIN")
    print(sep)

    return snapshot


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="关键词市场监控")
    parser.add_argument("keyword", nargs="?", help="关键词")
    args = parser.parse_args()

    if not args.keyword:
        print("用法: python keyword_monitor.py 'batana oil'")
        sys.exit(1)

    check_keyword(args.keyword)