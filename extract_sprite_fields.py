#!/usr/bin/env python3
"""
从卖家精灵插件 DOM 提取所有字段
修复正则提取问题：品牌名截断、评分数合并、流量词分类等
"""
import sys, os, time, json, re
sys.stdout.reconfigure(encoding='utf-8')
_backend = r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend"
sys.path.insert(0, _backend)
from browser.cdp_bridge import CDPBrowser

def parse_sprite_fields(text):
    """从插件文本内容中解析所有字段"""
    data = {}

    # === 指标面板字段 ===
    # 近30天销量(父体)12,736(1,317,315)  ← 父体数值, 子体数值
    sales = re.search(r'近30天销量[^)]*\s*\(?([\d,]+)\s*/\s*\(?([\d,]+)\)', text)
    if sales:
        data['sales_30d_parent'] = sales.group(1).replace(',', '')
        data['sales_30d_child'] = sales.group(2).replace(',', '')

    # Listing销售额 $41,137
    rev = re.search(r'Listing销售额\s+\$([\d,]+)', text)
    if rev:
        data['revenue_30d'] = rev.group(1).replace(',', '')

    # 均价 $7.91
    avg = re.search(r'均价\s+\$([\d.]+)', text)
    if avg:
        data['avg_price'] = avg.group(1)

    # BSR8 (紧跟 BSR 后面是数字)
    bsr = re.search(r'BSR([\d,]+)', text)
    if bsr:
        data['bsr'] = bsr.group(1).replace(',', '')

    # FBA费用 $3.50
    fba = re.search(r'FBA费用\$([\d.]+)', text)
    if fba:
        data['fba_fee'] = fba.group(1)

    # 变体数 2
    variants = re.search(r'变体数(\d+)', text)
    if variants:
        data['variant_count'] = variants.group(1)

    # 上架时间 2022-03-16(1,548天)
    launch = re.search(r'(\d{4}-\d{2}-\d{2})\s*\((\d+)天\)', text)
    if launch:
        data['launch_date'] = launch.group(1)
        data['days_online'] = launch.group(2)

    # 质量得分 7.9
    lqs = re.search(r'质量得分([\d.]+)', text)
    if lqs:
        data['lqs'] = lqs.group(1)

    # === 主面板字段 ===
    # ASIN:B09542G9ZN
    asin_m = re.search(r'ASIN[:：]*(B[A-Z0-9]{9,10})', text)
    if asin_m:
        data['asin'] = asin_m.group(1)

    # 品牌:Amazon Basics (品牌可能多单词，匹配到下一个空格+卖家:)
    brand = re.search(r'品牌[:：]*([^\s：:]+(?:\s+[^\s：:]+)?)', text)
    if brand:
        data['brand'] = brand.group(1).strip()

    # 卖家:Amazon (到配送:为止)
    seller = re.search(r'卖家[:：]*([^\s：:]+)', text)
    if seller:
        data['seller'] = seller.group(1)

    # 配送: AMZ (FBA)
    fulfill = re.search(r'配送[:：]*\s*([^\s：:]+)', text)
    if fulfill:
        data['fulfillment'] = fulfill.group(1)

    # 卖家数: 2
    sc = re.search(r'卖家[:：]*\s*(\d+)', text)
    if sc:
        data['seller_count'] = sc.group(1)

    # #8 in Beauty & Personal Care (大类BSR)
    bsr_main = re.search(r'#(\d+)\s+in\s+([^#\s：:]{3,40})', text)
    if bsr_main:
        data['bsr_rank'] = bsr_main.group(1)
        data['bsr_category'] = bsr_main.group(2).strip()

    # #1 in Cotton Pads & Rounds (小类BSR，第二个 # )
    bsr_sub = re.search(r'#(\d+)\s+in\s+([^#\s：:]{3,40})', text[text.find('#')+1:])
    if bsr_sub:
        data['bsr_sub_rank'] = bsr_sub.group(1)
        data['bsr_sub_category'] = bsr_sub.group(2).strip()

    # 评分(评分数): 4.7(51,083) 或 评分(评分数):4.7(51,083)
    rating_m = re.search(r'评分[^\d]*\(?\s*([\d.]+)\s*\(?([\d,]+)\)?', text)
    if rating_m:
        data['rating'] = rating_m.group(1)
        data['review_count'] = rating_m.group(2).replace(',', '')

    # 价格: $3.23
    price_m = re.search(r'价格[^\d]*\$([\d.]+)', text)
    if price_m:
        data['price'] = price_m.group(1)

    # 配送时长: 5天 / Prime配送时长: 2天
    ship = re.search(r'配送时长[^\d]*(\d+)天', text)
    if ship:
        data['ship_days'] = ship.group(1)
    prime_ship = re.search(r'Prime配送时长[^\d]*(\d+)天', text)
    if prime_ship:
        data['prime_ship_days'] = prime_ship.group(1)

    # 商品重量: 1.76 ounces (49.90 g)
    weight = re.search(r'商品重量[:：]*\s*([\d.]+)\s*ounces?\s*\(?([\d.]+)\s*g\)?', text)
    if weight:
        data['weight_oz'] = weight.group(1)
        data['weight_g'] = weight.group(2)

    # 商品尺寸: 2.3 x 3.7 x 12.8 inches
    dims = re.search(r'商品尺寸[:：]*\s*([\d.]+)\s*x\s*([\d.]+)\s*x\s*([\d.]+)\s*inches?', text)
    if dims:
        data['dim_l'] = dims.group(1)
        data['dim_w'] = dims.group(2)
        data['dim_h'] = dims.group(3)

    # 全部流量词:947 / 自然搜索词:810 / 广告流量词:162 / 搜索推荐词:226
    total_kw = re.search(r'全部流量词[^\d]*(\d+)', text)
    if total_kw:
        data['total_keywords'] = total_kw.group(1)
    natural_kw = re.search(r'自然搜索词[^\d]*(\d+)', text)
    if natural_kw:
        data['natural_keywords'] = natural_kw.group(1)
    ad_kw = re.search(r'广告流量词[^\d]*(\d+)', text)
    if ad_kw:
        data['ad_keywords'] = ad_kw.group(1)
    suggest_kw = re.search(r'搜索推荐词[^\d]*(\d+)', text)
    if suggest_kw:
        data['suggest_keywords'] = suggest_kw.group(1)

    # 毛利率: N/A
    profit = re.search(r'毛利率[^\d]*([\d.%N/A]+)', text)
    if profit:
        data['gross_margin'] = profit.group(1)

    return data


