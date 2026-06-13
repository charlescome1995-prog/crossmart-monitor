import sys, os, json, websocket, random, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend")

# Monkey-patch CDPBrowser.connect_tab to show debug info
from browser import cdp_bridge
_orig = cdp_bridge.CDPBrowser.connect_tab

def debug_connect_tab(self, tab_index=0, tab_url_filter=None):
    self._refresh_tabs()
    tabs = self._raw_tabs
    print(f"  [DEBUG] Total tabs: {len(tabs)}", file=sys.stderr)
    if tab_url_filter:
        filtered = [t for t in tabs if tab_url_filter.lower() in (t.get("url","")+t.get("title","")).lower()]
        print(f"  [DEBUG] Filter '{tab_url_filter}' matches {len(filtered)} tabs", file=sys.stderr)
        for i, t in enumerate(filtered[:5]):
            print(f"  [DEBUG]   [{i}] {t.get('title','')[:40]} | {t.get('url','')[:60]}", file=sys.stderr)
        if filtered:
            self.tab = filtered[0]
        else:
            print(f"  [DEBUG] No match! Using first tab: {tabs[0].get('title','')[:40]} | {tabs[0].get('url','')[:60]}", file=sys.stderr)
            self.tab = tabs[0]
    else:
        self.tab = tabs[tab_index] if tab_index < len(tabs) else tabs[0]
    print(f"  [DEBUG] Selected tab: {self.tab.get('title','')[:40]} | {self.tab.get('url','')[:60]}", file=sys.stderr)
    return _orig(self, tab_index, tab_url_filter)

cdp_bridge.CDPBrowser.connect_tab = debug_connect_tab

from browser.cdp_bridge import CDPBrowser
browser = CDPBrowser()
browser.connect_tab(tab_url_filter="amazon.com/dp")
print(f"Final tab: {browser.tab.get('title','')[:40]} | {browser.tab.get('url','')[:60]}", file=sys.stderr)
browser.close()