import sys, os, time
sys.path.insert(0, r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend")
sys.stdout.reconfigure(encoding='utf-8')
import importlib
import browser.cdp_bridge as cdp
cdp.EDGE_PORT = 9225
cdp._USER_SET_PORT = 9225

import browser.asin_monitor as am
importlib.reload(am)

browser = cdp.CDPBrowser()
browser.connect_tab(tab_url_filter="B09542G9ZN")

for i in range(10):
    r = browser.eval("(function(){var el=document.querySelector('#productTitle');return el&&el.textContent.trim()?{ok:true}:{ok:false};})()")
    if r and r.get('ok'):
        print(f"Page ready ({i+1}s)")
        break
    time.sleep(1)

time.sleep(2)

print("\n=== extract_sprite_plugin_data ===")
plugin_data = am.extract_sprite_plugin_data(browser)
print(f"Keys: {list(plugin_data.keys()) if plugin_data else 'NONE'}")
print(f"traffic_keywords_top: {plugin_data.get('traffic_keywords_top', [])}")

browser.close()