import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
_backend = r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend"
sys.path.insert(0, _backend)

import browser.cdp_bridge as cdp
cdp.EDGE_PORT = 9225
cdp._USER_SET_PORT = 9225

import importlib
import browser.asin_monitor as am
importlib.reload(am)

asin = sys.argv[1] if len(sys.argv) > 1 else "B09542G9ZN"

browser = cdp.CDPBrowser()
browser.connect_tab(tab_url_filter=asin)

for i in range(30):
    r = browser.eval("(function(){var el=document.querySelector('#productTitle');return el&&el.textContent.trim()?{ok:true}:{ok:false};})()")
    if r and r.get('ok'):
        print(f"Page ready ({i+1}s)")
        break
    time.sleep(1)

time.sleep(2)  # let plugin warm up, then poll until ready (max 30s)

# Extract Amazon data
amazon_data = am.extract_asin_data(browser)

# Active polling: wait for plugin data to be ready
plugin_data = {}
for elapsed in range(30):
    candidate = am.extract_sprite_plugin_data(browser)
    if candidate and (candidate.get('plugin_version') or candidate.get('lqs') or (candidate.get('main_text') or '').strip()):
        plugin_data = candidate
        print(f"  Plugin data ready after {elapsed+1}s")
        break
    time.sleep(1)
else:
    print("  Plugin data not detected (extension not installed or not loaded)")

if plugin_data:
    for k, v in plugin_data.items():
        amazon_data['sprite_' + k] = v

# Print results
print(f"\n{'='*60}")
print(f"ASIN: {asin}")
print(f"{'='*60}")
print(f"title: {amazon_data.get('title','')[:80]}")
print(f"price: {amazon_data.get('price','')}")
print(f"rating: {amazon_data.get('rating','')}")
print(f"review_count: {amazon_data.get('review_count','')}")
print(f"brand: {amazon_data.get('brand','')}")
print(f"bsr: {amazon_data.get('bsr','')}")
print(f"bsr_subcategory: {amazon_data.get('bsr_subcategory','')}")
print(f"main_image: {amazon_data.get('main_image','')}")
print(f"rating_distribution: {amazon_data.get('rating_distribution',{})}")
print(f"traffic_keywords_top: {amazon_data.get('traffic_keywords_top',[])}")

# Also print sprite data
sprite_kw = amazon_data.get('sprite_traffic_keywords_top', [])
if sprite_kw:
    print(f"\nsprite_traffic_keywords_top ({len(sprite_kw)}):")
    for kw in sprite_kw:
        print(f"  {kw}")

browser.close()