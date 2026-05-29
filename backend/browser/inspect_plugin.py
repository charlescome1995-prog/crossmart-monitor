#!/usr/bin/env python3
import os, sys, time, json
os.environ["CDP_PORT"] = "9225"
sys.path.insert(0, 'C:/Users/OPENPC/.openclaw/workspace-openpc_ad/crossmart-monitor/backend')

from browser.amazon_browser import CDPBrowser

browser = CDPBrowser()
browser._refresh_tabs()
real_tabs = [(i,t) for i,t in enumerate(browser._raw_tabs) if "amazon.com/s" in t.get("url","") and "view-source" not in t.get("url","")]

if not real_tabs:
    print("No Amazon tab found")
    browser.close()
    sys.exit(1)

browser.connect_tab(tab_index=real_tabs[0][0])
time.sleep(3)

# Extract the correct plugin markers:
# "自然位：第1页第1位" - the pattern is "自然位" followed by "第" later in the text
js = r"""
(function() {
    var items = document.querySelectorAll('.s-result-item[data-component-type="s-search-result"]');
    var results = [];

    for (var i = 0; i < Math.min(items.length, 10); i++) {
        var item = items[i];
        var asinEl = item.querySelector('a[href*="/dp/"]');
        var asin = '';
        if (asinEl && asinEl.href) {
            var m = asinEl.href.match(/\/dp\/([A-Z0-9]{10})/);
            if (m) asin = m[1];
        }
        var title = (item.querySelector('h2') || {}).innerText || '';
        var inner = item.innerText || '';

        // Pattern: "自然位：第1页第1位" -> "自然位" is the marker, "第X页第Y位" is the position
        // Pattern: "广告位" -> ad marker (if present)
        var naturalMatch = inner.match(/自然位[：:](第(\d+)[页页]第(\d+)位)/);
        var adMatch = inner.match(/广告位[：:]?(第(\d+)[页页]第(\d+)位)/);
        var newMatch = inner.match(/新品位[：:]?(第(\d+)[页页]第(\d+)位)/);

        // Also check for standalone "自然位" without page info
        var hasNaturalPos = /自然位/.test(inner);
        var hasAdPos = /广告位/.test(inner);

        // Get all Chinese text fragments for debugging
        var chineseFragments = inner.match(/[\u4e00-\u9fa5]{2,}/g) || [];

        results.push({
            idx: i,
            asin: asin,
            title: title.substring(0, 60),
            naturalMatch: naturalMatch ? naturalMatch[0] : '',
            adMatch: adMatch ? adMatch[0] : '',
            newMatch: newMatch ? newMatch[0] : '',
            hasNaturalPos: hasNaturalPos,
            hasAdPos: hasAdPos,
            chineseFragments: chineseFragments.slice(0, 30)
        });
    }
    return results;
})()
"""
try:
    r = browser.eval(js)
    print("Plugin marker detection:")
    for item in r:
        print("=" + "="*60)
        print(f"Result #{item['idx']} ASIN={item['asin']}")
        print(f"  naturalMatch: {item['naturalMatch']}")
        print(f"  adMatch: {item['adMatch']}")
        print(f"  newMatch: {item['newMatch']}")
        print(f"  hasNaturalPos: {item['hasNaturalPos']}, hasAdPos: {item['hasAdPos']}")
        print(f"  Chinese fragments: {item['chineseFragments']}")
except Exception as e:
    print("JS error:", e)
    import traceback
    traceback.print_exc()

browser.close()