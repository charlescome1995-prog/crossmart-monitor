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
    return el ? el.textContent : 'NOT FOUND';
})()
"""
r = browser.eval(js)
print(f"traffic_text (first 800 chars):\n{r[:800] if r else 'EMPTY'}")
browser.close()