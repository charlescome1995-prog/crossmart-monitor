#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

metrics_text = 'v5.0.3（数据来源：卖家精灵）质量得分7.9近30天销量(父体)12,736(1,317,315)Listing销售额 $41,137均价 $7.91BSR8FBA费用$3.50变体数2上架时间2022-03-16(1,548天)1688找货源查外观专利变体对比(2)Keepa插件替代流量洞察AI评论分析全站点售卖反查出单词变体流量对比3D展示展开'
main_text = 'ASIN:B09542G9ZN收起 品牌:Amazon Basics卖家:Amazon配送: AMZ卖家: 2加入产品库#8 in Beauty & Personal Care#1 in Cotton Pads & Rounds近30天销量(父体):12,736近30天销量(子体):100,000+销售额:$41,137FBA费用:$3.50毛利率:N/A变体数:2价格:$3.23评分(评分数):4.7(51,083)配送时长:5天Prime配送时长:2天Size: 100 Count (Pack of 1)商品重量:1.76 ounces (49.90 g)商品尺寸:2.3 x 3.7 x 12.8 inches包装重量:0.11 pounds (49.90 g)包装尺寸:11.8 x 3.5 x 2.2 inches  (大号标准尺寸) 上架时间:2022-03-16 (1,548天)全部流量词:947自然搜索词:810广告流量词:162搜索推荐词:226关键词反查广告洞察关联流量市场分析Listing生成器1688找货源Alibaba历史销量产品卖点产品概要优麦云TikTok达人MCP服务 品牌检测 AI评论分析评论下载主图下载评论图片下载关联视频下载卖家精灵'
traffic_text = '主要流量词收起 流量词流量占比流量词类型自然排名广告排名amazon亚马逊14.50%主要流量词自然搜索词37第1页,37/48昨日16:47排名前3页无排名cotton rounds棉轮9.71%主要流量词转化优质词自然搜索词SP广告词AC推荐词4第1页,4/61昨日21:24排名1第1页,1/6406月05日排名qtips技巧9.52%自然搜索词22第1页,22/602天前03:25排名前3页无排名makeup化妆8.78%自然搜索词59第1页,59/67昨日15:41排名前3页无排名点击查看全部流量词'
inv_text = '卖家精灵-库存监控剩余库存27$3.23Amazon27$3.23AmazonFresh100查看详细'

combined = metrics_text + ' ' + main_text
data = {}

# 基础指标
v = re.search(r'v([\d.]+)', metrics_text)
if v: data['plugin_version'] = v.group(1)
lqs = re.search(r'质量得分([\d.]+)', metrics_text)
if lqs: data['lqs'] = lqs.group(1)

# 近30天销量 - 父体/子体
sales = re.search(r'近30天销量[^)]*\s*\(?([\d,]+)\s*/\s*\(?([\d,]+)\)?', combined)
if sales:
    data['sales_30d_parent'] = sales.group(1).replace(',','')
    data['sales_30d_child'] = sales.group(2).replace(',','')

rev = re.search(r'Listing销售额\s+\$([\d,]+)', combined)
if rev: data['revenue_30d'] = rev.group(1).replace(',','')
avg = re.search(r'均价\s+\$([\d.]+)', combined)
if avg: data['avg_price'] = avg.group(1)
bsr = re.search(r'BSR([\d,]+)', combined)
if bsr: data['bsr'] = bsr.group(1).replace(',','')
fba = re.search(r'FBA费用\$([\d.]+)', combined)
if fba: data['fba_fee'] = fba.group(1)
variants = re.search(r'变体数(\d+)', combined)
if variants: data['variant_count'] = variants.group(1)

# 上架时间
launch = re.search(r'(\d{4}-\d{2}-\d{2})\s*\((\d+)天\)', combined)
if launch:
    data['launch_date'] = launch.group(1)
    data['days_online'] = launch.group(2)

# 毛利率 - 修复：支持 N/A 和数字
profit = re.search(r'毛利率[^:\d]*([\d.]+%|[N/n]\s*/\s*[A/a])', combined)
if profit: data['gross_margin'] = profit.group(1).replace('\n','').replace(' ','')

