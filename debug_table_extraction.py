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
    
    // Element UI table: body rows are div.el-table__row inside el-table__body-wrapper
    var rows = section.querySelectorAll('.el-table__body-wrapper .el-table__row');
    
    var keywords = [];
    rows.forEach(function(row){
        var cells = row.querySelectorAll('td');
        // In Element UI, each td has .cell that contains the actual content
        if (cells.length >= 4) {
            var kw = (cells[0].querySelector('.cell') || cells[0]).innerText.trim();
            var clickShare = (cells[1].querySelector('.cell') || cells[1]).innerText.trim();
            var kwType = (cells[2].querySelector('.cell') || cells[2]).innerText.trim().split('\\n')[0];
            var organicRank = (cells[4].querySelector('.cell') || cells[4]).innerText.trim().split('\\n')[0];
            
            if (kw && clickShare) {
                keywords.push({
                    keyword: kw,
                    click_share: clickShare,
                    type: kwType,
                    organic_rank: organicRank
                });
            }
        }
    });
    
    // Fallback: if no rows found, try direct td extraction
    if (keywords.length === 0) {
        var allTds = section.querySelectorAll('td');
        var tdTexts = [];
        allTds.forEach(function(td){
            tdTexts.push((td.innerText||'').trim());
        });
        return JSON.stringify({fallback_tds: tdTexts.slice(0, 30), row_count: rows.length});
    }
    
    return JSON.stringify({count: keywords.length, keywords: keywords});
})()
"""
r = browser.eval(js)
print(f"Element UI table extraction: {r}")
browser.close()