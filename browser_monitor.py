#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用 browser 工具直接执行 ASIN 监控（不依赖 CDP 端口）
通过 OpenClaw 的 browser 工具控制 Edge，提取插件数据
"""
import subprocess, json, time, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ASIN = "B09542G9ZN"
KEYWORD = "batana oil"

JS_SPRITE_EXTRACT = r"""
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
        if (el) data[ids[i]] = (el.textContent||'').trim();
    }
    return JSON.stringify(data);
})()
"""

JS_AMAZON_EXTRACT = r"""
(function(){
    var $ = function(sel){return document.querySelector(sel)};
    var body = document.body.innerText||'';
    var titleEl = document.querySelector('#productTitle');
    var title = titleEl ? titleEl.textContent.trim().substring(0,200) : '';
    var priceEl = document.querySelector('#corePrice_feature_div .a-offscreen');
    var price = priceEl ? priceEl.textContent.trim() : '';
    if (!price) { var pm = body.match(/\$\d+\.\d{2}/); if (pm) price = pm[0]; }
    var ratingEl = document.querySelector('.a-icon-alt');
    var ratingM = ratingEl ? ratingEl.textContent.trim().match(/([\d.]+)/) : null;
    var rating = ratingM ? ratingM[1] : '';
    var reviewEl = document.querySelector('#acrCustomerReviewText');
    var reviewM = reviewEl ? reviewEl.textContent.trim().match(/([\d,]+)/) : null;
    var review_count = reviewM ? reviewM[1].replace(/,/g,'') : '';
    var brandEl = document.querySelector('#bylineInfo');
    var brand = brandEl ? brandEl.textContent.trim().replace(/^Visit the /,'').replace(/ Store$/,'').trim() : '';
    var mainImgEl = document.querySelector('#landingImage');
    var mainImg = mainImgEl ? (mainImgEl.getAttribute('src')||mainImgEl.getAttribute('data-old-hires')||'') : '';
    if (mainImg) { mainImg = mainImg.replace(/\._AC_\w+_\.jpg/,'._AC_SL1500_.jpg').replace(/\?.*$/,''); }
    var bsrSection = body.match(/Best Sellers Rank[\s\S]{0,500}/);
    var bsr = bsrSection ? bsrSection[0].substring(0,300) : '';
    var bsrSubRank = '', bsrSubCategory = '';
    var topM = bsr.match(/#([\d,]+)\s+in\s+([^\n\r]+)/);
    if (topM) { bsrSubRank = topM[1].replace(/,/g,''); bsrSubCategory = topM[2].trim().substring(0,100); }
    var badges = [];
    if (body.toLowerCase().includes('bestseller')) badges.push('BS');
    if (body.toLowerCase().includes("amazon's choice")) badges.push('AC');
    if (body.toLowerCase().includes('new release')) badges.push('NR');
    var deal_activity = '无';
    var dealEl = document.querySelector('#dealBadge_feature_div, #dealsLabel_feature_div');
    if (dealEl) { var dt = dealEl.innerText||''; if (dt.includes('Lightning')) deal_activity='Lightning Deal'; else if (dt.includes('Deal')) deal_activity='Deal'; }
    var coupon = '无';
    var couponEl = document.querySelector('[data-coupon], .coupon-badge');
    if (couponEl) { var ct = couponEl.innerText||''; var pctM = ct.match(/(\d+)%/); if (pctM) coupon=pctM[1]+'% off'; else coupon='有优惠券'; }
    var prime_discount = '未开启';
    return JSON.stringify({title:title, price:price, rating:rating, review_count:review_count,
        brand:brand, main_image:mainImg, bsr:bsr, bsr_subrank:bsrSubRank,
        bsr_subcategory:bsrSubCategory, badges:badges, deal_activity:deal_activity,
        coupon:coupon, prime_discount:prime_discount,
        snapshot_time:new Date().toISOString()});
})()
"""

def parse_plugin_texts(texts_dict):
    """用 Python regex 解析插件 DOM 文本（修复了所有提取 bug）"""
    metrics_text = texts_dict.get('seller-sprite-extension-quick-view-listing-page', '')
    main_text   = texts_dict.get('seller-sprite-extension-quick-view-listing', '')
    traffic_text = texts_dict.get('seller-sprite-extension-main-relation', '')
    inv_text    = texts_dict.get('sellersprite-extension-inventory', '')

    combined = (metrics_text + ' ' + main_text).replace('\n', ' ')
    data = {}

    v = re.search(r'v([\d.]+)', metrics_text)
    if v: data['plugin_version'] = v.group(1)
    lqs = re.search(r'质量得分([\d.]+)', metrics_text)
    if lqs: data['lqs'] = lqs.group(1)

    sales = re.search(r'近30天销量[^)]*\(父体\)\s*([\d,]+)', combined)
    if sales: data['sales_30d_parent'] = sales.group(1).replace(',', '')
    sales_child = re.search(r'近30天销量[^)]*\(子体\)\s*([\d,]+)', combined)
    if sales_child: data['sales_30d_child'] = sales_child.group(1).replace(',', '')

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

    # 上架时间
    launch = re.search(r'(\d{4}-\d{2}-\d{2})\((\d+)天)', combined)
    if launch:
        data['launch_date'] = launch.group(1)
        data['days_online'] = launch.group(3)

    # 毛利率
    profit = re.search(r'毛利率[^:\d]*([\d.]+%|[N/n]\s*/\s*[A/a])', combined)
    if profit: data['gross_margin'] = profit.group(1).replace(' ', '')

    asin_m = re.search(r'ASIN[:：]*(B[A-Z0-9]{9,10})', combined)
    if asin_m: data['asin'] = asin_m.group(1)

    brand = re.search(r'品牌[:：]*([A-Za-z][^\s：:]{3,30}(?:\s+[A-Za-z][^\s：:]{2,20})?)', combined)
    if brand:
        b = brand.group(1).strip()
        b = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', b)
        data['brand'] = b

    seller = re.search(r'卖家[:：]*([A-Za-z][^\s配送：:]{2,30})', combined)
    if seller: data['seller'] = seller.group(1).strip()

    fulfill = re.search(r'配送[:：]*\s*([A-Z]{2,6}(?![A-Za-z\u4e00-\u9fff]))', combined)
    if fulfill: data['fulfillment'] = fulfill.group(1).strip()

    sc = re.search(r'卖家[:：]*\s*(\d+)', combined)
    if sc: data['seller_count'] = sc.group(1)

    bsr_main = re.search(r'#(\d+)\s+in\s+([^#\n]{3,40})', combined)
    if bsr_main:
        data['bsr_rank'] = bsr_main.group(1)
        data['bsr_category'] = bsr_main.group(2).strip()

    # 小类BSR：第二个 # 后面
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

    weight = re.search(r'商品重量[:：]*\s*([\d.]+)\s*ounces?\s*\(?([\d.]+)\s*g\)?', combined)
    if weight:
        data['weight_oz'] = weight.group(1)
        data['weight_g'] = weight.group(2)

    dims = re.search(r'商品尺寸[:：]*\s*([\d.]+)\s*x\s*([\d.]+)\s*x\s*([\d.]+)\s*inches?', combined)
    if dims:
        data['dim_l'], data['dim_w'], data['dim_h'] = dims.group(1), dims.group(2), dims.group(3)

    for label, key in [('全部流量词', 'total_keywords'), ('自然搜索词', 'natural_keywords'),
                       ('广告流量词', 'ad_keywords'), ('搜索推荐词', 'suggest_keywords')]:
        m = re.search(rf'{re.escape(label)}[^\d]*(\d+)', combined)
        if m: data[key] = m.group(1)

    inv_stock = re.search(r'剩余库存(\d+)', inv_text)
    inv_price = re.search(r'剩余库存\d+\$([\d.]+)', inv_text)
    if inv_stock: data['inv_stock'] = inv_stock.group(1)
    if inv_price: data['inv_price'] = inv_price.group(1)

    # 流量词
    keywords = []
    lines = re.split(r'\s{2,}', traffic_text)
    for line in lines:
        line = line.strip()
        if not line or any(k in line for k in ['主要流量词', '收起', '点击查看', '流量词流量占比', '自然排名', '广告排名']):
            continue
        m = re.match(r'^([a-zA-Z\s\-\']+?)\s*([\d.]+%)\s*([^\s]+)\s*(第[^\s]+|前\d+页|无排名)?', line)
        if m and m.group(1).strip() and m.group(2):
            keywords.append({
                'keyword': m.group(1).strip(),
                'traffic_pct': m.group(2),
                'type': m.group(3),
                'ranking': m.group(4) or '',
            })
    if keywords:
        data['traffic_keywords_top'] = keywords

    return data


def print_results(amazon_data, plugin_data):
    print("\n" + "="*60)
    print("监控结果")
    print("="*60)
    print(f"ASIN: {amazon_data.get('asin', 'N/A') or plugin_data.get('asin', 'N/A')}")
    print(f"标题: {(amazon_data.get('title') or plugin_data.get('title', 'N/A'))[:80]}")
    price_a = amazon_data.get('price', '')
    price_s = plugin_data.get('price', '')
    print(f"价格: 亚马逊 {price_a} / 插件 {price_s}")
    rating_a = amazon_data.get('rating', '')
    rating_s = plugin_data.get('rating', '')
    print(f"评分: 亚马逊 {rating_a} / 插件 {rating_s}")
    reviews_a = amazon_data.get('review_count', '')
    reviews_s = plugin_data.get('review_count', '')
    print(f"评论: 亚马逊 {reviews_a} / 插件 {reviews_s}")
    brand_a = amazon_data.get('brand', '')
    brand_s = plugin_data.get('brand', '')
    print(f"品牌: 亚马逊 {brand_a} / 插件 {brand_s}")
    bsr_rank_a = amazon_data.get('bsr_subrank', '')
    bsr_cat_a = amazon_data.get('bsr_subcategory', '')[:40]
    bsr_rank_s = plugin_data.get('bsr_sub_rank', '')
    bsr_cat_s = plugin_data.get('bsr_sub_category', '')[:40]
    print(f"BSR:  亚马逊 #{bsr_rank_a} {bsr_cat_a}")
    print(f"       插件 #{bsr_rank_s} {bsr_cat_s}")
    print()
    print("── 卖家精灵插件数据 ──")
    print(f"插件版本: {plugin_data.get('plugin_version', 'N/A')} | LQS: {plugin_data.get('lqs', 'N/A')}")
    print(f"近30天销量(父体): {plugin_data.get('sales_30d_parent', 'N/A')} | (子体): {plugin_data.get('sales_30d_child', 'N/A')}")
    print(f"销售额: ${plugin_data.get('revenue_30d', 'N/A')} | 均价: ${plugin_data.get('avg_price', 'N/A')}")
    print(f"BSR: {plugin_data.get('bsr', 'N/A')} | FBA费用: ${plugin_data.get('fba_fee', 'N/A')} | 变体数: {plugin_data.get('variant_count', 'N/A')}")
    print(f"上架时间: {plugin_data.get('launch_date', 'N/A')} ({plugin_data.get('days_online', 'N/A')}天)")
    print(f"毛利率: {plugin_data.get('gross_margin', 'N/A')} | 配送: {plugin_data.get('fulfillment', 'N/A')} | 卖家数: {plugin_data.get('seller_count', 'N/A')}")
    print(f"大类BSR: #{plugin_data.get('bsr_rank', 'N/A')} in {plugin_data.get('bsr_category', 'N/A')}")
    print(f"小类BSR: #{plugin_data.get('bsr_sub_rank', 'N/A')} in {plugin_data.get('bsr_sub_category', 'N/A')}")
    print(f"配送时效: {plugin_data.get('ship_days', 'N/A')}天 | Prime: {plugin_data.get('prime_ship_days', 'N/A')}天")
    print(f"商品重量: {plugin_data.get('weight_oz', 'N/A')} oz ({plugin_data.get('weight_g', 'N/A')} g)")
    print(f"商品尺寸: {plugin_data.get('dim_l', 'N/A')} x {plugin_data.get('dim_w', 'N/A')} x {plugin_data.get('dim_h', 'N/A')} inches")
    print(f"关键词统计: 全部{plugin_data.get('total_keywords', 'N/A')} | 自然{plugin_data.get('natural_keywords', 'N/A')} | 广告{plugin_data.get('ad_keywords', 'N/A')} | 推荐{plugin_data.get('suggest_keywords', 'N/A')}")
    print(f"库存: {plugin_data.get('inv_stock', 'N/A')}件 @ ${plugin_data.get('inv_price', 'N/A')}")
    kws = plugin_data.get('traffic_keywords_top', [])
    if kws:
        print(f"流量词Top: {len(kws)}条")
        for kw in kws[:5]:
            print(f"  {kw['keyword']}: {kw['traffic_pct']} ({kw['type']}) {kw['ranking']}")
    print("="*60)


if __name__ == "__main__":
    import urllib.request, json as _json

    # 读取 browser 工具的执行结果
    # 这个脚本由外部调用，browser 工具结果通过环境变量或文件传入
    # 这里做解析演示
    print("用法：通过 openclaw browser 工具调用，然后在 Python 中解析结果")