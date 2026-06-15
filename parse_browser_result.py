#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

raw = r'''{"plugin":{"seller-sprite-extension-quick-view-listing-page":"v5.0.3（数据来源：卖家精灵）质量得分7.9近30天销量(父体)12,736(1,317,315)Listing销售额 $41,137均价 $7.91BSR8FBA费用$3.50变体数2上架时间2022-03-16(1,548天)1688找货源查外观专利变体对比(2)Keepa插件替代流量洞察AI评论分析全站点售卖反查出单词变体流量对比3D展示展开","seller-sprite-extension-quick-view-listing":"ASIN:B09542G9ZN收起 品牌:Amazon Basics卖家:Amazon配送: AMZ卖家: 2加入产品库#8 in Beauty & Personal Care#1 in Cotton Pads & Rounds近30天销量(父体):12,736近30天销量(子体):100,000+销售额:$41,137FBA费用:$3.50毛利率:N/A变体数:2价格:$3.23评分(评分数):4.7(51,083)配送时长:5天Prime配送时长:2天Size: 100 Count (Pack of 1)商品重量:1.76 ounces (49.90 g)商品尺寸:2.3 x 3.7 x 12.8 inches包装重量:0.11 pounds (49.90 g)包装尺寸:11.8 x 3.5 x 2.2 inches  (大号标准尺寸) 上架时间:2022-03-16 (1,548天)全部流量词:947自然搜索词:810广告流量词:162搜索推荐词:226关键词反查广告洞察关联流量市场分析Listing生成器1688找货源Alibaba历史销量产品卖点产品概要优麦云TikTok达人MCP服务 品牌检测 AI评论分析评论下载主图下载评论图片下载关联视频下载卖家精灵","seller-sprite-extension-main-relation":"主要流量词收起 流量词流量占比流量词类型自然排名广告排名amazon亚马逊14.50%主要流量词自然搜索词37第1页,37/48昨日16:47排名前3页无排名cotton rounds棉轮9.71%主要流量词转化优质词自然搜索词SP广告词AC推荐词4第1页,4/61昨日21:24排名1第1页,1/6406月05日排名qtips技巧9.52%自然搜索词22第1页,22/602天前03:25排名前3页无排名makeup化妆8.78%自然搜索词59第1页,59/67昨日15:41排名前3页无排名点击查看全部流量词","sellersprite-extension-inventory":"卖家精灵-库存监控剩余库存27$3.23Amazon27$3.23AmazonFresh100查看详细"},"amazon":{"title":"Amazon Basics Hypoallergenic Cotton Rounds for Makeup Removal and Skincare, 100 Count, 1 Pack","price":"$3.23","rating":"4.7","review_count":"51083","brand":"Amazon Basics","main_image":"https://m.media-amazon.com/images/I/41roS4Ps5RL._SY879_.jpg","bsr_subrank":"8","bsr_subcategory":"Beauty & Personal Care (See Top 100 in Beauty & Personal Care)","badges":["AC","NR"],"deal_activity":"无","coupon":"无","snapshot_time":"2026-06-11T02:18:10.919Z"}}
'''

data = json.loads(raw)
plugin_texts = data['plugin']
amazon_data = data['amazon']

metrics_text = plugin_texts.get('seller-sprite-extension-quick-view-listing-page', '')
main_text   = plugin_texts.get('seller-sprite-extension-quick-view-listing', '')
traffic_text = plugin_texts.get('seller-sprite-extension-main-relation', '')
inv_text    = plugin_texts.get('sellersprite-extension-inventory', '')

combined = (metrics_text + ' ' + main_text).replace('\n', ' ')
pdata = {}

v = re.search(r'v([\d.]+)', metrics_text)
if v: pdata['plugin_version'] = v.group(1)
lqs = re.search(r'质量得分([\d.]+)', metrics_text)
if lqs: pdata['lqs'] = lqs.group(1)

# 近30天销量 - 父体（直接在 "近30天销量(父体)" 之后匹配数字）
sales = re.search(r'近30天销量\(父体\)\s*([\d,]+)', combined)
if sales: pdata['sales_30d_parent'] = sales.group(1).replace(',', '')
# 子体（直接在 "近30天销量(子体)" 之后匹配数字）
sales_child = re.search(r'近30天销量\(子体\)\s*([\d,]+)', combined)
if sales_child: pdata['sales_30d_child'] = sales_child.group(1).replace(',', '')

