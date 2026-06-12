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
import sys, os, json, time, random, re
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

def extract_sprite_plugin_data(browser: CDPBrowser):
    """从亚马逊页面的卖家精灵插件 DOM 提取数据（插件面板在页面内嵌）"""
    js_get_plugin_text = r"""
(function(){
    var ids = [
        'seller-sprite-extension-quick-view-listing-page',
        'seller-sprite-extension-quick-view-listing',
        'seller-sprite-extension-main-relation',
        'sellersprite-extension-inventory'
    ];
    var data = {};
    for (var i = 0; i < ids.length; i++) {
        var el = document.getElementById(ids[i]);
        if (el) {
            // 流量词用 innerHTML（Element UI 表格结构，textContent 解析不了）
            if (ids[i] === 'seller-sprite-extension-main-relation') {
                data[ids[i]] = el.innerHTML;
            } else {
                data[ids[i]] = (el.textContent||'').trim();
            }
        }
    }
    return JSON.stringify(data);
})()
"""
    try:
        raw = browser.eval(js_get_plugin_text)
        if not raw:
            return {}
        plugin_texts = json.loads(raw) if isinstance(raw, str) else raw
        metrics_text = plugin_texts.get('seller-sprite-extension-quick-view-listing-page', '')
        main_text   = plugin_texts.get('seller-sprite-extension-quick-view-listing', '')
        traffic_text = plugin_texts.get('seller-sprite-extension-main-relation', '')
        inv_text    = plugin_texts.get('sellersprite-extension-inventory', '')
    except Exception as e:
        print("  [插件] DOM 提取失败: " + str(e))
        return {}

    combined = (metrics_text + ' ' + main_text).replace('\n', ' ').replace('  ', ' ')
    data = {}

    # ── 指标面板字段 ──
    v = re.search(r'v([\d.]+)', metrics_text)
    if v: data['plugin_version'] = v.group(1)
    lqs = re.search(r'质量得分([\d.]+)', metrics_text)
    if lqs: data['lqs'] = lqs.group(1)


    sales = re.search(r'近30天销量.+?\(父体\)[^:\d]*([\d,]+)', combined)
    if sales:
        data['sales_30d_parent'] = sales.group(1).replace(',', '')
    sales_child = re.search(r'近30天销量.+?\(子体\)[^:\d]*([\d,]+)', combined)
    if sales_child:
        data['sales_30d_child'] = sales_child.group(1).replace(',', '')

    rev = re.search(r'Listing销售额\s+\$([\d,]+)', combined)
    if rev: data['revenue_30d'] = rev.group(1).replace(',', '')
    avg = re.search(r'均价\s+\$([\d.]+)', combined)
    if avg: data['avg_price'] = avg.group(1)
    bsr = re.search(r'BSR([\d,]+)', combined)
    if bsr: data['bsr'] = bsr.group(1).replace(',', '')
    fba = re.search(r'FBA费用\$([\d.]+)', combined)
    if fba: data['fba_fee'] = fba.group(1)
    variants = re.search(r'变体数(\d+)', combined)
    if variants: data['variant_count'] = variants.group(1)

    # 上架时间：格式 "2022-03-16(1,548天)" 或 "2022-03-16 (1,548天)"
    launch = re.search(r'(\d{4}-\d{2}-\d{2})\s*\((\d+)天\)', combined)
    if launch:
        data['launch_date'] = launch.group(1)
        data['days_online'] = launch.group(2)

    # 毛利率：支持 N/A 或 12.5% 格式
    profit = re.search(r'毛利率[^:\d]*([\d.]+%|[N/n]\s*/\s*[A/a])', combined)
    if profit:
        data['gross_margin'] = profit.group(1).replace(' ', '')

    # ── 主面板字段 ──
    asin_m = re.search(r'ASIN[:：]*(B[A-Z0-9]{9,10})', combined)
    if asin_m: data['asin'] = asin_m.group(1)


    # 品牌：Amazon Basics
    brand = re.search(r'品牌[:：]*\s*([A-Za-z][^\s：:]{2,30}(?:\s+[A-Za-z][^\s：:]{2,20})?)(?=\s*卖家|$)', combined)
    if brand:
        b = brand.group(1).strip()
        b = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', b)
        data['brand'] = b

    # 卖家
    seller = re.search(r'卖家[:：]*\s*([A-Za-z][^\s：:]{2,30})', combined)
    if seller: data['seller'] = seller.group(1).strip()

    # 配送类型：AMZ / FBA（用负向前瞻排除中文"卖家"）
    fulfill = re.search(r'配送[:：]*\s*([A-Z]{2,6}(?![A-Za-z\u4e00-\u9fff]))', combined)
    if fulfill: data['fulfillment'] = fulfill.group(1).strip()


    # 卖家数
    sc = re.search(r'卖家[:：]*\s*(\d+)', combined)
    if sc: data['seller_count'] = sc.group(1)

    # 大类 BSR
    bsr_main = re.search(r'#(\d+)\s+in\s+([^#\n]{3,40})', combined)
    if bsr_main:
        data['bsr_rank'] = bsr_main.group(1)
        data['bsr_category'] = bsr_main.group(2).strip()

    # 小类 BSR：第二个 # 后面到 "近30天销量" 或下一个 # 之前
    idx1 = combined.find('#')
    if idx1 >= 0:
        rest = combined[idx1 + 1:]
        idx2 = rest.find('#')
        if idx2 >= 0:
            segment = rest[idx2:]
            bsr_sub = re.search(r'#(\d+)\s+in\s+(.{3,40}?)(?=\s*#|\s*近30天)', segment)
            if bsr_sub:
                data['bsr_sub_rank'] = bsr_sub.group(1)
                data['bsr_sub_category'] = bsr_sub.group(2).strip()


    # 评分 + 评分数（合并提取）
    rating_m = re.search(r'评分[^\d]*([\d.]+)\s*\(?([\d,]+)\)?', combined)
    if rating_m:
        data['rating'] = rating_m.group(1)
        data['review_count'] = rating_m.group(2).replace(',', '')

    price_m = re.search(r'价格[^\d]*\$([\d.]+)', combined)
    if price_m: data['price'] = price_m.group(1)
    ship = re.search(r'配送时长[^\d]*(\d+)天', combined)
    if ship: data['ship_days'] = ship.group(1)
    prime = re.search(r'Prime配送时长[^\d]*(\d+)天', combined)
    if prime: data['prime_ship_days'] = prime.group(1)

    # 商品重量
    weight = re.search(r'商品重量[:：]*\s*([\d.]+)\s*ounces?\s*\(?([\d.]+)\s*g\)?', combined)
    if weight:
        data['weight_oz'] = weight.group(1)
        data['weight_g'] = weight.group(2)

    # 商品尺寸
    dims = re.search(r'商品尺寸[:：]*\s*([\d.]+)\s*x\s*([\d.]+)\s*x\s*([\d.]+)\s*inches?', combined)
    if dims:
        data['dim_l'], data['dim_w'], data['dim_h'] = dims.group(1), dims.group(2), dims.group(3)


    # 关键词统计
    for label, key in [('全部流量词', 'total_keywords'), ('自然搜索词', 'natural_keywords'),
                       ('广告流量词', 'ad_keywords'), ('搜索推荐词', 'suggest_keywords')]:
        m = re.search(rf'{re.escape(label)}[^\d]*(\d+)', combined)
        if m: data[key] = m.group(1)


    # 库存
    inv_stock = re.search(r'剩余库存(\d+)', inv_text)
    inv_price = re.search(r'剩余库存\d+\$([\d.]+)', inv_text)
    if inv_stock: data['inv_stock'] = inv_stock.group(1)
    if inv_price: data['inv_price'] = inv_price.group(1)

    # 流量词 Top 列表（Element UI 表格解析）
    # 插件使用 div.el-table__row 结构，每行 6 个 td.cell，innerHTML 含嵌套 div
    try:
        tds = re.findall(r'<td[^>]*>(.*?)</td>', traffic_text, re.DOTALL)
        cell_texts = []
        for td in tds:
            # 剥除所有 HTML 标签；把 >< 替换为换行符，这样不同嵌套层级的文本不会串线
            raw = re.sub(r'<[^>]*>', '', td)
            raw = re.sub(r'\{\{[^}]+\}\}', '', raw)
            lines = [l.strip() for l in raw.split('\n') if l.strip()]
            cell_texts.append('\n'.join(lines))

        keywords = []
        for i in range(0, len(cell_texts), 6):
            if i + 5 >= len(cell_texts):
                break
            kw = cell_texts[i+1].strip()
            click_raw = cell_texts[i+2].strip()
            click_lines = [l.strip() for l in click_raw.split('\n') if l.strip()]
            click_pct = click_lines[0] if click_lines else ''
            kw_type = click_lines[1] if len(click_lines) > 1 else ''
            organic_raw = cell_texts[i+4].strip()
            organic_lines = [l.strip() for l in organic_raw.split('\n') if l.strip()]
            organic_rank = organic_lines[0] if organic_lines else ''
            if kw:
                keywords.append({
                    'keyword': kw,
                    'traffic_pct': click_pct,
                    'type': kw_type,
                    'organic_rank': organic_rank
                })
        if keywords:
            data['traffic_keywords_top'] = keywords[:4]  # 只取前4个主要流量词
    except Exception as e:
        pass  # 流量词解析失败不影响主流程

    print(f"  [插件] 提取到 {len(data)} 个字段" + (f", 流量词 {len(keywords)} 条" if keywords else ""))
    return data


