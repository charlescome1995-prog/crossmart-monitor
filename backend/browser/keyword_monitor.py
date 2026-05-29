#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词市场监控 - 重写版

行为规则：
- 所有跳转用 click()，不在地址栏输入 URL
- 鼠标随机移动（贝塞尔曲线，非直线）
- 随机停顿模拟真人
- 中途随机浏览其他 ASIN 页面（不记录）
- 打开浏览器后先停顿让你检查网络和账号登录状态
- 从亚马逊搜索结果页 DOM 读取卖家精灵插件标记，区分自然位/广告位/新品
"""
import sys, os, json, random, time, re
sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode = True
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from browser.cdp_bridge import CDPBrowser
from browser.snapshot_storage import save_keyword_snapshot
from browser.human_timer import human_pause, read_pause, think_pause


# ─── 人类行为工具 ───────────────────────────────────────────────

def random_scroll(browser, times=None, min_pause=1.0, max_pause=2.0):
    """随机滚动，带随机停顿"""
    t = times if times is not None else random.randint(1, 3)
    for _ in range(t):
        amt = random.randint(300, 700)
        browser.eval(f"window.scrollBy(0, {amt})")
        time.sleep(random.uniform(min_pause, max_pause))


def random_hovers(browser, count=None):
    """随机悬停到一些商品上（模拟人类阅读）"""
    n = count if count is not None else random.randint(1, 3)
    browser.eval(f"""
        (() => {{
            const els = document.querySelectorAll('.s-result-item[data-component-type="s-search-result"]');
            const picks = Array.from(els).sort(() => Math.random() - 0.5).slice(0, {n});
            picks.forEach((el, i) => {{
                setTimeout(() => el.dispatchEvent(new MouseEvent('mouseenter', {{bubbles:true}}))), i * 800);
            }});
        }})()
    """)


def browse_random_asins(browser, count=2):
    """随机逛一些 ASIN 页面（不记录数据，只模拟人类行为）"""
    js = f"""
    (() => {{
        const links = document.querySelectorAll('a.a-link-normal[href*="/dp/"]');
        const candidates = Array.from(links)
            .map(a => {{ try {{ return {{href: a.href, asin: (a.href.match(/\\/dp\\/([A-Z0-9]+)/)||[])[1]}}; }} catch(e) {{ return null; }}})
            .filter(x => x && x.asin)
            .sort(() => Math.random() - 0.5)
            .slice(0, {count});
        if (candidates.length === 0) return;
        candidates.forEach((item, i) => {{
            setTimeout(() => {{ window.open(item.href, '_blank'); }}, i * 3500);
        }});
    }})()
    """
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
    """等页面完全渲染（给卖家精灵插件时间）"""
    time.sleep(random.uniform(min_sec, max_sec))


# ─── 核心提取逻辑 ───────────────────────────────────────────────

def extract_asin_marks_from_page(browser):
    """
    从亚马逊搜索结果页 DOM 读取卖家精灵插件标记
    优先级：
    1. 插件气泡文字（"自然第1" "广告第2" "新品第1"）——最准确
    2. 插件 data 属性（data-sg-rank 等）
    3. DOM Sponsored 标记（最后 fallback，避免误判）
    """
    js = r"""
    (() => {
        const results = [];
        const items = document.querySelectorAll('.s-result-item[data-component-type="s-search-result"]');
        items.forEach((item) => {
            // ASIN
            const asinLink = item.querySelector('a[href*="/dp/"]');
            if (!asinLink) return;
            const asinMatch = asinLink.href.match(/\/dp\/([A-Z0-9]+)/);
            if (!asinMatch) return;
            const asin = asinMatch[1];
            if (!asin || asin.length < 5) return;

            // 标题
            const titleEl = item.querySelector('h2 .a-text-normal, h2 span') || item.querySelector('h2');
            const title = titleEl ? titleEl.textContent.trim().substring(0, 100) : '';

            // 价格
            const priceEl = item.querySelector('.a-price .a-offscreen') || item.querySelector('.a-price-whole');
            const price = priceEl ? priceEl.textContent.trim() : '';

            // 评分
            const ratingEl = item.querySelector('.a-icon-alt');
            const rating = ratingEl ? ratingEl.textContent.trim() : '';

            // 评论数
            const revEl = item.querySelector('.a-size-base.s-underline-text');
            const reviews = revEl ? revEl.textContent.trim() : '';

            let keyword_type = 'natural';
            let keyword_rank = '';
            let plugin_found = false;

            // ── 方法1: 插件气泡文字（最优先） ──────────────────────
            const allEls = item.querySelectorAll('*');
            for (const el of allEls) {
                const txt = (el.textContent || '').trim();
                // 卖家精灵插件格式: "自然第1" "自然第2" "广告第1" "新品第1" "新品广告第1"
                if (/自然第\d/.test(txt)) {
                    keyword_type = 'natural';
                    keyword_rank = txt;
                    plugin_found = true;
                    break;
                }
                if (/广告第\d/.test(txt)) {
                    keyword_type = 'ad';
                    keyword_rank = txt;
                    plugin_found = true;
                    break;
                }
                if (/新品第\d/.test(txt) || /新品广告第\d/.test(txt)) {
                    keyword_type = 'new';
                    keyword_rank = txt;
                    plugin_found = true;
                    break;
                }
            }

            // ── 方法2: 插件 data 属性 ──────────────────────────────
            if (!plugin_found) {
                const attrs = ['data-sg-rank', 'data-sr', 'data-position', 'data-keyword-rank',
                               'data-ad-rank', 'data-natural-rank', 'data-sellersprite-rank',
                               'data-market', 'data-kw-rank'];
                for (const attr of attrs) {
                    const val = item.getAttribute(attr);
                    if (val) {
                        keyword_rank = val;
                        // 根据属性名判断类型
                        if (/natural/i.test(attr) || /kw-rank/i.test(attr)) keyword_type = 'natural';
                        else if (/ad|spons/i.test(attr)) keyword_type = 'ad';
                        else keyword_type = 'natural';
                        plugin_found = true;
                        break;
                    }
                }
            }

            // ── 方法3: DOM Sponsored 标记（最后 fallback）──────────
            // 只有在插件没有给出任何标记时，才用这个判断
            if (!plugin_found) {
                const adEl = item.querySelector('[class*="sponsorship"], [class*="sponsored"], [class*="ad-label"]');
                if (adEl || item.closest('[data-component-type="s-sponsored"]')) {
                    keyword_type = 'ad';
                }
                // 否则默认 natural，不主动判 new（new 必须有插件标记）
            }

            results.push({
                asin,
                type: keyword_type,
                rank: keyword_rank,
                title,
                price,
                rating,
                reviews
            });
        });
        return JSON.stringify(results);
    })()
    """
    raw = browser.eval(js)
    if not raw:
        return []
    try:
        return json.loads(raw)
    except:
        return []


def group_and_pick_top5(marks):
    """
    从提取到的 marks 中，按类型分组，取出5个不同的 ASIN
    优先级: natural_top1 > ad_top1 > new_natural_top1 > new_ad_top1 > natural_other
    """
    selected = {}

    def try_add(key, item):
        if key not in selected and item.get('asin'):
            selected[key] = item

    for item in marks:
        asin = item.get('asin', '')
        if not asin or asin in [v.get('asin') for v in selected.values()]:
            continue
        t = (item.get('type') or '').lower()

        if 'ad' in t and 'new' not in t:
            if 'ad_top1' not in selected:
                try_add('ad_top1', item)
        elif 'new' in t and 'ad' in t:
            if 'new_ad_top1' not in selected:
                try_add('new_ad_top1', item)
        elif 'new' in t:
            if 'new_natural_top1' not in selected:
                try_add('new_natural_top1', item)
        else:
            if 'natural_top1' not in selected:
                try_add('natural_top1', item)
            elif 'natural_other' not in selected:
                try_add('natural_other', item)

        if len(selected) >= 5:
            break

    # 降级补充（如果某种类型找不到，用其他类型的广告ASIN填充）
    while len(selected) < 5:
        for item in marks:
            asin = item.get('asin', '')
            existing = [v.get('asin') for v in selected.values()]
            if asin and asin not in existing:
                try_add(f'fill_{len(selected)}', item)
                break
        else:
            break

    return list(selected.values())[:5]


# ─── 人类搜索流程 ───────────────────────────────────────────────

def do_keyword_search(browser, keyword):
    """在亚马逊上搜索关键词，模拟人类行为"""
    print(f"\n{'='*60}")
    print(f"🔍 关键词市场: {keyword}")
    print(f"{'='*60}")

    # 1. 打开亚马逊，停顿等用户检查
    # 关键：强制新建空白标签页，不用任何已有标签页（避免 Neck Duster 等残留状态）
    print(f"\n  🌐 打开亚马逊（请确认账号已登录）...")
    browser.cmd("Target.createTarget", {"url": "about:blank"})
    time.sleep(1.5)
    browser.connect_tab(tab_url_filter="about:blank")
    if not browser.tab:
        browser.cmd("Target.createTarget", {"url": "about:blank"})
        time.sleep(1.5)
        browser.connect_tab(tab_url_filter="about:blank")

    browser.navigate("https://www.amazon.com/", wait_min=2, wait_max=4)
    print(f"  ⏳ 等待 {random.uniform(5,8):.0f}s（检查网络和账号登录）...")
    time.sleep(random.uniform(5, 8))

    # 2. 搜索关键词
    print(f"  🔍 在搜索框输入: {keyword}")
    time.sleep(random.uniform(1, 2))
    browser.click_element("#twotabsearchtextbox")
    human_pause(1, 3)
    browser.eval("""
        (() => {
            const inp = document.querySelector('#twotabsearchtextbox');
            if (inp) { inp.value = ''; inp.dispatchEvent(new Event('input', {bubbles:true})); }
        })()
    """)
    human_pause(0.5, 1.5)

    for ch in keyword:
        browser.eval(f"""
            (() => {{
                const inp = document.querySelector('#twotabsearchtextbox');
                if (inp) {{
                    inp.focus();
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(inp, inp.value + '{ch}');
                    inp.dispatchEvent(new Event('input', {{bubbles:true}}));
                }})()
        }})()
        """)
        time.sleep(random.uniform(0.08, 0.25))
        human_pause(0.05, 0.2)

    human_pause(0.5, 1.5)
    browser.click_element("#nav-search-submit-text, #nav-search-submit-button, input[type='submit'][aria-label]")
    print(f"  ⏳ 等待搜索结果渲染（给卖家精灵插件留时间）...")
    wait_for_render(browser, min_sec=4, max_sec=8)

    # 3. 随机滚动
    random_scroll(browser, times=random.randint(1, 2))
    human_pause(2, 5)

    # 4. 随机悬停
    random_hovers(browser, count=random.randint(1, 3))

    # 5. 随机浏览其他 ASIN
    print(f"  🚶 随机浏览其他商品（不记录）...")
    browse_random_asins(browser, count=random.randint(1, 2))
    human_pause(2, 5)

    # 6. 回到搜索结果页
    browser._refresh_tabs()
    for t in browser._raw_tabs:
        if 'amazon.com/s' in t.get('url', ''):
            browser.connect_tab(tab_index=browser._raw_tabs.index(t))
            break

    random_scroll(browser, times=2)
    wait_for_render(browser, min_sec=2, max_sec=4)
    human_pause(2, 5)

    # 7. 提取数据
    print(f"  📊 提取搜索结果数据...")
    marks = extract_asin_marks_from_page(browser)
    print(f"  ℹ️ 共找到 {len(marks)} 个商品结果")
    for m in marks[:5]:
        print(f"     [{str(m.get('type','')):15s}] {m.get('asin')} | {str(m.get('title','')[:40])}")

    top_asins = group_and_pick_top5(marks)
    print(f"  🎯 Top5 ASIN:")
    for a in top_asins:
        print(f"     [{str(a.get('type','')):20s}] {a.get('asin')} | {a.get('price','')}")

    return marks, top_asins


# ─── 主入口 ────────────────────────────────────────────────────

def check_keyword(keyword):
    """关键词监控主函数"""
    browser = CDPBrowser()

    try:
        marks, top_asins = do_keyword_search(browser, keyword)
    except Exception as e:
        print(f"  ⚠️ 亚马逊搜索失败: {e}")
        import traceback; traceback.print_exc()
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

    save_keyword_snapshot(keyword, snapshot)

    browser.close()

    print(f"\n{'='*60}")
    print(f"✅ 关键词 [{keyword}] 检查完成，找到 {len(top_asins)} 个目标 ASIN")
    print(f"{'='*60}")

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