rev = re.search(r'Listing销售额\s+\$([\d,]+)', combined)
if rev: pdata['revenue_30d'] = rev.group(1).replace(',', '')
avg = re.search(r'均价\s+\$([\d.]+)', combined)
if avg: pdata['avg_price'] = avg.group(1)
bsr = re.search(r'BSR([\d,]+)', combined)
if bsr: pdata['bsr'] = bsr.group(1).replace(',', '')
fba = re.search(r'FBA费用\$([\d.]+)', combined)
if fba: pdata['fba_fee'] = fba.group(1)
variants = re.search(r'变体数(\d+)', combined)
if variants: pdata['variant_count'] = variants.group(1)

# 上架时间：格式 "上架时间2022-03-16(1,548天)" —— 注意 label 和日期之间没有空格
launch = re.search(r'上架时间\s*(\d{4}-\d{2}-\d{2})\s*\((\d+)天\)', combined)
if launch:
    pdata['launch_date'] = launch.group(1)
    pdata['days_online'] = launch.group(2)

# 毛利率：格式 "毛利率:N/A" 或 "毛利率:12.5%"
profit = re.search(r'毛利率[:：]*\s*([\d.]+%|[N/n]\s*/\s*[A/a])', combined)
if profit: pdata['gross_margin'] = profit.group(1).replace(' ', '')

asin_m = re.search(r'ASIN[:：]*(B[A-Z0-9]{9,10})', combined)
if asin_m: pdata['asin'] = asin_m.group(1)

brand = re.search(r'品牌[:：]*([A-Za-z][^\s：:]{3,30}(?:\s+[A-Za-z][^\s：:]{2,20})?)', combined)
if brand:
    b = brand.group(1).strip()
    b = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', b)
    pdata['brand'] = b

seller = re.search(r'卖家[:：]*([A-Za-z][^\s配送：:]{2,30})', combined)
if seller: pdata['seller'] = seller.group(1).strip()

# 配送类型：AMZ（在"配送: AMZ卖家:"格式中）
fulfill = re.search(r'配送[:：]*\s*([A-Z]{2,6})(?=\s*卖家)', combined)
if fulfill: pdata['fulfillment'] = fulfill.group(1).strip()

sc = re.search(r'卖家[:：]*\s*(\d+)', combined)
if sc: pdata['seller_count'] = sc.group(1)

bsr_main = re.search(r'#(\d+)\s+in\s+([^#\n]{3,40})', combined)
if bsr_main:
    pdata['bsr_rank'] = bsr_main.group(1)
    pdata['bsr_category'] = bsr_main.group(2).strip()

idx1 = combined.find('#')
if idx1 >= 0:
    rest = combined[idx1 + 1:]
    idx2 = rest.find('#')
    if idx2 >= 0:
        segment = rest[idx2:]
        bsr_sub = re.search(r'#(\d+)\s+in\s+(.{3,40}?)(?=\s*#|\s*近30天)', segment)
        if bsr_sub:
            pdata['bsr_sub_rank'] = bsr_sub.group(1)
            pdata['bsr_sub_category'] = bsr_sub.group(2).strip()

rating_m = re.search(r'评分[^\d]*([\d.]+)\s*\(?([\d,]+)\)?', combined)
if rating_m:
    pdata['rating'] = rating_m.group(1)
    pdata['review_count'] = rating_m.group(2).replace(',', '')
price_m = re.search(r'价格[^\d]*\$([\d.]+)', combined)
if price_m: pdata['price'] = price_m.group(1)
ship = re.search(r'配送时长[^\d]*(\d+)天', combined)
if ship: pdata['ship_days'] = ship.group(1)
prime = re.search(r'Prime配送时长[^\d]*(\d+)天', combined)
if prime: pdata['prime_ship_days'] = prime.group(1)

weight = re.search(r'商品重量[:：]*\s*([\d.]+)\s*ounces?\s*\(?([\d.]+)\s*g\)?', combined)
if weight:
    pdata['weight_oz'] = weight.group(1)
    pdata['weight_g'] = weight.group(2)

dims = re.search(r'商品尺寸[:：]*\s*([\d.]+)\s*x\s*([\d.]+)\s*x\s*([\d.]+)\s*inches?', combined)
if dims:
    pdata['dim_l'], pdata['dim_w'], pdata['dim_h'] = dims.group(1), dims.group(2), dims.group(3)

for label, key in [('全部流量词', 'total_keywords'), ('自然搜索词', 'natural_keywords'),
                   ('广告流量词', 'ad_keywords'), ('搜索推荐词', 'suggest_keywords')]:
    m = re.search(rf'{re.escape(label)}[^\d]*(\d+)', combined)
    if m: pdata[key] = m.group(1)