def extract_asin_data(browser: CDPBrowser):
    """从当前详情页提取完整的商品数据（修复版）"""
    print("  📊 提取商品数据...")

    js_bundle = r"""
(() => {
    const $ = (sel) => document.querySelector(sel);
    const body = document.body.innerText || '';

    const titleEl = document.querySelector('#productTitle');
    const title = (titleEl ? titleEl.textContent.trim() : (document.querySelector('h1') || {textContent: ''}).textContent.trim()).substring(0, 200);
    // title 备选：从 meta og:title 或 JSON-LD
    if (!title) {
        const ogT = document.querySelector('meta[property="og:title"]');
        if (ogT) title = ogT.content.substring(0, 200);
    }
    if (!title) {
        const ld = document.querySelector('script[type="application/ld+json"]');
        if (ld) { try { const d = JSON.parse(ld.textContent); if (d && d.name) title = d.name.substring(0, 200); } catch(e){} }
    }

    const priceWholeEl = document.querySelector('#corePrice_feature_div .a-price-whole');
    const priceOffscreenEl = document.querySelector('#corePrice_feature_div .a-offscreen');
    const corePrice = priceOffscreenEl ? priceOffscreenEl.textContent.trim() : (priceWholeEl ? '$' + priceWholeEl.textContent.trim() : '');
    let price = corePrice || (document.querySelector('.a-price .a-offscreen') || {textContent: ''}).textContent.trim();
    // price 备选：从页面 body 文本匹配 $xx.xx 或 $xx
    if (!price) { const pm = body.match(/\$\d+\.\d{2}/); if (pm) price = pm[0]; }
    if (!price) { const pm2 = body.match(/\$\d+(?:\.\d+)?/); if (pm2) price = pm2[0]; }

    const ratingEl = document.querySelector('.a-icon-alt');
    const ratingM = (ratingEl ? ratingEl.textContent.trim() : '').match(/([\d.]+)/);
    let rating = ratingM ? ratingM[1] : '';
    // rating 备选：从 body 文本匹配 "X.X out of 5 stars"
    if (!rating) { const rm = body.match(/([\d.]+)\s*out\s*of\s*5\s*stars?/i); if (rm) rating = rm[1]; }

    const reviewEl = document.querySelector('#acrCustomerReviewText');
    const reviewM = (reviewEl ? reviewEl.textContent.trim() : '').match(/([\d,]+)/);
    const review_count = reviewM ? reviewM[1].replace(/,/g, '') : '';

    const brandEl = document.querySelector('#bylineInfo');
    let brand = (brandEl ? brandEl.textContent.trim() : '').replace(/^Visit the /, '').replace(/ Store$/, '').replace(/^访问/, '').replace(/品牌旗舰店$/, '').trim();
    if (brand.length > 60) brand = brand.substring(0, 60);

    const soldByEl = document.querySelector('#merchantInfoFeature_feature_div .a-link-normal') || document.querySelector('#merchant-info');
    const soldBy = soldByEl ? soldByEl.textContent.trim() : '';

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
                else if (d && d["@graph"]) { const g = d["@graph"].find(x => x['@type'] === 'Product'); if (g && g.image) mainImg = Array.isArray(g.image) ? g.image[0] : g.image; }
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
        const discM = pt.match(/(\d+)%/);
        if (discM) prime_discount = discM[1] + '%';
        else if (pt.includes('Prime')) prime_discount = pt.trim().substring(0, 30);
    }
    if (prime_discount === '未开启') {
        if (lowerBody.includes('prime member') && lowerBody.includes('%')) {
            const pdM = body.match(/prime.*?(\d+)%/i);
            if (pdM) prime_discount = pdM[1] + '%';
        }
    }

    // ── 评分分布（直方图） ──
    const rating_distribution = {};
    const histBars = document.querySelectorAll('#histogramTable .a-histogram-bar');
    if (histBars.length > 0) {
        histBars.forEach(bar => {
            const barEl = bar.querySelector('.a-bar-container');
            const countEl = bar.querySelector('.a-histogram-count');
            const barAria = barEl ? barEl.getAttribute('aria-label') || '' : '';
            const countText = countEl ? countEl.textContent.trim() : '';
            const starsM = barAria.match(/(\d+)星/);
            const pctM = barAria.match(/(\d+)%/);
            if (starsM) {
                const star = starsM[1] + 'star';
                const pct = pctM ? pctM[1] + '%' : '';
                const count = countText.replace(/[,，]/g, '').match(/(\d+)/);
                rating_distribution[star] = { pct: pct, count: count ? count[1] : countText };
            }
        });
    }

    const result = {
        title, price, rating, review_count, brand, soldBy,
        main_image: mainImg,
        bsr: bsr, bsr_subcategory: bsrSubCategory, bsr_subrank: bsrSubRank, bsr_all_subranks: bsrAllSubRanks,
        badges: badges,
        deal_activity: deal_activity,
        coupon: coupon,
        prime_discount: prime_discount,
        rating_distribution: rating_distribution,
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
        # ── 等待页面关键元素加载（最长30秒）──
        deadline = time.time() + 30
        while time.time() < deadline:
            ready = browser.eval("""(() => {
                var titleEl = document.querySelector('#productTitle');
                var titleOk = titleEl && titleEl.textContent.trim().length > 0;
                var imgEl = document.querySelector('#landingImage');
                var imgOk = imgEl && imgEl.complete && imgEl.naturalWidth > 0;
                return { titleOk: titleOk, imgOk: imgOk, ready: titleOk };
            })()""")
            if ready and ready.get('ready'):
                elapsed = time.time() - (deadline - 30)
                print(f"  页面加载完成，耗时 {elapsed:.1f}s (title={ready.get('titleOk')}, img={ready.get('imgOk')})")
                break
            time.sleep(1)
        time.sleep(random.uniform(0.3, 0.8))  # 再等1-3秒让插件彻底渲染
        amazon_data = extract_asin_data(browser)
        if not amazon_data.get("bsr"):
            bsr = extract_bsr_direct(browser)
            if bsr:
                amazon_data["bsr"] = bsr
        print_card(amazon_data)

        print("  亚马逊检查完成")
    except Exception as e:
        print("  亚马逊检查失败: %s" % e)

    # ─── Phase A2: 卖家精灵插件 DOM（直接从页面内嵌插件提取，插件在页面上浮窗显示）───
    if mode == "full":
        print("\n" + "="*50)
        print("卖家精灵插件数据")
        print("="*50)
        time.sleep(random.uniform(0.5, 1.5))  # 等待插件 DOM 完全渲染
        try:
            plugin_data = extract_sprite_plugin_data(browser)
            if plugin_data:
                # 插件数据与 amazon_data 合并（插件字段加前缀 sprite_ 避免覆盖）
                for k, v in plugin_data.items():
                    amazon_data['sprite_' + k] = v
                print("  插件数据提取完成")
            else:
                print("  插件面板未检测到（可能未安装或未激活）")
        except Exception as e:
            print("  插件提取失败: %s" % e)

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