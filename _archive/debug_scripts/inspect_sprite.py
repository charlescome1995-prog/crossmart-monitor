#!/usr/bin/env python3
"""Connect to CDP and inspect what Seller Sprite actually injects into Amazon pages."""
import json, asyncio, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Use websocket-client
try:
    from websocket import create_connection
except ImportError:
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'websocket-client', '-q'])
    from websocket import create_connection

import urllib.request
tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9225/json').read())
amazon_tab = None
for t in tabs:
    if t.get('type') == 'page' and 'B017PCGABI' in t.get('url', ''):
        amazon_tab = t
        break
if not amazon_tab:
    # Try Garnier tab
    for t in tabs:
        if t.get('type') == 'page' and 'amazon.com' in t.get('url', ''):
            amazon_tab = t
            break
print('Found Amazon tab:', amazon_tab.get('url')[:100] if amazon_tab else 'NONE')
print('Tab ID:', amazon_tab.get('id') if amazon_tab else 'NONE')

# Connect to its WS
ws = create_connection(amazon_tab['webSocketDebuggerUrl'])

def cdp(method, params=None, mid=[1]):
    mid[0] += 1
    ws.send(json.dumps({'id': mid[0], 'method': method, 'params': params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == mid[0]:
            return r

# Eval: find any element with "sprite" in id, class, or data
expr = '''
JSON.stringify({
    has_seller_sprite_global: !!window.sellerSprite,
    has_amazon_page_ext: !!document.querySelector('[id*="seller-sprite"]'),
    has_amazon_listing_ext: !!document.querySelector('[class*="seller-sprite"]'),
    has_amazon_quick_view: !!document.querySelector('#seller-sprite-extension-quick-view-listing-page, [id*="quick-view-listing"]'),
    has_amazon_quick_view2: !!document.querySelector('[id*="quick-view"]'),
    body_classes: document.body.className,
    doc_html_size: document.documentElement.outerHTML.length,
    body_html_size: document.body.outerHTML.length,
    // Check for productScout-style injected elements
    extension_iframes: Array.from(document.querySelectorAll('iframe')).filter(f => f.src.includes('seller') || f.src.includes('sprite')).map(f => f.src).slice(0, 5),
    // Shadow DOM check
    seller_sprite_shadow: Array.from(document.querySelectorAll('*')).filter(e => e.shadowRoot && (e.id||'').toLowerCase().includes('sprite')).map(e => e.id).slice(0, 5),
    // Amazon detail page specific
    has_aplus: !!document.querySelector('#aplus'),
    has_feature_bullets: !!document.querySelector('#feature-bullets'),
    has_detail_bullets: !!document.querySelector('#detailBullets_feature_div'),
    has_product_details: !!document.querySelector('#productDetails_detailBullets_sections1'),
    has_product_info: !!document.querySelector('#productInfo'),
    has_sellersprite_rank: !!document.querySelector('[data-sellersprite]'),
    all_ids_with_seller: Array.from(document.querySelectorAll('[id*="seller" i]')).map(e => e.id).slice(0, 10),
    all_classes_with_seller: Array.from(document.querySelectorAll('[class*="seller" i]')).map(e => e.className).slice(0, 5),
    all_ids_with_sprite: Array.from(document.querySelectorAll('[id*="sprite" i]')).map(e => e.id).slice(0, 10),
    // Check for "产品查询" text
    has_cnq_text: document.body.innerText.includes('产品查询'),
    has_ecs_text: document.body.innerText.includes('查询'),
    has_quick_text: document.body.innerText.includes('Quick View')
})
'''
r = cdp('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
print('\n=== DOM inspection ===')
print(json.dumps(json.loads(r['result']['result']['value']), indent=2, ensure_ascii=False))
ws.close()