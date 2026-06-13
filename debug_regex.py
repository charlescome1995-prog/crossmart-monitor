#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

metrics_text = 'v5.0.3（数据来源：卖家精灵）质量得分7.9近30天销量(父体)12,736(1,317,315)Listing销售额 $41,137均价 $7.91BSR8FBA费用$3.50变体数2上架时间2022-03-16(1,548天)1688找货源查外观专利变体对比(2)Keepa插件替代流量洞察AI评论分析全站点售卖反查出单词变体流量对比3D展示展开'
main_text = 'ASIN:B09542G9ZN收起 品牌:Amazon Basics卖家:Amazon配送: AMZ卖家: 2加入产品库#8 in Beauty & Personal Care#1 in Cotton Pads & Rounds近30天销量(父体):12,736近30天销量(子体):100,000+销售额:$41,137FBA费用:$3.50毛利率:N/A变体数:2价格:$3.23评分(评分数):4.7(51,083)配送时长:5天Prime配送时长:2天Size: 100 Count (Pack of 1)商品重量:1.76 ounces (49.90 g)商品尺寸:2.3 x 3.7 x 12.8 inches包装重量:0.11 pounds (49.90 g)包装尺寸:11.8 x 3.5 x 2.2 inches  (大号标准尺寸) 上架时间:2022-03-16 (1,548天)全部流量词:947自然搜索词:810广告流量词:162搜索推荐词:226关键词反查广告洞察关联流量市场分析Listing生成器1688找货源Alibaba历史销量产品卖点产品概要优麦云TikTok达人MCP服务 品牌检测 AI评论分析评论下载主图下载评论图片下载关联视频下载卖家精灵'
traffic_text = '主要流量词收起 流量词流量占比流量词类型自然排名广告排名amazon亚马逊14.50%主要流量词自然搜索词37第1页,37/48昨日16:47排名前3页无排名cotton rounds棉轮9.71%主要流量词转化优质词自然搜索词SP广告词AC推荐词4第1页,4/61昨日21:24排名1第1页,1/6406月05日排名qtips技巧9.52%自然搜索词22第1页,22/602天前03:25排名前3页无排名makeup化妆8.78%自然搜索词59第1页,59/67昨日15:41排名前3页无排名点击查看全部流量词'
inv_text = '卖家精灵-库存监控剩余库存27$3.23Amazon27$3.23AmazonFresh100查看详细'

combined = metrics_text + ' ' + main_text

print("=== 调试各字段 ===")
print()

# days_online
print("--- days_online ---")
launch_all = re.findall(r'(\d{4}-\d{2}-\d{2})\s*\((\d+)天\)', combined)
print("所有日期对:", launch_all)

# bsr_category (第一个)
print("\n--- bsr_category ---")
idx1 = combined.find('#')
print("第一个#位置:", idx1, "内容:", combined[idx1:idx1+30])
m = re.search(r'#(\d+)\s+in\s+([^#\n]{3,40})', combined)
if m:
    print("第一个BSR match:", m.group(1), m.group(2))

idx2 = combined.find('#', idx1+1)
print("第二个#位置:", idx2, "内容:", combined[idx2:idx2+30])
rest = combined[idx2:]
m2 = re.search(r'#(\d+)\s+in\s+([^#\n]{3,40})', rest)
if m2:
    print("第二个BSR match:", m2.group(1), m2.group(2)[:50])

# 品牌
print("\n--- brand ---")
# 找"品牌:" 到 "卖家:" 之间的内容
brand_m = re.search(r'品牌[:：]*([^\s：:]{3,30})', combined)
print("品牌 match:", brand_m.group(1) if brand_m else None)

# 用更精确的：品牌:Amazon Basics卖家
brand_m2 = re.search(r'品牌[:：]*([A-Za-z\s]+ Basics)', combined)
if brand_m2:
    print("品牌 match2:", brand_m2.group(1))

# 卖家
print("\n--- seller ---")
seller_m = re.search(r'卖家[:：]*([A-Za-z][^\s配送：:]{2,30})', combined)
if seller_m:
    print("卖家 match:", seller_m.group(1))

# fulfillment
print("\n--- fulfillment ---")
fulfill_m = re.search(r'配送[:：]*\s*([A-Z]{2,10}\s*卖家)?', combined)
if fulfill_m:
    print("配送 match:", fulfill_m.group(1))
fulfill_m2 = re.search(r'配送[:：]*\s*([A-Z]{3,15})', combined)
if fulfill_m2:
    print("配送 match2:", fulfill_m2.group(1))

# gross_margin
print("\n--- gross_margin ---")
profit_all = re.findall(r'毛利率[^\d]*([\d.%N/A]+)', combined)
print("毛利率 all matches:", profit_all)

# seller_count
print("\n--- seller_count ---")
sc_all = re.findall(r'卖家[:：]*\s*(\d+)', combined)
print("卖家数 all matches:", sc_all)

print("\n=== 完成 ===")