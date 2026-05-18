#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASIN监控主入口 — 完整版

单Edge浏览器（闫旭的默认Edge），DOM提取数据，不截图。
每次都让浏览器可见地执行操作。

用法:
  python browser/asin_monitor.py B0XXXXXXX           # 完整检查(亚马逊+卖家精灵)
  python browser/asin_monitor.py B0XXXXXXX --amazon   # 只查亚马逊
  python browser/asin_monitor.py B0XXXXXXX --status   # 查看状态
"""
import sys, os, json, time, random
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from browser.cdp_bridge import CDPBrowser
from browser.amazon_browser import AmazonBrowser
from browser.sprite_bridge import SpriteBrowser
from browser.snapshot_storage import save_asin_snapshot, load_latest_asin, diff_asin, diff_summary
from browser.human_timer import get_daily_plan

# ─── DOM数据提取工具 ───

def extract_asin_data(browser: CDPBrowser):
    """从当前详情页提取完整的商品数据（修复版）"""
    print("  📊 提取商品数据...")

    js_bundle = r"""
(() => {
    const $ = (sel) => { const e = document.querySelector(sel); return e ? e.textContent.trim() : ''; };
    
    // 标题
    const title = ($('#productTitle') || $('h1')).substring(0,200);
    
    // 价格：只用核心价格区域，排除变体价格
    const corePrice = $('#corePrice_feature_div .a-offscreen') ||
                     ($('#corePrice_feature_div .a-price-whole') ? 
                      '$' + $('#corePrice_feature_div .a-price-whole') : '');
    // fallback: 如果核心区没有，用第一个.a-price
    const price = corePrice || $('.a-price .a-offscreen') || '';
    
    // 评分 - 只取数字
    const ratingRaw = $('.a-icon-alt') || '';
    const ratingM = ratingRaw.match(/([\d.]+)/);
    const rating = ratingM ? ratingM[1] : ratingRaw;
    
    // 评论数 - 纯数字
    const reviewRaw = $('#acrCustomerReviewText') || '';
    const reviewM = reviewRaw.match(/([\d,]+)/);
    const review_count = reviewM ? reviewM[1].replace(/,/g,'') : reviewRaw;
    
    // 品牌 - 去掉"访问"和"Store"的中英文
    let brand = ($('#bylineInfo') || '').replace(/^Visit the /,'').replace(/ Store$/,'').replace(/^访问/,'').replace(/品牌旗舰店$/,'').trim();
    if (brand.length > 60) brand = brand.substring(0,60);
    
    // 卖家
    const soldBy = $('#merchantInfoFeature_feature_div .a-link-normal') ||
                   $('#merchant-info') || '';
    
    // 主图 - 高清版
    let mainImg = (document.querySelector('#landingImage') ||
                   document.querySelector('#imgTagWrapperId img') ||
                   document.querySelector('#main-image'))?.getAttribute('src') || '';
    mainImg = mainImg.replace(/\._AC_SX\d+_\.jpg/, '._AC_SL1500_.jpg');
    
    // 原价（划线价）
    const listPriceRaw = $('#corePrice_feature_div .a-text-price .a-offscreen') || '';
    
    // BSR 从页面大段文本中提取
    let bsr = '', bsrSubCategory = '', bsrSubRank = '';
    const bodyText = document.body.innerText || '';
    const bsrSection = bodyText.match(/Best Sellers Rank[\s\S]{0,500}/);
    if (bsrSection) {
        bsr = bsrSection[0].substring(0, 300);
        // 找大类BSR: #N in Category
        const topM = bsr.match(/#([\d,]+)\s+in\s+([^#\n\r]+)/);
        if (topM) {
            bsrSubCategory = topM[2].trim().substring(0,80);
            bsrSubRank = topM[1];
        }
    }
    
    return JSON.stringify({
        title: title,
        price: price,
        rating: rating,
        review_count: review_count,
        bsr: bsr,
        brand: brand,
        sold_by: (soldBy || '').substring(0,80),
        bsr_sub_category: bsrSubCategory,
        bsr_sub_rank: bsrSubRank,
        main_image: mainImg,
        list_price: listPriceRaw
    });
})()
"""
    try:
        raw = browser.eval(js_bundle)
        if raw:
            return json.loads(raw)
    except Exception as e:
        print("  ⚠️ 提取失败: %s" % e)
    return {}

def extract_bsr_direct(browser: CDPBrowser):
    """
    BSR在商品详情页底部，需要滚动让懒加载触发。
    如果上面没拿到，这里专门拿。
    """
    browser.scroll_down(times=3, min_pause=0.5, max_pause=1.5)
    time.sleep(2)
    js = """
    (() => {
        const cells = document.querySelectorAll('#productDetails_detailBullets_sections1 td, ' +
                                                 '#detailBullets_feature_div li, ' +
                                                 '#SalesRank tr td');
        for (const c of cells) {
            const t = c.textContent.trim();
            if (t.includes('#') || t.includes('Best Sellers')) return t.substring(0, 200);
            if (/^#[0-9,]+/.test(t)) return t;
        }
        // 二选：看页面body里有没有bsr
        const body = document.body.innerText;
        const match = body.match(/Best Sellers Rank[^\\n]*\\n([^\\n]+)/);
        return match ? match[1].trim().substring(0, 200) : '';
    })()
    """
    try:
        return browser.eval(js) or ""
    except:
        return ""

def print_card(data: dict):
    """打印商品数据卡片 8维度"""
    title = data.get("title", "?")[:50]
    price = data.get("price", "?")
    list_p = data.get("list_price", "")
    rating = data.get("rating", "?")
    reviews = data.get("review_count", "?")
    bsr = data.get("bsr", "")[:50]
    bsr_sub = data.get("bsr_sub_category", "")
    bsr_sub_num = data.get("bsr_sub_rank", "")
    brand = data.get("brand", "?")
    sold_by = data.get("sold_by", "")
    discount = ""
    if list_p and price:
        try:
            lp = float(list_p.replace("$","").replace(",",""))
            cp = float(price.replace("$","").replace(",",""))
            if lp and cp and lp > cp:
                discount = "-" + str(round((1-cp/lp)*100)) + "%"
        except:
            pass
    print("  --------------------------------")
    print("  %s" % title)
    print("  Brand: %s" % brand)
    if sold_by:
        print("  Seller: %s" % sold_by[:30])
    if discount:
        print("  Price: %s (was %s, %s)" % (price, list_p, discount))
    else:
        print("  Price: %s" % price)
    print("  Rating: %s  (%s reviews)" % (rating, reviews))
    if bsr:
        print("  BSR Top: %s" % bsr)
    if bsr_sub and bsr_sub_num:
        print("  BSR Sub: #%s in %s" % (bsr_sub_num, bsr_sub[:30]))
    print("  --------------------------------")

# ─── 主函数 ───

def check_asin(asin, search_keyword=None, use_sprite=True):
    print("\n" + "="*70)
    print("ASIN监控检查")
    print("  ASIN: %s" % asin)
    print("  时间: %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("="*70)

    browser = CDPBrowser()
    # 打开一个空白标签页开始操作
    browser.connect_tab(tab_url_filter="about:blank")
    if not browser.tab:
        browser.cmd("Target.createTarget", {"url": "about:blank"})
        time.sleep(0.5)
        browser.connect_tab(tab_url_filter="about:blank")

    amazon_data = {}
    sprite_data = {}

    # ─── Phase A: 亚马逊 ───
    print("\n" + "="*50)
    print("亚马逊前台浏览")
    print("="*50)

    try:
        amazon = AmazonBrowser(browser)

        # 1. 逛首页
        amazon.browse_homepage()

        # 2. 逛随机类目 (不用每次都搞，概率降低)
        if random.random() < 0.5:
            amazon.browse_category()

        # 3. 搜目标ASIN
        amazon.search_for_asin(asin, search_keyword)

        # 4. 在详情页浏览（假装看）
        browser.scroll_down(times=1, min_pause=1, max_pause=2)
        time.sleep(1)

        # 5. 提取数据
        amazon_data = extract_asin_data(browser)
        if not amazon_data.get("bsr"):
            bsr = extract_bsr_direct(browser)
            if bsr:
                amazon_data["bsr"] = bsr

        print_card(amazon_data)

        # 6. 浏览评价页 (伪装)
        if random.random() < 0.5:
            amazon.view_reviews()

        print("  亚马逊检查完成")

    except Exception as e:
        print("  亚马逊检查失败: %s" % e)

    # ─── Phase B: 卖家精灵 ───
    if use_sprite:
        print("\n" + "="*50)
        print("卖家精灵数据查询")
        print("="*50)

        try:
            # 开新标签页去卖家精灵
            browser.open_new_tab("https://www.sellersprite.com")
            sprite = SpriteBrowser(browser)
            sprite_data = sprite.full_asin_check(asin)
            print("  卖家精灵查询完成")
        except Exception as e:
            print("  卖家精灵失败: %s" % e)

    # ─── Phase C: 对比保存 ───
    print("\n" + "="*50)
    print("变化对比")
    print("="*50)

    previous = load_latest_asin(asin)
    changes = {"has_changes": False, "changes": []}
    if previous:
        old_data = previous.get("data", {})
        report = diff_asin(old_data, amazon_data)
        changes = report
        if report["has_changes"]:
            print("  检测到变化!")
            for c in report["changes"]:
                print("    * %s" % c)
        else:
            print("  价格/评分/评论 均无变化")
    else:
        print("  首次记录")

    snapshot_data = {
        **amazon_data,
        "_sprite_text": sprite_data.get("competitor", {}).get("text", "")[:2000] if sprite_data else "",
        "_timestamp": datetime.now().isoformat(),
    }
    save_asin_snapshot(asin, snapshot_data)

    browser.close()

    # ─── 最终摘要 ───
    print("\n" + "="*70)
    summary = diff_summary(asin, changes)
    print("摘要: %s" % summary)
    print("  ASIN: %s" % asin)
    print("  商品: %s" % amazon_data.get('title','?')[:60])
    print("  价格: %s" % amazon_data.get('price','?'))
    print("  评分: %s" % amazon_data.get('rating','?'))
    print("  评论: %s" % amazon_data.get('review_count','?'))
    if changes["has_changes"]:
        for c in changes["changes"]:
            print("  * %s" % c)
    print("="*70)

    return {
        "asin": asin,
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "changes": changes,
        "has_changes": changes["has_changes"],
        "data": amazon_data,
    }


def show_status(asin):
    latest = load_latest_asin(asin)
    if not latest:
        print("  %s 暂无监控数据" % asin)
        return
    data = latest.get("data", {})
    ts = latest.get("_timestamp", latest.get("timestamp", ""))
    print("\n%s" % ("="*40))
    print("%s 监控状态" % asin)
    print("="*40)
    print("  最后检查: %s" % ts)
    print("  标题: %s" % data.get('title','?')[:60])
    print("  价格: %s" % data.get('price','?'))
    print("  评分: %s / %s条评论" % (data.get('rating','?'), data.get('review_count','?')))
    bsr = data.get('bsr','')
    if bsr:
        print("  BSR: %s" % bsr[:60])
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ASIN监控")
    parser.add_argument("asin", nargs="?", help="ASIN")
    parser.add_argument("--keywords", "-k", help="搜索关键词")
    parser.add_argument("--amazon", "-a", action="store_true", help="只查亚马逊")
    parser.add_argument("--status", "-s", action="store_true", help="查看状态")
    args = parser.parse_args()

    if args.status and args.asin:
        show_status(args.asin)
        sys.exit(0)

    if not args.asin:
        print("python browser/asin_monitor.py B0XXXXXXX")
        print("python browser/asin_monitor.py B0XXXXXXX --status")
        sys.exit(1)

    check_asin(args.asin, args.keywords, use_sprite=not args.amazon)
