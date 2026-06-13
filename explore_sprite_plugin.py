#!/usr/bin/env python3
import sys, os, time, json
sys.stdout.reconfigure(encoding='utf-8')
_backend = r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend"
sys.path.insert(0, _backend)
from browser.cdp_bridge import CDPBrowser

browser = CDPBrowser()
browser.connect_tab(tab_url_filter="about:blank")
if not browser.tab:
    browser.cmd("Target.createTarget", {"url": "about:blank"})
    time.sleep(1)
    browser.connect_tab(tab_url_filter="about:blank")

TEST_ASIN = "B09542G9ZN"
browser.navigate("https://www.amazon.com/dp/" + TEST_ASIN, wait_min=3, wait_max=6)

for i in range(20):
    time.sleep(1)
    r = browser.eval("(function(){var el=document.querySelector('#productTitle');return el&&el.textContent.trim()?{ok:true}:{ok:false};})()")
    if r and r.get('ok'):
        print("Page ready ({}s)".format(i+1))
        break

browser.screenshot("amazon_plugin_overview")

# 探索所有 seller-sprite 元素
print("\n=== seller-sprite 元素详情 ===")
elements = browser.eval("""
(function(){
    var els = document.querySelectorAll('[class*="seller-sprite"], [id*="seller-sprite"]');
    var result = [];
    for (var i = 0; i < els.length; i++) {
        var el = els[i];
        var rect = el.getBoundingClientRect();
        var style = window.getComputedStyle(el);
        var children = el.children ? el.children.length : 0;
        result.push({
            index: i,
            tag: el.tagName,
            id: el.id.substring(0, 40),
            className: el.className.substring(0, 60),
            pos: style.position,
            display: style.display,
            visibility: style.visibility,
            width: Math.round(rect.width),
            height: Math.round(rect.height),
            children: children,
            textPreview: (el.textContent || '').trim().substring(0, 100)
        });
    }
    return JSON.stringify(result);
})()
""")
elements = json.loads(elements)
for el in elements:
    print("  [{}] {} id={} class={} pos={} {}x{} children={}".format(
        el['index'], el['tag'], el['id'], el['className'], el['pos'], el['width'], el['height'], el['children']))
    if el['textPreview']:
        print("       text: {}".format(el['textPreview'][:80]))

# 找最大的浮窗元素
print("\n=== 最大 seller-sprite 元素 ===")
max_el = browser.eval("""
(function(){
    var els = document.querySelectorAll('[class*="seller-sprite"], [id*="seller-sprite"]');
    var maxArea = 0;
    var maxEl = null;
    for (var i = 0; i < els.length; i++) {
        var r = els[i].getBoundingClientRect();
        var area = r.width * r.height;
        if (area > maxArea) { maxArea = area; maxEl = els[i]; }
    }
    if (!maxEl) return JSON.stringify({});
    return JSON.stringify({
        tag: maxEl.tagName,
        id: maxEl.id,
        className: maxEl.className,
        width: maxEl.getBoundingClientRect().width,
        height: maxEl.getBoundingClientRect().height,
        html: maxEl.innerHTML.substring(0, 2000)
    });
})()
""")
max_data = json.loads(max_el)
print("最大元素: {} id={} class={} {}x{}".format(max_data.get('tag'), max_data.get('id'), max_data.get('className'), max_data.get('width'), max_data.get('height')))
print("HTML预览:", max_data.get('html', '')[:1500])

# 看 side-panel
print("\n=== side-panel 元素 ===")
sp = browser.eval("""
(function(){
    var els = document.querySelectorAll('[class*="side-panel"]');
    var result = [];
    for (var i = 0; i < els.length; i++) {
        var el = els[i];
        var rect = el.getBoundingClientRect();
        result.push({
            tag: el.tagName,
            id: el.id,
            className: el.className,
            width: Math.round(rect.width),
            height: Math.round(rect.height),
            text: (el.textContent || '').trim().substring(0, 200)
        });
    }
    return JSON.stringify(result);
})()
""")
print(sp[:1000])

browser.close()