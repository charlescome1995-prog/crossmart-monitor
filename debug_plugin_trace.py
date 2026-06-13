"""Debug: trace what's happening in extract_plugin_data"""
import sys, os, json, re
sys.path.insert(0, r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend")
sys.stdout.reconfigure(encoding='utf-8')
from browser.cdp_bridge import CDPBrowser
import browser.cdp_bridge as cdp
cdp.EDGE_PORT = 9225
cdp._USER_SET_PORT = 9225

browser = CDPBrowser()
browser.connect_tab(tab_url_filter="B09542G9ZN")

# Simulate exactly what asin_monitor.py does
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
raw = browser.eval(js_get_plugin_text)
print(f"Type of raw: {type(raw)}")
print(f"Raw is None: {raw is None}")
print(f"Raw is str: {isinstance(raw, str)}")

if isinstance(raw, str):
    try:
        plugin_texts = json.loads(raw)
        print(f"JSON parsed OK, keys: {list(plugin_texts.keys())}")
    except Exception as e:
        print(f"JSON parse error: {e}")
        print(f"Raw (first 200): {repr(raw[:200])}")
elif isinstance(raw, dict):
    print(f"Raw is dict (not JSON string), keys: {list(raw.keys())}")
    plugin_texts = raw
else:
    print(f"Raw type: {type(raw)}")
    plugin_texts = {}

traffic_text = plugin_texts.get('seller-sprite-extension-main-relation', '')
print(f"\ntraffic_text type: {type(traffic_text)}")
print(f"traffic_text is None: {traffic_text is None}")
print(f"traffic_text length: {len(traffic_text) if traffic_text else 0}")

if traffic_text:
    tds = re.findall(r'<td[^>]*>(.*?)</td>', traffic_text, re.DOTALL)
    print(f"TDs found: {len(tds)}")
    cell_texts = []
    for td in tds:
        raw_td = re.sub(r'<[^>]*>', '', td)
        lines = [l.strip() for l in raw_td.split('\n') if l.strip()]
        cell_texts.append('\n'.join(lines))
    print(f"cell_texts count: {len(cell_texts)}")
    for i, ct in enumerate(cell_texts[:6]):
        print(f"  [{i}] {repr(ct[:60])}")
else:
    print("traffic_text is empty!")

browser.close()