inv_stock = re.search(r'剩余库存(\d+)', inv_text)
inv_price = re.search(r'剩余库存\d+\$([\d.]+)', inv_text)
if inv_stock: pdata['inv_stock'] = inv_stock.group(1)
if inv_price: pdata['inv_price'] = inv_price.group(1)

# 流量词解析（流量词面板文本以多空格拆分）
keywords = []
lines = re.split(r'\s{2,}', traffic_text)
for line in lines:
    line = line.strip()
    # 跳过标题行和干扰行
    if not line:
        continue
    skip_words = ['主要流量词', '收起', '点击查看', '流量词流量占比', '自然排名',
                  '广告排名', '流量词', '类型', '自然', '广告', '排名', '占比']
    if any(k in line for k in skip_words) and not re.search(r'[\d.]+%', line):
        continue
    # 匹配: 关键词 + 百分比 + 类型词 + 排名
    m = re.match(r'^([a-zA-Z\s\-\']+?)\s*([\d.]+%)\s*([^\s]+)\s*(第[^\s]+|前\d+页|无排名)?', line)
    if m and m.group(1).strip() and m.group(2):
        kw_text = m.group(1).strip()
        # 过滤纯中文行
        if re.match(r'^[\u4e00-\u9fff]+$', kw_text):
            continue
        keywords.append({
            'keyword': kw_text,
            'traffic_pct': m.group(2),
            'type': m.group(3),
            'ranking': m.group(4) or '',
        })
if keywords:
    pdata['traffic_keywords_top'] = keywords

# 打印结果
print("=" * 65)
print("亚马逊前台数据（browser 工具）")
print("=" * 65)
print(f"  标题:     {amazon_data['title'][:70]}")
print(f"  价格:     {amazon_data['price']}")
print(f"  评分:     {amazon_data['rating']}")
print(f"  评论数:   {amazon_data['review_count']}")
print(f"  品牌:     {amazon_data['brand']}")
print(f"  BSR:      #{amazon_data['bsr_subrank']} in {amazon_data['bsr_subcategory'][:40]}")
print(f"  徽章:     {amazon_data['badges']}")
print()
print("=" * 65)
print("卖家精灵插件数据")
print("=" * 65)
print(f"  插件版本:      {pdata.get('plugin_version','N/A')} | LQS: {pdata.get('lqs','N/A')}")
print(f"  近30天销量(父): {pdata.get('sales_30d_parent','N/A')} | (子): {pdata.get('sales_30d_child','N/A')}")
print(f"  销售额:         ${pdata.get('revenue_30d','N/A')} | 均价: ${pdata.get('avg_price','N/A')}")
print(f"  BSR:            #{pdata.get('bsr','N/A')} | FBA费用: ${pdata.get('fba_fee','N/A')} | 变体: {pdata.get('variant_count','N/A')}")
print(f"  上架时间:       {pdata.get('launch_date','N/A')} ({pdata.get('days_online','N/A')}天)")
print(f"  毛利率:         {pdata.get('gross_margin','N/A')} | 配送: {pdata.get('fulfillment','N/A')} | 卖家数: {pdata.get('seller_count','N/A')}")
print(f"  大类BSR:        #{pdata.get('bsr_rank','N/A')} in {pdata.get('bsr_category','N/A')}")
print(f"  小类BSR:        #{pdata.get('bsr_sub_rank','N/A')} in {pdata.get('bsr_sub_category','N/A')}")
print(f"  评分:           {pdata.get('rating','N/A')} | 评论数: {pdata.get('review_count','N/A')}")
print(f"  价格:           ${pdata.get('price','N/A')}")
print(f"  配送时效:        {pdata.get('ship_days','N/A')}天 | Prime: {pdata.get('prime_ship_days','N/A')}天")
print(f"  商品重量:        {pdata.get('weight_oz','N/A')} oz ({pdata.get('weight_g','N/A')} g)")
print(f"  商品尺寸:        {pdata.get('dim_l','N/A')} x {pdata.get('dim_w','N/A')} x {pdata.get('dim_h','N/A')} in")
print(f"  关键词: 全部:{pdata.get('total_keywords','N/A')} 自然:{pdata.get('natural_keywords','N/A')} 广告:{pdata.get('ad_keywords','N/A')} 推荐:{pdata.get('suggest_keywords','N/A')}")
print(f"  库存:           {pdata.get('inv_stock','N/A')}件 @ ${pdata.get('inv_price','N/A')}")
kws = pdata.get('traffic_keywords_top', [])
print(f"\n  流量词 Top ({len(kws)}条):")
for kw in kws:
    print(f"    {kw['keyword']}: {kw['traffic_pct']} ({kw['type']}) {kw['ranking']}")
print("=" * 65)