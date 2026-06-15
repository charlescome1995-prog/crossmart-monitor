#!/usr/bin/env python3
import sys, os, time, json
sys.stdout.reconfigure(encoding='utf-8')
_backend = r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend"
sys.path.insert(0, _backend)
from browser.cdp_bridge import CDPBrowser

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

# 直接 eval 提取所有结构化数据
result = browser.eval("""
(function(){
    var data = {};

    // === 指标面板 (quick-view-listing-page) ===
    var metricsPanel = document.getElementById('seller-sprite-extension-quick-view-listing-page');
    if (metricsPanel) {
        var text = metricsPanel.textContent || '';
        data.metrics_text = text;
        data.metrics = {};
        var vM = text.match(/v([\\d.]+)/);
        var sM = text.match(/质量得分([\\d.]+)/);
        var salesM = text.match(/近30天销量[^\\(]*\\(?([\\d,]+)/);
        var revM = text.match(/Listing销售额\\s+\\$([\\d,]+)/);
        var avgM = text.match(/均价\\s+\\$([\\d.]+)/);
        var bsrM = text.match(/BSR[^\\d]*([\\d,]+)/);
        if (vM) data.metrics.plugin_version = vM[1];
        if (sM) data.metrics.quality_score = sM[1];
        if (salesM) data.metrics.sales_30d = salesM[1];
        if (revM) data.metrics.revenue_30d = revM[1];
        if (avgM) data.metrics.avg_price = avgM[1];
        if (bsrM) data.metrics.bsr = bsrM[1];
    }

    // === 主面板 (quick-view-listing) ===
    var mainPanel = document.getElementById('seller-sprite-extension-quick-view-listing');
    if (mainPanel) {
        var text = mainPanel.textContent || '';
        data.main_text = text;
        data.main = {};
        var asinM = text.match(/ASIN[:：]*(B[A-Z0-9]{9,10})/);
        var brandM = text.match(/品牌[:：]*([^\\s：:]+)/);
        var sellerM = text.match(/卖家[:：]*([^\\s：:]+)/);
        var bsrM = text.match(/#(\\d+)\\s+in\\s+([^\\s：:]{3,30})/);
        var scM = text.match(/卖家[:：]*\\s*(\\d+)/);
        var fbmM = text.match(/配送[:：]*\\s*([^\\s：:]{2,10})/);
        if (asinM) data.main.asin = asinM[1];
        if (brandM) data.main.brand = brandM[1];
        if (sellerM) data.main.seller = sellerM[1];
        if (bsrM) { data.main.bsr_rank = bsrM[1]; data.main.bsr_category = bsrM[2]; }
        if (scM) data.main.seller_count = scM[1];
        if (fbmM) data.main.fulfillment = fbmM[1];
    }

    // === 库存面板 ===
    var invPanel = document.getElementById('sellersprite-extension-inventory');
    if (invPanel) {
        var text = invPanel.textContent || '';
        data.inventory_text = text;
    }

    // === 主要流量词 ===
    var trafficPanel = document.getElementById('seller-sprite-extension-main-relation');
    if (trafficPanel) {
        var text = trafficPanel.textContent || '';
        data.traffic_text = text;
    }

    // === 所有 seller-sprite 文本（完整抓取）===
    var allEls = document.querySelectorAll('[id*="seller-sprite"], [id*="sellersprite"]');
    var allText = [];
    for (var i = 0; i < allEls.length; i++) {
        var t = (allEls[i].textContent || '').trim();
        if (t && t.length > 2) allText.push({id: allEls[i].id, text: t.substring(0, 200)});
    }
    data.all_elements = allText;

    return JSON.stringify(data);
})()
""")

if result:
    data = json.loads(result)
    print("=== 指标面板 ===")
    print(data.get('metrics_text', ''))
    print("\n结构化字段:")
    for k, v in data.get('metrics', {}).items():
        print("  {}: {}".format(k, v))

    print("\n=== 主面板 ===")
    print(data.get('main_text', ''))
    print("\n结构化字段:")
    for k, v in data.get('main', {}).items():
        print("  {}: {}".format(k, v))

    print("\n=== 库存 ===")
    print(data.get('inventory_text', ''))

    print("\n=== 主要流量词 ===")
    print(data.get('traffic_text', ''))

    print("\n=== 所有插件元素 ===")
    for item in data.get('all_elements', []):
        if item['text']:
            print("  {}: {}".format(item['id'], item['text'][:100]))
else:
    print("返回为空")

browser.close()