import sys, os
sys.path.insert(0, r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend")
sys.stdout.reconfigure(encoding='utf-8')
from browser.cdp_bridge import CDPBrowser
import browser.cdp_bridge as cdp
cdp.EDGE_PORT = 9225
cdp._USER_SET_PORT = 9225

browser = CDPBrowser()
browser.connect_tab(tab_url_filter="B09542G9ZN")

# Get the full plugin text as asin_monitor.py would
js = """
(function(){
    var ids = [
        'seller-sprite-extension-main-relation',
        'seller-sprite-extension-keyword',
        'seller-sprite-extension-traffic',
        'seller-sprite-extension-quick-view-listing-page',
        'seller-sprite-extension-quick-view-listing'
    ];
    var data = {};
    for (var i = 0; i < ids.length; i++) {
        var el = document.getElementById(ids[i]);
        if (el) data[ids[i]] = (el.textContent||'').trim();
    }
    return JSON.stringify(data);
})()
"""
r = browser.eval(js)
import json
plugin_texts = json.loads(r) if isinstance(r, str) else r
traffic_text = plugin_texts.get('seller-sprite-extension-main-relation', '')
print(f"traffic_text length: {len(traffic_text)}")
print(f"traffic_text repr: {repr(traffic_text[:500])}")

# Simulate the asin_monitor extraction
import re
def _extract_kw(text, utf8_bytes, pct_char_pos):
    pct_byte = len(text[:pct_char_pos].encode('utf-8'))
    j = pct_byte - 1
    while j >= 0 and utf8_bytes[j] > 32:
        j -= 1
    kw_bytes = utf8_bytes[j+1:pct_byte-len(str(re.search(r'\d+\.\d+%', text).group()))]
    return kw_bytes.decode('utf-8', errors='replace').strip()

TYPE_WORDS = ['Highly searched', 'High-conv', 'High-conv term', 'SP ad words', 'Low-search']
utf8_traffic = traffic_text.encode('utf-8')
pct_positions = [(m.start(), m.group()) for m in re.finditer(r'\d+\.\d+%', traffic_text)]
print(f"\npct_positions: {pct_positions}")
keywords = []
for i, (pct_pos, pct) in enumerate(pct_positions):
    kw = _extract_kw(traffic_text, utf8_traffic, pct_pos)
    after_start = pct_pos + len(pct)
    after_end = pct_positions[i+1][0] if i+1 < len(pct_positions) else len(traffic_text)
    metadata = traffic_text[after_start:after_end]
    kw_type = next((tw for tw in TYPE_WORDS if tw in metadata), '')
    print(f"\n[{i}] pct={pct}, kw={repr(kw)}, metadata={repr(metadata[:80])}")
    print(f"    kw_type={repr(kw_type)}")
    if kw:
        keywords.append({'keyword': kw, 'traffic_pct': pct, 'type': kw_type})

print(f"\nTotal keywords found: {len(keywords)}")
for kw in keywords:
    print(f"  {kw}")
browser.close()