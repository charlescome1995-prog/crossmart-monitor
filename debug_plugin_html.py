import sys, os
sys.path.insert(0, r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend")
sys.stdout.reconfigure(encoding='utf-8')
from browser.cdp_bridge import CDPBrowser
import browser.cdp_bridge as cdp
cdp.EDGE_PORT = 9225
cdp._USER_SET_PORT = 9225

browser = CDPBrowser()
browser.connect_tab(tab_url_filter="B09542G9ZN")

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
import json, re
plugin_texts = json.loads(raw) if isinstance(raw, str) else raw
traffic_text = plugin_texts.get('seller-sprite-extension-main-relation', '')

def _strip_html(html_str):
    return re.sub(r'<[^>]+>', '', html_str).strip()

def _get_cell_texts(html_str):
    texts = re.findall(r'(?<=<div>)[^<]+', html_str)
    return '\n'.join(texts).strip()

tds = re.findall(r'<td[^>]*>(.*?)</td>', traffic_text, re.DOTALL)
cell_texts = [_get_cell_texts(td) for td in tds]
print(f"Total TDs: {len(tds)}, cell_texts: {len(cell_texts)}")
print(f"cell_texts: {cell_texts}")

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

print(f"\nKeywords found: {len(keywords)}")
for kw in keywords:
    print(f"  {kw}")

browser.close()