def parse_traffic_keywords(text):
    """解析主要流量词面板"""
    keywords = []
    # 切分：流量词|流量占比|类型|自然排名|广告排名
    # 模式: word % type rank / rank
    lines = re.split(r'\s{2,}', text)
    for line in lines:
        line = line.strip()
        if not line or line == '主要流量词' or line.startswith('收起') or line.startswith('点击查看'):
            continue
        # amazon 14.50%主要流量词自然搜索词37第1页,37/48昨日16:47排名前3页无排名
        m = re.match(r'^([a-zA-Z\s\-\']+?)\s*([\d.]+%)\s*([^\s]+)\s*(第\S+|前\d+页|无排名)?\s*(?:,([^,]+))?', line)
        if not m:
            continue
        kw = m.group(1).strip()
        pct = m.group(2)
        kw_type = m.group(3)
        rank1 = m.group(4) or ''
        rank2 = m.group(5) or ''
        if kw and pct:
            keywords.append({
                'keyword': kw,
                'traffic_pct': pct,
                'type': kw_type,
                'natural_rank': rank1,
                'ad_rank': rank2
            })
    return keywords


# === 主程序 ===
browser = CDPBrowser()
browser.connect_tab(tab_url_filter="about:blank")
if not browser.tab:
    browser.cmd("Target.createTarget", {"url": "about:blank"})
    time.sleep(1)
    browser.connect_tab(tab_url_filter="about:blank")

TEST_ASIN = "B09542G9ZN"
browser.navigate("https://www.amazon.com/dp/" + TEST_ASIN, wait_min=3, wait_max=6)

for i in range(20):
    time.sleep(1)
    r = browser.eval('(function(){var el=document.querySelector("#productTitle");return el&&el.textContent.trim()?{ok:true}:{ok:false};})()')
    if r and r.get('ok'):
        print("Page ready ({}s)".format(i+1))
        break

time.sleep(5)

result = browser.eval("""
(function(){
    var data = {};
    var ids = [
        'seller-sprite-extension-quick-view-listing-page',
        'seller-sprite-extension-quick-view-listing',
        'seller-sprite-extension-main-relation',
        'sellersprite-extension-inventory'
    ];
    for (var i = 0; i < ids.length; i++) {
        var el = document.getElementById(ids[i]);
        if (el) data[ids[i]] = (el.textContent||'').trim();
    }
    return JSON.stringify(data);
})()
""")

if not result:
    print("ERROR: 无返回")
    browser.close()
    sys.exit(1)

data = json.loads(result)

print("="*60)
print("指标面板文本:")
print(data.get('seller-sprite-extension-quick-view-listing-page',''))
print()
print("="*60)
print("主面板文本:")
print(data.get('seller-sprite-extension-quick-view-listing',''))
print()
print("="*60)
print("流量词面板文本:")
print(data.get('seller-sprite-extension-main-relation',''))

# 解析
metrics_text = data.get('seller-sprite-extension-quick-view-listing-page', '')
main_text = data.get('seller-sprite-extension-quick-view-listing', '')
traffic_text = data.get('seller-sprite-extension-main-relation', '')
inv_text = data.get('sellersprite-extension-inventory', '')

# 合并两个面板的文本一起解析（字段可能跨面板）
combined = metrics_text + ' ' + main_text

fields = parse_sprite_fields(combined)
fields['inventory_text'] = inv_text

# 解析流量词
fields['traffic_keywords'] = parse_traffic_keywords(traffic_text)

print("\n" + "="*60)
print("提取结果:")
print("="*60)
for k, v in fields.items():
    if k == 'traffic_keywords':
        print("\n流量词列表:")
        for kw in v:
            print("  {} | {}% | {} | 自然:{} | 广告:{}".format(
                kw['keyword'], kw['traffic_pct'], kw['type'],
                kw['natural_rank'], kw['ad_rank']))
    else:
        print("  {}: {}".format(k, v))

browser.close()
print("\n完成")