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
      Priority: natural_top1-3 > ad_top1 > new_natural_top1 > unknown (fill remaining)
    Deduplicated. Stop when 5 collected.
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

    # Fill remaining slots from unknown
    if len(selected) < 5:
        for m in unknown:
            if m.get("asin") not in seen:
                m["_label"] = "unknown_top"
                selected.append(m)
                seen.add(m.get("asin"))
                if len(selected) >= 5:
                    break

    return selected[:5]


# --- Seller Sprite vxe-table 提取 (P0) ---

SPRITE_KEYWORD_RESEARCH_URL = "https://www.sellersprite.com/v2/keyword-research"
SPRITE_VXE_ROWS_PER_SCROLL = 16  # vxe-table 每次滚动大约加载 16 行
SPRITE_VXE_MAX_SCROLL_ROUNDS = 5  # 最多滚 5 次 (16*5=80 行，覆盖 64 行)
SPRITE_VXE_LOAD_TIMEOUT = 90      # 服务端查询 1-2 分钟


def open_sprite_tab(browser):
    """
    在新 tab 里打开卖家精灵，独立 WS 连接，不污染当前 Amazon tab。
    返回 (new_ws, new_tab, target_id)；失败返回 (None, None, None)。
    调用方负责关闭。
    """
    saved_ws = browser.ws
    saved_tab = browser.tab

    result = browser.cmd("Target.createTarget", {"url": "about:blank"})
    target_id = result.get("targetId")
    if not target_id:
        return None, None, None
    time.sleep(1.2)
    browser._refresh_tabs()

    new_tab = None
    for t in browser._raw_tabs:
        if t.get("id") == target_id:
            new_tab = t
            break
    if not new_tab:
        return None, None, None

    ws_url = new_tab.get("webSocketDebuggerUrl")
    if browser.ws:
        try:
            browser.ws.close()
        except:
            pass
    browser.ws = websocket.create_connection(ws_url, timeout=15)
    browser.tab = new_tab
    return saved_ws, saved_tab, target_id


def close_sprite_tab(browser, saved_ws, saved_tab, target_id):
    """关闭卖家精灵 tab 并恢复主 tab WS"""
    try:
        browser.cmd("Target.closeTarget", {"targetId": target_id})
    except:
        pass
    browser._refresh_tabs()
    if saved_ws:
        try:
            saved_ws.close()
        except:
            pass
    if saved_tab:
        ws_url = saved_tab.get("webSocketDebuggerUrl")
        if ws_url:
            try:
                browser.ws = websocket.create_connection(ws_url, timeout=15)
                browser.tab = saved_tab
            except:
                pass


def scroll_vxe_table(browser, scroll_rounds=None):
    """
    触发 vxe-table 虚拟滚动，分批加载行。
    返回当前可见的行数。
    """
    if scroll_rounds is None:
        scroll_rounds = SPRITE_VXE_MAX_SCROLL_ROUNDS

    js = """
    (function(rounds) {
        // vxe-table body-wrapper: .vxe-table--body-wrapper
        var wrapper = document.querySelector(
            '#main-sellersprite-extension .vxe-table--body-wrapper, ' +
            '.seller-sprite-extension-app .vxe-table--body-wrapper, ' +
            '.vxe-table--body-wrapper'
        );
        if (!wrapper) return -1;
        var step = wrapper.clientHeight || 400;
        for (var i = 0; i < rounds; i++) {
            wrapper.scrollTop = (i + 1) * step;
            wrapper.dispatchEvent(new Event('scroll', {bubbles: true}));
        }
        // 统计当前可见 + 缓冲区的 row 数
        var rows = wrapper.querySelectorAll('tr.body--wrapper, tr.vxe-body--row');
        return rows.length;
    })(arguments[0])
    """
    try:
        return browser.eval(js.replace("arguments[0]", str(scroll_rounds)))
    except Exception as e:
        print("  [vxe-scroll] " + str(e))
        return -1


