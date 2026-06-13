import sys, os
sys.path.insert(0, r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend")
sys.stdout.reconfigure(encoding='utf-8')
from browser.cdp_bridge import CDPBrowser
import browser.cdp_bridge as cdp
cdp.EDGE_PORT = 9225
cdp._USER_SET_PORT = 9225

browser = CDPBrowser()
browser.connect_tab(tab_url_filter="B09542G9ZN")

js = """
(function(){
    var el = document.getElementById('seller-sprite-extension-main-relation');
    if (!el) return 'NOT FOUND';
    return el.innerHTML.replace(/\\0/g, '');
})()
"""
html = browser.eval(js)
if not html:
    print("No HTML returned")
    browser.close()
    exit()

import re

tds = re.findall(r'<td[^>]*>(.*?)</td>', html, re.DOTALL)
print(f"Found {len(tds)} TDs")

# Extract text for each TD
cell_texts = []
for td in tds:
    raw = re.sub(r'<[^>]*>', '', td)
    lines = [l.strip() for l in raw.split('\n') if l.strip()]
    cell_texts.append('\n'.join(lines))

print(f"\nAll cell_texts:")
for i, ct in enumerate(cell_texts):
    print(f"  [{i}] {repr(ct[:80])}")

browser.close()