#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASIN监控主入口 — 完整版
用法:
  python browser/asin_monitor.py B0XXXXXXX           # 完整检查(亚马逊+卖家精灵)
  python browser/asin_monitor.py B0XXXXXXX --amazon  # 只查亚马逊
  python browser/asin_monitor.py B0XXXXXXX --discover  # 只做竞品关联发现（不查亚马逊）
  python browser/asin_monitor.py B0XXXXXXX --status   # 查看状态
"""
import sys, os, json, time, random
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from browser.cdp_bridge import CDPBrowser
from browser.amazon_browser import AmazonBrowser
from browser.sprite_bridge import SpriteBrowser
from browser.snapshot_storage import (
    save_asin_snapshot, load_latest_asin, diff_asin, diff_summary,
    save_asin_meta, load_asin_meta,
)
from browser.human_timer import get_daily_plan

# ─── DOM数据提取工具 ───

def extract_asin_data(browser: CDPBrowser):
    """从当前详情页提取完整的商品数据（修复版）"""
    print("  📊 提取商品数据...")

    js_bundle = r"""
(() => {
    const $ = (sel) => document.querySelector(sel) ? document.querySelector(sel).textContent.trim() : '';
    const body = document.body.innerText || '';

    const title = ($('#productTitle') || $('h1')).substring(0, 200);
    // title 备选：从 meta og:title 或 JSON-LD
    if (!title) {
        const ogT = document.querySelector('meta[property="og:title"]');
        if (ogT) title = ogT.content.substring(0, 200);
    }
    if (!title) {
        const ld = document.querySelector('script[type="application/ld+json"]');
        if (ld) { try { const d = JSON.parse(ld.textContent); if (d && d.name) title = d.name.substring(0, 200); } catch(e){} }
    }

    const corePrice = $('#corePrice_feature_div .a-offscreen') ||
                     ($('#corePrice_feature_div .a-price-whole') ? '$' + $('#corePrice_feature_div .a-price-whole') : '');
    let price = corePrice || $('.a-price .a-offscreen') || '';
    // price 备选：从页面 body 文本匹配 $xx.xx 或 $xx
    if (!price) { const pm = body.match(/\$\d+\.\d{2}/); if (pm) price = pm[0]; }
    if (!price) { const pm2 = body.match(/\$\d+(?:\.\d+)?/); if (pm2) price = pm2[0]; }

    const ratingM = ($('.a-icon-alt') || '').match(/([\d.]+)/);
    let rating = ratingM ? ratingM[1] : '';
    // rating 备选：从 body 文本匹配 "X.X out of 5 stars"
    if (!rating) { const rm = body.match(/([\d.]+)\s*out\s*of\s*5\s*stars?/i); if (rm) rating = rm[1]; }

    const reviewM = ($('#acrCustomerReviewText') || '').match(/([\d,]+)/);
    const review_count = reviewM ? reviewM[1].replace(/,/g, '') : '';

    let brand = ($('#bylineInfo') || '').replace(/^Visit the /, '').replace(/ Store$/, '').replace(/^访问/, '').replace(/品牌旗舰店$/, '').trim();
    if (brand.length > 60) brand = brand.substring(0, 60);

    const soldBy = $('#merchantInfoFeature_feature_div .a-link-normal') || $('#merchant-info') || '';

    // ── 产品图片（多个备选选择器 + 高分辨率替换）──
    let mainImg = '';
    const imgSelectors = [
        '#landingImage',
        '#imgTagWrapperId img',
        '#main-image',
        '#imgBlkFront',
        '#mainImage',
        '#ebay-image img',
        '.a-dynamic-image',
        '#altImages img',
        '#richThumbnails img',
    ];
    for (const sel of imgSelectors) {
        const el = document.querySelector(sel);
        if (el) {
            mainImg = el.getAttribute('src') || el.getAttribute('data-old-hires') || '';
            if (mainImg) break;
        }
    }
    // 尝试从 data-a-dynamic-image 提取最高分辨率图片
    if (!mainImg) {
        const dynEl = document.querySelector('[data-a-dynamic-image]');
        if (dynEl) {
            try {
                const dynData = JSON.parse(dynEl.getAttribute('data-a-dynamic-image') || '{}');
                const urls = Object.keys(dynData);
                if (urls.length > 0) {
                    // 取分辨率最高的（最后一张通常是主图）
                    mainImg = urls[urls.length - 1];
                }
            } catch(e) {}
        }
    }
    // 升级到高分辨率
    if (mainImg) {
        mainImg = mainImg.replace(/\._AC_\w+_\.jpg/, '._AC_SL1500_.jpg');
        mainImg = mainImg.replace(/\._SY\d+_\.jpg/, '._AC_SL1500_.jpg');
        mainImg = mainImg.replace(/\._SX\d+_\.jpg/, '._AC_SL1500_.jpg');
        // 去掉尺寸后缀参数
        mainImg = mainImg.replace(/\?.*$/, '');
    }
    // main_image 备选：从 meta og:image
    if (!mainImg) {
        const ogI = document.querySelector('meta[property="og:image"]');
        if (ogI && ogI.content) mainImg = ogI.content;
    }
    // main_image 备选：从 JSON-LD product image
    if (!mainImg) {
        const ldI = document.querySelector('script[type="application/ld+json"]');
        if (ldI) {
            try {
                const d = JSON.parse(ldI.textContent);
                if (d && d.image) mainImg = Array.isArray(d.image) ? d.image[0] : d.image;
                else if (d && d.@graph) { const g = d.@graph.find(x => x['@type'] === 'Product'); if (g && g.image) mainImg = Array.isArray(g.image) ? g.image[0] : g.image; }
            } catch(e){}
        }
    }

    // ── BSR ──
    let bsr = '', bsrSubCategory = '', bsrSubRank = '', bsrAllSubRanks = [];
    const bsrSection = body.match(/Best Sellers Rank[\s\S]{0,500}/);
    if (bsrSection) {
        bsr = bsrSection[0].substring(0, 300);
        const topM = bsr.match(/#([\d,]+)\s+in\s+([^#\n\r]+)/);
        if (topM) { bsrSubRank = topM[1].replace(/,/g, ''); bsrSubCategory = topM[2].trim().substring(0, 100); }
        // 提取所有 #数字（第一个是大类，其余是小类/子分类排名）
        const allMatches = bsr.matchAll(/#([\d,]+)\s+in\s+([^\n\r]+)/g);
        let idx = 0;
        for (const m of allMatches) {
            if (idx === 0) { idx++; continue; } // 跳过第一个（已作为大类）
            bsrAllSubRanks.push(m[1].replace(/,/g, ''));
            idx++;
            if (bsrAllSubRanks.length >= 5) break; // 最多取5个
        }
    }

    // ── Badges (多个来源) ──
    const badges = [];
    const lowerBody = body.toLowerCase();
    if (lowerBody.includes("bestseller") || document.querySelector('[class*="bestseller"], #detailBulletsWrapper_feature_div [class*="bestseller"]')) badges.push('BS');
    if (lowerBody.includes("amazon's choice") || document.querySelector('[class*="choices"], #acBadge')) badges.push('AC');
    if (lowerBody.includes("new release") || document.querySelector('[class*="new-releases"]')) badges.push('NR');
    if (document.querySelector('#aplusBrandLogo, #aplus_feature_div iframe, #aplus3pFeatureText')) badges.push('A+');
    const badgeEl = document.querySelector('.a-badge-container');
    if (badgeEl) {
        const bt = badgeEl.innerText || '';
        if (bt.includes('Bestseller')) badges.push('BS');
        if (bt.includes('New')) badges.push('NR');
    }
    // A+ badge
    if (badges.indexOf('A+') === -1 && document.querySelector('#aplus_feature_div')) badges.push('A+');

    // ── Deal 活动 ──
    let deal_activity = '无';
    const dealEl = document.querySelector('#dealBadge_feature_div, #dealsLabel_feature_div, .deal-sash, [class*="deal-badge"]');
    if (dealEl) {
        const dt = dealEl.innerText || '';
        if (dt.includes('Lightning Deal')) deal_activity = 'Lightning Deal';
        else if (dt.includes('Deal of the Day') || dt.includes('DOTD')) deal_activity = 'Deal of the Day';
        else if (dt.includes('Best Deal')) deal_activity = 'Best Deal';
        else if (dt.includes('Deal')) deal_activity = 'Deal';
        else deal_activity = dt.trim() || 'Deal';
    }
    // 从 body 文本二次确认
    if (deal_activity === '无') {
        if (lowerBody.includes('lightning deal')) deal_activity = 'Lightning Deal';
        else if (lowerBody.includes('deal of the day')) deal_activity = 'Deal of the Day';
        else if (lowerBody.includes('best deal')) deal_activity = 'Best Deal';
    }

    // ── 优惠券 ──
    let coupon = '无';
    const couponEl = document.querySelector('#couponPopoverFeature, [data-coupon], .coupon-badge, #sidesheet看到她 .coupon');
    if (couponEl) {
        const ct = couponEl.innerText || '';
        const pctM = ct.match(/(\d+)%/);
        const amtM = ct.match(/\$(\d+\.?\d*)/);
        if (pctM) coupon = pctM[1] + '% off';
        else if (amtM) coupon = '$' + amtM[1] + ' off';
        else if (ct.trim()) coupon = ct.trim();
        else coupon = '有优惠券';
    }
    if (coupon === '无' && lowerBody.includes('coupon')) {
        const cM = body.match(/(\d+)%\s*off.*coupon|save\s*\$(\d+\.?\d*)/i);
        if (cM) coupon = cM[1] ? cM[1] + '% off' : '$' + cM[2] + ' off';
    }

    // ── Prime 专享折扣 ──
    let prime_discount = '未开启';
    const primeEl = document.querySelector('#primeExclusiveExtraContent, #primeBenefits, .prime-benefits, #prime-ingress-features');
    if (primeEl) {
        const pt = primeEl.innerText || '';
        const discM = pt.match((\d+)%/);
        if (discM) prime_discount = discM[1] + '%';
        else if (pt.includes('Prime')) prime_discount = pt.trim().substring(0, 30);
    }
    if (prime_discount === '未开启') {
        if (lowerBody.includes('prime member') && lowerBody.includes('%')) {
            const pdM = body.match(/prime.*?(\d+)%/i);
            if (pdM) prime_discount = pdM[1] + '%';
        }
    }

    const result = {
        title, price, rating, review_count, brand, soldBy,
        main_image: mainImg,
        bsr: bsr, bsr_subcategory: bsrSubCategory, bsr_subrank: bsrSubRank, bsr_all_subranks: bsrAllSubRanks,
        badges: badges,
        deal_activity: deal_activity,
        coupon: coupon,
        prime_discount: prime_discount,
        snapshot_time: new Date().toISOString(),
    };
    return JSON.stringify(result);
})()
"""
    try:
        raw = browser.eval(js_bundle)
        if raw:
            data = json.loads(raw) if isinstance(raw, str) else raw
            return data
    except Exception as e:
        print("  JS提取错误: " + str(e))
    return {}


def extract_bsr_direct(browser):
    """直接从页面文本提 BSR（备用）"""
    js = r"""
(() => {
    const text = document.body.innerText || '';
    const m = text.match(/Best Sellers Rank[\s\S]{0,200}/);
    return m ? m[0].substring(0,300) : '';
})()
"""
    try:
        r = browser.eval(js)
        return r if r else ""
    except:
        return ""


def print_card(data):
    print("  商品标题: " + str(data.get("title","(无)")[:80]))
    print("  当前价格: " + str(data.get("price","")))
    print("  评分: " + str(data.get("rating","")))
    print("  评论数: " + str(data.get("review_count","")))
    print("  品牌: " + str(data.get("brand","")))
    print("  BSR: " + str(data.get("bsr_subrank","")) + " (" + str(data.get("bsr_subcategory","")[:40]) + ")")
    badge = data.get("badge","")
    if badge:
        print("  标签: " + badge)


def _fetch_related_asin_data(browser, related_list):
    """批量抓取关联ASIN实时数据（复用已有浏览器）"""
    results = []
    for rel in related_list:
        asin = rel.get("asin","")
        source = rel.get("source","")
        if not asin:
            continue
        print(f"\n  [关联] 抓取 {asin} ({source}) ...")
        try:
            amazon = AmazonBrowser(browser)
            amazon.search_for_asin(asin)
            browser.scroll_down(times=1, min_pause=0.3, max_pause=0.8)
            time.sleep(0.5)
            data = extract_asin_data(browser)
            results.append({
                "asin": asin, "source": source,
                "title": data.get("title",""),
                "price": data.get("price",""),
                "rating": data.get("rating",""),
                "reviews": data.get("review_count",""),
                "bsr": data.get("bsr_subrank",""),
                "brand": data.get("brand",""),
            })
        except Exception as e:
            print(f"  ⚠️ 抓取关联ASIN {asin} 失败: {e}")
            results.append({
                "asin": asin, "source": source,
                "title": "", "price": "", "rating": "", "reviews": "",
                "bsr": "", "brand": "",
            })
    return results


# ─── 主函数 ───

def check_asin(asin, search_keyword=None, use_sprite=True, mode="full"):
    """
    mode:
      "full"       - 完整流程（亚马逊 + 卖家精灵 + 快照）
      "amazon"     - 只查亚马逊（不调用卖家精灵）
      "discover"   - 只做竞品关联发现（通过卖家精灵查竞品），输出 JSON 到 stdout
    """
    print("\n" + "="*70)
    print("ASIN 监控检查")
    print("  ASIN: %s" % asin)
    print("  模式: %s" % mode)
    print("  时间: %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("="*70)

    # ── discover 模式：只做竞品发现 ──
    if mode == "discover":
        import re as _re
        browser = CDPBrowser()
        browser.connect_tab(tab_url_filter="about:blank")
        if not browser.tab:
            browser.cmd("Target.createTarget", {"url": "about:blank"})
            time.sleep(0.5)
            browser.connect_tab(tab_url_filter="about:blank")
        try:
            sprite = SpriteBrowser(browser)
            result = sprite.lookup_competitor(asin)
            page_text = result.get("text", "") if isinstance(result, dict) else ""
            found = _re.findall(r'B[A-Z0-9]{9,10}', page_text)
            related = []
            seen = set()
            for a in found:
                a = a.strip()
                if a != asin and a not in seen and len(a) == 10 and a.startswith('B0'):
                    seen.add(a)
                    related.append({"asin": a, "source": "competitor"})
            related = related[:5]
            print("\n  [竞品发现] 主ASIN %s → %d 个关联ASIN: %s"
                  % (asin, len(related), [r["asin"] for r in related]))
            # 输出 JSON 到 stdout（供 run_monitor.py 捕获）
            print(json.dumps(related, ensure_ascii=False))
        finally:
            try:
                browser.close()
            except:
                pass
        return

    # ── amazon / full 模式 ──
    browser = CDPBrowser()
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
        amazon.browse_homepage()
        if random.random() < 0.15:
            amazon.browse_category()
        amazon.search_for_asin(asin, search_keyword)
        browser.scroll_down(times=1, min_pause=0.3, max_pause=0.8)
        # ── 等待插件加载（最长30秒）──
        deadline = time.time() + 30
        while time.time() < deadline:
            ready = browser.eval("""
                document.querySelector('#productTitle') !== null ||
                document.querySelector('#dpContainer') !== null ||
                document.readyState === 'complete'
            """)
            if ready:
                break
            time.sleep(1)
        time.sleep(random.uniform(0.3, 0.8))  # 再等1-3秒让插件彻底渲染
        amazon_data = extract_asin_data(browser)
        if not amazon_data.get("bsr"):
            bsr = extract_bsr_direct(browser)
            if bsr:
                amazon_data["bsr"] = bsr
        print_card(amazon_data)
        if random.random() < 0.15:
            amazon.view_reviews()
        print("  亚马逊检查完成")
    except Exception as e:
        print("  亚马逊检查失败: %s" % e)

    # ─── Phase B: 卖家精灵（可选）───
    related_asins_meta = []
    if use_sprite and mode == "full":
        print("\n" + "="*50)
        print("卖家精灵数据查询")
        print("="*50)
        try:
            sprite = SpriteBrowser(browser)
            sprite_data = sprite.full_asin_check(asin)
            print("  卖家精灵查询完成")
        except Exception as e:
            print("  卖家精灵失败: %s" % e)

        # ── 关联 ASIN 发现 → 写入 asin_related_asins.json（统一由 run_monitor.py 处理，这里不再写入 _meta.json）──
        # 注：关联 ASIN 发现逻辑已移至 run_monitor.py + discover_related.py，
        # asin_monitor.py 此处只负责主 ASIN 的监控，不处理关联 ASIN 发现

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
    print("\n" + "="*50)
    print("ASIN: %s" % asin)
    print("价格: %s" % amazon_data.get("price",""))
    print("评分: %s %s (%s reviews)" % (
        amazon_data.get("rating",""),
        amazon_data.get("badge",""),
        amazon_data.get("review_count","")))
    print("排名: %s  (%s)" % (
        amazon_data.get("bsr_subrank",""),
        amazon_data.get("bsr_subcategory","")[:40]))
    if changes.get("has_changes"):
        print("变化: %s" % ", ".join(changes["changes"][:5]))
    print("="*50)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("asin", nargs="?")
    parser.add_argument("--amazon", action="store_true")
    parser.add_argument("--discover", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    if not args.asin:
        print("用法: python asin_monitor.py ASIN [--amazon] [--discover] [--status]")
        sys.exit(1)

    mode = "full"
    if args.amazon:
        mode = "amazon"
    elif args.discover:
        mode = "discover"

    if args.status:
        from browser.snapshot_storage import load_latest_asin
        prev = load_latest_asin(args.asin)
        if prev:
            print("已有快照，时间: %s" % prev.get("_timestamp","未知"))
            print("价格: %s" % prev.get("data",{}).get("price",""))
        else:
            print("无快照记录")
        sys.exit(0)

    check_asin(args.asin.strip(), use_sprite=True, mode=mode)