def extract_vxe_rows(browser):
    """
    从卖家精灵 vxe-table 提取当前可见的所有行。
    根据 audit: col_4=rank, col_6=title, col_7=brand, col_22=launch_date
    返回 [{rank:int, title:str, brand:str, asin:str|None, launch_date:str|None}]
    """
    js = r"""
    (function() {
        var rows = document.querySelectorAll(
            '#main-sellersprite-extension .vxe-table--body-wrapper tr, ' +
            '.seller-sprite-extension-app .vxe-table--body-wrapper tr, ' +
            '.vxe-table--body-wrapper tr'
        );
        var out = [];
        var seen = new Set();
        for (var i = 0; i < rows.length; i++) {
            var row = rows[i];
            // 排除表头
            if (row.parentElement && row.parentElement.tagName === 'THEAD') continue;
            if (row.classList.contains('vxe-header--row')) continue;

            var cells = row.querySelectorAll('td, .vxe-body--column');
            if (cells.length < 8) continue;

            // col_4 = rank 数字（也可能是其它 cell，根据 audit）
            var rankCell = cells[3] || cells[0];
            var rankText = (rankCell.innerText || '').trim();
            var rank = parseInt(rankText.replace(/[^\d]/g, ''), 10);

            // col_6 = title, col_7 = brand
            var title = (cells[5] && cells[5].innerText || '').trim().slice(0, 200);
            var brand = (cells[6] && cells[6].innerText || '').trim().slice(0, 80);

            // col_22 = launch_date (索引 21)
            var launch = '';
            if (cells[21]) {
                launch = (cells[21].innerText || '').trim().slice(0, 20);
            }

            // 尝试从 title 单元格里的链接抓 ASIN
            var asin = '';
            var linkEl = (cells[5] || row).querySelector('a[href*="/dp/"]');
            if (linkEl) {
                var m = linkEl.href.match(/\/dp\/([A-Z0-9]{10})/);
                if (m) asin = m[1];
            }
            // 备用：从单元格文本里匹配 B0 开头的 ASIN
            if (!asin) {
                var allText = row.innerText || '';
                var ma = allText.match(/B[A-Z0-9]{9}/);
                if (ma) asin = ma[0];
            }

            if (!rank || isNaN(rank)) continue;
            if (!title) continue;

            // 去重：同一 rank + title 只保留一次
            var key = rank + '|' + title.slice(0, 30);
            if (seen.has(key)) continue;
            seen.add(key);

            out.push({
                rank: rank,
                title: title,
                brand: brand,
                asin: asin,
                launch_date: launch
            });
        }
        return out;
    })()
    """
    try:
        raw = browser.eval(js)
        return raw if isinstance(raw, list) else []
    except Exception as e:
        print("  [vxe-extract] " + str(e))
        return []


def match_vxe_to_amazon_organic(vxe_rows, organic_marks):
    """
    用标题相似度把卖家精灵 vxe 行匹配到 Amazon organic 列表。
    返回 {asin: sprite_rank} 字典 + {asin: title_match_score}。
    """
    if not vxe_rows or not organic_marks:
        return {}, {}

    def norm(t):
        return re.sub(r'\s+', ' ', (t or '').lower().strip())[:60]

    # 构造 Amazon organic 标题索引 (按出现顺序 1-based)
    amazon_by_title = {}
    for i, m in enumerate(organic_marks):
        title = norm(m.get('title', ''))
        if title and title not in amazon_by_title:
            amazon_by_title[title] = {'asin': m.get('asin', ''), 'position': i + 1}

    sprite_rank_by_asin = {}
    sprite_title_by_asin = {}
    matched_amazon_titles = set()

    for row in vxe_rows:
        rt = norm(row.get('title', ''))
        if not rt:
            continue
        # 精确匹配
        if rt in amazon_by_title and amazon_by_title[rt]['asin']:
            asin = amazon_by_title[rt]['asin']
            if asin not in sprite_rank_by_asin:  # 取最低 rank
                sprite_rank_by_asin[asin] = row['rank']
                sprite_title_by_asin[asin] = row['title']
            matched_amazon_titles.add(rt)
            continue
        # 模糊匹配: 前 30 字符相同
        prefix = rt[:30]
        for amz_title, info in amazon_by_title.items():
            if amz_title in matched_amazon_titles:
                continue
            if amz_title.startswith(prefix) or prefix.startswith(amz_title[:30]):
                asin = info['asin']
                if asin and asin not in sprite_rank_by_asin:
                    sprite_rank_by_asin[asin] = row['rank']
                    sprite_title_by_asin[asin] = row['title']
                matched_amazon_titles.add(amz_title)
                break

    return sprite_rank_by_asin, sprite_title_by_asin


