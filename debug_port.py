import sys, os
sys.path.insert(0, r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend")
sys.stdout.reconfigure(encoding='utf-8')
import browser.cdp_bridge as cdp
cdp.EDGE_PORT = 9225
cdp._USER_SET_PORT = 9225

print(f"[DEBUG] _USER_SET_PORT = {cdp._USER_SET_PORT}")
print(f"[DEBUG] EDGE_PORT = {cdp.EDGE_PORT}")
port = cdp.CDPBrowser()._detect_port()
print(f"[DEBUG] _detect_port() returned: {port}")

# Now check what tabs are on each port
import urllib.request, json
for p in [18800, 9225]:
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{p}/json", timeout=3)
        tabs = json.loads(req.read())
        print(f"[DEBUG] Port {p}: {len(tabs)} tabs")
        for t in tabs:
            print(f"  - [{t.get('id','?')[:15]}] {t.get('title','')[:40]} | {t.get('url','')[:60]}")
    except Exception as e:
        print(f"[DEBUG] Port {p}: error - {e}")