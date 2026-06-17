#!/usr/bin/env python3
"""Get the actual title cell (cell #6) and look for ASIN there"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from websocket import create_connection
import urllib.request

tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9225/json').read())
search_tab = next((t for t in tabs if t.get('type') == 'page' and '/s?k=' in t.get('url', '')), None)
ws = create_connection(search_tab['webSocketDebuggerUrl'])
def cdp(method, params=None, mid=[1]):
    mid[0] += 1
    ws.send(json.dumps({'id': mid[0], 'method': method, 'params': params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == mid[0]:
            return r

r = cdp('Runtime.evaluate', {'expression': '''
JSON.stringify({
    // Get cell 6 (title) HTML
    cell6_html: document.querySelectorAll('#main-sellersprite-extension .vxe-table--body-wrapper tr')[0]?.querySelectorAll('td')[5]?.outerHTML?.slice(0, 3000) || 'NONE',
    // Also dump all cell index -> first chars of textContent
    cell_map: (() => {
        const row = document.querySelectorAll('#main-sellersprite-extension .vxe-table--body-wrapper tr')[0];
        const cells = row?.querySelectorAll('td') || [];
        return Array.from(cells).map((c, i) => ({
            idx: i,
            colid: c.getAttribute('colid'),
            text_preview: (c.innerText || '').slice(0, 50),
            html_size: c.outerHTML.length
        }));
    })(),
})
''', 'returnByValue': True})
data = json.loads(r['result']['result']['value'])
print('Cell 6 (title) HTML:')
print(data.get('cell6_html', '')[:3000])
print('\nCell map:')
for c in data.get('cell_map', []):
    print(f'  [{c["idx"]}] colid={c["colid"]} size={c["html_size"]} text={c["text_preview"]!r}')
ws.close()