def extract_sprite_table_rank(browser, keyword, organic_marks=None, max_rows=64, timeout=SPRITE_VXE_LOAD_TIMEOUT):
    """
    [P0] 卖家精灵 vxe-table 提取器 (叠加模式)

    流程:
      1) 在新 tab 里打开 sellersprite /v2/keyword-research
      2) 搜索 keyword → 切到"产品查询" tab
      3) 等 vxe-table 加载 (最多 timeout 秒)
      4) 滚动虚拟列表直到收集到 >= max_rows 个不同 rank
      5) 返回 [{rank,title,brand,asin,launch_date}]
      6) 关闭 tab，不影响 Amazon 流程

    失败优雅降级：返回 []，调用方继续走主流程。
    """
    print("\n  [P0] 卖家精灵 vxe-table 提取开始...")
    saved_ws, saved_tab, target_id = open_sprite_tab(browser)
    if not target_id:
        print("  [P0] 创建卖家精灵 tab 失败，跳过")
        return []

    try:
        # 1) 导航到 keyword research
        url = SPRITE_KEYWORD_RESEARCH_URL + "?keyword=" + urllib_quote(keyword)
        browser.navigate(url, wait_min=3, wait_max=6)
        time.sleep(3)

        # 2) 激活"产品查询" tab (audit: 默认就是，但要确保 vxe-table 出现)
        activated = browser.eval("""
            (function() {
                var tabs = document.querySelectorAll('#main-sellersprite-extension [class*="tab"], .seller-sprite-extension-app [role="tab"], .el-tabs__item');
                for (var i = 0; i < tabs.length; i++) {
                    var t = (tabs[i].innerText || '').trim();
                    if (t.indexOf('产品查询') >= 0 || t.indexOf('Product Search') >= 0) {
                        tabs[i].click();
                        return true;
                    }
                }
                return false;
            })()
        """)
        print("  [P0] 激活产品查询 tab: " + str(activated))
        time.sleep(2)

        # 3) 等 vxe-table 出现 + 服务端查询完成
        start = time.time()
        rows_collected = []
        last_count = 0
        stall_rounds = 0
        while time.time() - start < timeout:
            js_check = """
                (function() {
                    var w = document.querySelector(
                        '#main-sellersprite-extension .vxe-table--body-wrapper, ' +
                        '.vxe-table--body-wrapper'
                    );
                    if (!w) return {ready: false, rows: 0};
                    var rows = w.querySelectorAll('tr.body--wrapper, tr.vxe-body--row');
                    return {ready: true, rows: rows.length};
                })()
            """
            try:
                state = browser.eval(js_check) or {}
            except:
                state = {}
            ready = state.get('ready', False)
            row_count = state.get('rows', 0)

            # 滚动加载更多
            if ready and row_count > 0:
                scroll_vxe_table(browser, scroll_rounds=2)
                time.sleep(1.5)
                # 提取当前可见
                new_rows = extract_vxe_rows(browser)
                # 合并去重
                seen_keys = {(r['rank'], r['title'][:30]) for r in rows_collected}
                added = 0
                for r in new_rows:
                    key = (r['rank'], r['title'][:30])
                    if key not in seen_keys:
                        rows_collected.append(r)
                        seen_keys.add(key)
                        added += 1

                if len(rows_collected) >= max_rows:
                    print("  [P0] 已收集 " + str(len(rows_collected)) + " 行 (>= " + str(max_rows) + ")，停止")
                    break
                if added == 0:
                    stall_rounds += 1
                else:
                    stall_rounds = 0
                    last_count = len(rows_collected)

                # 连续 3 轮没新数据 → 认为已到底
                if stall_rounds >= 3:
                    print("  [P0] 已稳定在 " + str(len(rows_collected)) + " 行")
                    break
            else:
                # 表格还没出现，等更久
                time.sleep(3)

            time.sleep(2)

        print("  [P0] 卖家精灵 vxe-table 提取完成: " + str(len(rows_collected)) + " 行")

        # 4) 可选: 与 Amazon organic 匹配
        if organic_marks and rows_collected:
            ranks, titles = match_vxe_to_amazon_organic(rows_collected, organic_marks)
            print("  [P0] 与 Amazon organic 匹配: " + str(len(ranks)) + " 个 ASIN 找到卖家精灵 rank")
            for asin, rank in list(ranks.items())[:5]:
                t = titles.get(asin, '')[:40]
                print("       " + asin + " → sprite_rank=" + str(rank) + " | " + t)
            # 给每行附加 amazon_position 字段 (如有匹配)
            by_title = {}
            for i, m in enumerate(organic_marks):
                t = re.sub(r'\s+', ' ', (m.get('title', '') or '').lower().strip())[:60]
                if t and t not in by_title:
                    by_title[t] = i + 1
            for r in rows_collected:
                rt = re.sub(r'\s+', ' ', (r.get('title', '') or '').lower().strip())[:60]
                if rt in by_title:
                    r['amazon_position'] = by_title[rt]

        return rows_collected

    except Exception as e:
        print("  [P0] 卖家精灵提取异常: " + str(e))
        import traceback
        traceback.print_exc()
        return []
    finally:
        close_sprite_tab(browser, saved_ws, saved_tab, target_id)