# 主面板
asin_m = re.search(r'ASIN[:：]*(B[A-Z0-9]{9,10})', combined)
if asin_m: data['asin'] = asin_m.group(1)

# 品牌 - Amazon Basics（遇到卖家:截止，清理特殊字符）
brand = re.search(r'品牌[:：]*([A-Za-z][^\s：:]{3,30}(?:\s+[A-Za-z][^\s：:]{2,20})?)', combined)
if brand:
    b = brand.group(1).strip()
    b = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', b)
    data['brand'] = b

# 卖家
seller = re.search(r'卖家[:：]*([A-Za-z][^\s配送：:]{2,30})', combined)
if seller: data['seller'] = seller.group(1).strip()

# 配送类型
fulfill = re.search(r'配送[:：]*\s*([A-Z]{2,10})', combined)
if fulfill: data['fulfillment'] = fulfill.group(1).strip()

# 卖家数
sc = re.search(r'卖家[:：]*\s*(\d+)', combined)
if sc: data['seller_count'] = sc.group(1)

# 大类 BSR
bsr_main = re.search(r'#(\d+)\s+in\s+([^#\n]{3,40})', combined)
if bsr_main:
    data['bsr_rank'] = bsr_main.group(1)
    data['bsr_category'] = bsr_main.group(2).strip()

# 小类 BSR - 用前瞻断言：遇到 # 或 近30天销量 就停止
rest = combined[combined.find('#')+1:]
bsr_sub = re.search(r'#(\d+)\s+in\s+([^#\n]{3,40})(?=\s*#|\s*近30天)', rest)
if bsr_sub:
    data['bsr_sub_rank'] = bsr_sub.group(1)
    data['bsr_sub_category'] = bsr_sub.group(2).strip()

# 评分+评分数
rating_m = re.search(r'评分[^\d]*([\d.]+)\s*\(?([\d,]+)\)?', combined)
if rating_m:
    data['rating'] = rating_m.group(1)
    data['review_count'] = rating_m.group(2).replace(',','')

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
total_kw = re.search(r'全部流量词[^\d]*(\d+)', combined)
if total_kw: data['total_keywords'] = total_kw.group(1)
natural_kw = re.search(r'自然搜索词[^\d]*(\d+)', combined)
if natural_kw: data['natural_keywords'] = natural_kw.group(1)
ad_kw = re.search(r'广告流量词[^\d]*(\d+)', combined)
if ad_kw: data['ad_keywords'] = ad_kw.group(1)
suggest_kw = re.search(r'搜索推荐词[^\d]*(\d+)', combined)
if suggest_kw: data['suggest_keywords'] = suggest_kw.group(1)

# 库存
inv_stock = re.search(r'剩余库存(\d+)', inv_text)
inv_price = re.search(r'剩余库存\d+\$([\d.]+)', inv_text)
if inv_stock: data['inv_stock'] = inv_stock.group(1)
if inv_price: data['inv_price'] = inv_price.group(1)

# 流量词解析
keywords = []
lines = re.split(r'\s{2,}', traffic_text)
for line in lines:
    line = line.strip()
    if not line or '主要流量词' in line or '收起' in line or '点击查看' in line:
        continue
    m = re.match(r'^([a-zA-Z\s\-\']+?)\s*([\d.]+%)\s*([^\s]+)\s*(第[^\s]+|前\d+页|无排名)?', line)
    if m:
        kw = m.group(1).strip()
        pct = m.group(2)
        kw_type = m.group(3)
        rank = m.group(4) or ''
        if kw and pct:
            keywords.append({'keyword': kw, 'traffic_pct': pct, 'type': kw_type, 'ranking': rank})

data['traffic_keywords'] = keywords

print('=== 结构化字段 ===')
for k, v in sorted(data.items()):
    if k != 'traffic_keywords':
        print(f'  {k}: {v}')
print()
print('=== 流量词 ===')
for kw in keywords:
    print(f'  {kw}')