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
    var section = document.getElementById('seller-sprite-extension-main-relation');
    if (!section) return JSON.stringify({error: 'section not found'});
    
    // Get ALL text content with element structure
    var result = {
        innerHTML: section.innerHTML.substring(0, 2000),
        childCount: section.children.length,
        firstChildTag: section.firstElementChild ? section.firstElementChild.tagName : 'none'
    };
    
    // Look for divs that might contain rows
    var allDivs = section.querySelectorAll('div');
    var divData = [];
    allDivs.forEach(function(d, i){
        var txt = d.innerText.trim();
        if (txt.length > 2 && txt.length < 100) {
            divData.push({i: i, tag: d.tagName, text: txt.substring(0, 50)});
        }
    });
    result.divs = divData.slice(0, 20);
    
    return JSON.stringify(result);
})()
"""
r = browser.eval(js)
print(f"Full HTML (first 2000 chars):\n{r}")
browser.close()