def urllib_quote(s):
    """Minimal URL encoder (avoids extra import)"""
    import urllib.parse
    return urllib.parse.quote(s)


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

    # 5.5 [P0] 卖家精灵 vxe-table 提取（已禁用，不需要跳转卖家精灵官网，插件已在亚马逊页打标）
    sprite_rows = []
    sprite_ranks = {}
    # 禁用跳转到卖家精灵官网，减少不必要的标签页打开
    # try:
    #     sprite_rows = extract_sprite_table_rank(browser, keyword, organic_marks=marks)
    #     if sprite_rows:
    #         sprite_ranks, _ = match_vxe_to_amazon_organic(sprite_rows, marks)
    #         # 把 sprite_rank 合并到 top_asins
    #         for a in top_asins:
    #             asin = a.get("asin", "")
    #             if asin in sprite_ranks:
    #                 a["sprite_rank"] = sprite_ranks[asin]
    #         print("  [P0] 已为 " + str(len(sprite_ranks)) + " 个 top ASIN 填充 sprite_rank")
    # except Exception as e:
    #     print("  [P0] 卖家精灵提取跳过: " + str(e))

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

    return marks, top_asins, sprite_rows


# --- Entry Point ---

def check_keyword(keyword):
    """Keyword monitoring main function"""
    from browser.amazon_browser import CDPBrowser

    browser = CDPBrowser()

    marks = []
    top_asins = []
    sep = "=" * 60

    try:
        marks, top_asins, sprite_rows = do_keyword_search(browser, keyword)
    except Exception as e:
        print("  Amazon search failed: " + str(e))
        import traceback
        traceback.print_exc()
        marks, top_asins, sprite_rows = [], [], []

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
                "sprite_rank": a.get("sprite_rank", ""),  # [P0] 卖家精灵交叉验证
            }
            for a in top_asins
        ],
        "raw_marks": [
            {"asin": a.get("asin", ""), "type": a.get("type", ""), "rank": a.get("rank", "")}
            for a in marks[:50]
        ],
        # [P0] 卖家精灵 vxe-table 原始数据 (最多 80 行)
        "sprite_table_rows": sprite_rows[:80] if sprite_rows else []
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

    # Keyword related ASINs: incremental merge (keep-old + add-new)
    # - 不删除已存在的 ASIN（用户手动配的可能还在用）
    # - 新出现的 ASIN 添加进来
    # - 已消失但历史出现过的 ASIN 保留（用于变动的轮转历史）
    existing = load_kw_related_asins(keyword)
    existing_map = {a.get('asin', ''): a for a in existing if a.get('asin', '')}
    new_count = 0
    for a in top_asins:
        asin = a.get('asin', '')
        if asin and asin not in existing_map:
            existing_map[asin] = {"asin": asin, "name": a.get("title", "")[:60]}
            new_count += 1
    merged = list(existing_map.values())
    if new_count > 0 or not existing:
        save_kw_related_asins(keyword, merged)
        if not existing:
            print("  [kw_rel] First run, saved " + str(len(merged)) + " related ASINs")
        else:
            print("  [kw_rel] Merged: kept " + str(len(existing)) + " + added " + str(new_count) + " = " + str(len(merged)))
    else:
        print("  [kw_rel] Cached " + str(len(merged)) + " related ASINs (no change)")

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
