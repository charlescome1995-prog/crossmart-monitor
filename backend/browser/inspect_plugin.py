#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test: does using a fresh tab with Target.createTarget + connect_tab work?"""
import os, sys, time, json
os.environ["CDP_PORT"] = "9225"
sys.path.insert(0, 'C:/Users/OPENPC/.openclaw/workspace-openpc_ad/crossmart-monitor/backend')

from browser.amazon_browser import CDPBrowser

browser = CDPBrowser()

# Open a brand new blank tab
print("Opening new blank tab...")
browser.cmd("Target.createTarget", {"url": "about:blank"})
time.sleep(2)

browser._refresh_tabs()
blank_tabs = [(i,t) for i,t in enumerate(browser._raw_tabs) if "about:blank" in t.get("url","")]
print(f"Blank tabs: {len(blank_tabs)}")
if blank_tabs:
    browser.connect_tab(tab_index=blank_tabs[0][0])
    time.sleep(1)
    print(f"Connected to blank tab id={browser.tab.get('id','')}")

# Navigate to search page
search_url = "https://www.amazon.com/s?k=batana+oil&ref=nb_sb_noss"
print(f"\nNavigating to: {search_url}")
browser.navigate(search_url, wait_min=2, wait_max=4)
time.sleep(8)

# Verify
title = browser.eval("document.title")
print(f"Title: {title}")

# Check search results
count = browser.eval("(function(){ return document.querySelectorAll('.s-result-item').length })()")
print(f"Search results: {count}")

# Check for plugin markers
js = r"""
(function() {
    var items = document.querySelectorAll('.s-result-item[data-component-type="s-search-result"]');
    if (items.length === 0) return { error: 'no items found' };
    var item = items[0];
    var inner = item.innerText || '';
    var naturalPos = inner.indexOf('\u81ea\u7136\u4f4d');
    var adPos = inner.indexOf('\u5e7f\u544a\u4f4d');
    return {
        innerLen: inner.length,
        naturalPos: naturalPos,
        adPos: adPos,
        last300: inner.substring(inner.length - 300).replace(/\n/g, '|')
    };
})()
"""
result = browser.eval(js)
print(f"Plugin detection: {json.dumps(result, ensure_ascii=False)}")

browser.close()