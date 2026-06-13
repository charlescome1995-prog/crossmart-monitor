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
    return el.innerHTML;
})()
"""
r = browser.eval(js)
print(f"innerHTML length: {len(r) if r else 0}")
print(f"innerHTML sample (first 300): {repr(r[:300]) if r else None}")
browser.close()