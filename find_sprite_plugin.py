#!/usr/bin/env python3
import sys, os, time
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

# 打开亚马逊产品页
browser.navigate("https://www.amazon.com/dp/" + TEST_ASIN, wait_min=3, wait_max=6)

# 等待页面加载
print("等待页面加载...")
for i in range(20):
    time.sleep(1)
    r = browser.eval("(function(){var el=document.querySelector('#productTitle');return el&&el.textContent.trim()?{ok:true}:{ok:false};})()")
    if r and r.get('ok'):
        print(f"页面就绪 ({i+1}s)")
        break

# 截图看整体布局
browser.screenshot("amazon_with_plugin")

# 找所有可能的浮窗元素
print("\n=== 搜索浮窗元素 ===")
# 常见浮窗选择器
selectors = [
    '[class*="sellersprite"]', '[class*="seller-sprite"]', '[class*="ss-plugin"]',
    '[class*="floating"]', '[class*="float-panel"]', '[class*="plugin-panel"]',
    '[id*="sellersprite"]', '[id*="seller-sprite"]',
    '[class*="side-panel"]', '[class*="analysis-panel"]',
    '[class*="product-insight"]', '[class*="asinsight"]',
    '#sellersprite', '#seller-sprite', '[data-plugin*="sellersprite"]',
    '[class*="seller-sprite"]', '[class*="sprites"]',
    '[data-vue]', '.v-dialog', '.el-dialog', '.el-drawer',
]
for sel in selectors:
    r = browser.eval("document.querySelectorAll('" + sel + "').length")
    if r > 0:
        print(f"  {sel}: {r} 个")

# 找 iframe（插件可能用 iframe 注入）
print("\n=== iframe ===")
iframes = browser.eval("""
(function(){
    var iframes = document.querySelectorAll('iframe');
    return Array.from(iframes).map(function(f){
        return {src: f.src || '', id: f.id || '', className: f.className || ''};
    });
})()
""")
print(iframes[:500])

# 找 shadow DOM
print("\n=== Shadow DOM ===")
shadow = browser.eval("""
(function(){
    var shadows = [];
    var walk = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
    var node;
    while (node = walk.nextNode()) {
        if (node.shadowRoot) {
            shadows.push({tag: node.tagName, id: node.id, className: node.className});
        }
    }
    return JSON.stringify(shadows.slice(0, 20));
})()
""")
print(shadow[:500])

# 找所有 fixed/absolute 定位的元素（浮窗常用定位方式）
print("\n=== Fixed/Absolute 定位元素 ===")
fixed = browser.eval("""
(function(){
    var all = document.querySelectorAll('*');
    var found = [];
    for (var i = 0; i < all.length; i++) {
        var s = window.getComputedStyle(all[i]);
        if ((s.position === 'fixed' || s.position === 'absolute') && s.display !== 'none') {
            var rect = all[i].getBoundingClientRect();
            if (rect.width > 50 && rect.height > 50) {
                found.push({tag: all[i].tagName, className: all[i].className.substring(0,50), id: all[i].id, rect: JSON.stringify(rect)});
            }
        }
    }
    return JSON.stringify(found.slice(0, 20));
})()
""")
print(fixed[:1000])

# 检查 localStorage/sessionStorage 里的 sellersprite 数据
print("\n=== 插件存储 ===")
storage = browser.eval("""
(function(){
    var keys = [];
    for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i);
        if (k.toLowerCase().includes('seller') || k.toLowerCase().includes('sprite')) {
            keys.push(k);
        }
    }
    return JSON.stringify(keys);
})()
""")
print("localStorage keys:", storage)

browser.close()