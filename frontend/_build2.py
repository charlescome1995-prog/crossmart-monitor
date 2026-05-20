#!/usr/bin/env python3
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'monitor.html')
DATA = os.path.join(BASE, 'data', 'monitor-data.json')

CSS = """.topbar{background:#131921;color:#fff;display:flex;align-items:center;justify-content:space-between;height:48px;padding:0 24px;position:sticky;top:0;z-index:100}
.topbar .brand{font-weight:700;font-size:16px}
.topbar nav{display:flex;gap:14px;font-size:13px}
.topbar nav a{color:rgba(255,255,255,.75);text-decoration:none;padding:4px 0;border-bottom:2px solid transparent;transition:.15s}
.topbar nav a:hover,.topbar nav a.active{color:#fff;border-bottom-color:#e94560}
.configbar{background:#f3f3f3;border-bottom:1px solid #ddd;padding:10px 16px;display:flex;flex-direction:column;gap:8px}
.config-row{display:flex;gap:8px;align-items:flex-start;flex-wrap:wrap}
.config-label{font-size:11px;font-weight:700;color:#555;text-transform:uppercase;letter-spacing:.4px;min-width:60px;padding-top:5px}
.config-inputs{display:flex;gap:6px;flex-wrap:wrap;flex:1}
.config-inputs input{padding:4px 8px;border:1px solid #ccc;border-radius:4px;font-size:11px;width:120px;background:#fff}
.config-inputs input:focus{border-color:#e94560;outline:none}
.config-actions{display:flex;gap:6px;align-items:center}
.btn{display:inline-flex;align-items:center;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;cursor:pointer;border:none;transition:.15s;background:#e6e8ea;color:#0f1111}
.btn:hover{background:#d5d9d9}
.btn-save{background:#ffd814;color:#0f1111}.btn-save:hover{background:#f7ca00}
.btn-p{background:#ffd814;color:#0f1111}.btn-p:hover{background:#f7ca00}
.btn-sm{padding:3px 8px;font-size:10px}
.config-hint{font-size:10px;color:#999}
.filters{background:#fff;padding:8px 16px;display:flex;gap:8px;align-items:center;border-bottom:1px solid #d5d9d9;position:sticky;z-index:99;box-shadow:0 1px 3px rgba(0,0,0,.04);flex-wrap:wrap}
.filters input{padding:5px 10px;border:1px solid #d5d9d9;border-radius:6px;font-size:12px;width:140px}
.filters select{padding:5px 10px;border:1px solid #d5d9d9;border-radius:6px;font-size:12px}
.filters label{font-size:12px;color:#555;display:flex;align-items:center;gap:4px;cursor:pointer}
.sort-indicator{font-size:9px;color:#e94560;margin-left:2px}
.board-wrap{padding:12px;overflow-x:auto}
.board{width:100%;border-collapse:collapse;font-size:12px;background:#fff;white-space:nowrap}
.board th{background:#f5f5f5;padding:8px 10px;text-align:left;font-size:10px;font-weight:700;color:#555;text-transform:uppercase;letter-spacing:.5px;border-bottom:2px solid #e0e0e0;position:sticky;z-index:10;cursor:pointer;user-select:none}
.board th:hover{background:#ececec}
.board td{padding:0;border-bottom:1px solid #f0f0f0;vertical-align:middle}
.board tr:hover td{background:#f9f9f9}
.board tr:last-child td{border-bottom:none}
.board .td-img{width:90px;min-width:90px;padding:6px 8px}
.board .td-img img{width:72px;height:72px;object-fit:cover;border-radius:6px;display:block;border:1px solid #eee}
.board .td-asin{font-size:10px;font-weight:700;color:#007185;padding:6px 8px;cursor:pointer}
.board .td-asin:hover,.board .td-title:hover{background:#f0f0f0}
.board .td-title{min-width:200px;max-width:280px;padding:6px 8px;cursor:pointer}
.board .td-title .title-text{overflow:hidden;text-overflow:ellipsis;font-size:11px;font-weight:600;color:#0f1111;max-width:280px}
.board .td-title .expand-arrow{font-size:9px;margin-right:4px;color:#999;display:inline-block}
.board .td-brand{min-width:100px;padding:6px 8px;font-size:10px;color:#888}
.board .td-price{min-width:80px;padding:6px 8px;text-align:right}
.board .td-price .price{font-size:14px;font-weight:700;color:#B12704}
.board .td-price .list{font-size:10px;color:#888;text-decoration:line-through;margin-left:4px}
.board .td-chg{min-width:70px;padding:6px 8px;text-align:center}
.board .chg{padding:2px 6px;border-radius:4px;font-size:10px;font-weight:700}
.board .chg.up{color:#059669;background:#f0fdf4}
.board .chg.dn{color:#dc2626;background:#fef2f2}
.board .chg.flat{color:#999;background:#f5f5f5}
.board .td-bsr{min-width:80px;padding:6px 8px;text-align:right}
.board .bsr{font-size:13px;font-weight:700;color:#067d62}
.board .bsr-sub{font-size:10px;color:#888}
.board .td-rating{min-width:80px;padding:6px 8px;text-align:center}
.board .rating{font-size:13px;font-weight:700;color:#d99536}
.board .td-reviews{min-width:80px;padding:6px 8px;text-align:right;font-size:13px;font-weight:600}
.board .td-seller{min-width:120px;padding:6px 8px;font-size:10px;color:#555;max-width:150px;overflow:hidden;text-overflow:ellipsis}
.board .td-group{padding:6px 8px;text-align:center}
.board .grp-badge{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;background:#e94560;color:#fff;font-size:10px;font-weight:700}
tr.detail-row td{padding:0;border-bottom:none;background:#fafafa}
tr.detail-row:hover td{background:#f5f5f5}
.detail-expanded{padding:12px 16px 16px 98px}
.de-header{display:flex;align-items:center;gap:16px;margin-bottom:10px;flex-wrap:wrap}
.de-metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-bottom:10px}
.de-m{background:#f0f0f0;border-radius:8px;padding:8px 10px;text-align:center}
.de-ml{font-size:9px;color:#888;font-weight:600;text-transform:uppercase;margin-bottom:3px}
.de-mv{font-size:15px;font-weight:800;color:#131921;word-break:break-all}
.de-mv.pc{color:#B12704}.de-mv.rt{color:#d99536}.de-mv.bsr{color:#067d62}
.de-chart-wrap{height:100px;margin-bottom:6px}
.de-chart-wrap canvas{max-height:100px!important}
.de-history{font-size:9px;color:#bbb;text-align:right;margin-bottom:10px}
.de-sub-header{font-size:10px;font-weight:700;color:#555;text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid #e0e0e0}
.de-members{display:flex;flex-direction:column;gap:6px}
.de-member{display:flex;align-items:center;gap:10px;background:#fff;border:1px solid #e8e8e8;border-radius:6px;padding:6px 10px}
.de-member.main-member{border-color:#ffd814;background:#fffbe6}
.de-member-img{width:32px;height:32px;border-radius:4px;object-fit:cover;flex-shrink:0}
.de-member-info{flex:1;min-width:0}
.de-member-name{font-size:10px;font-weight:700;color:#007185;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.de-member-title{font-size:9px;color:#888;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.de-member-chg{margin-left:auto;flex-shrink:0}
.loading{text-align:center;padding:40px;color:#999;font-size:13px}"""

HTML_PROLOG = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CrossMart Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7"></script>
<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
<style>
{CSS}
</style>
</head>
<body>
<div class="topbar">
  <span class="brand">Cross<span style="color:#e94560">Mart</span></span>
  <nav>
    <a href="../index.html">Home</a>
    <a href="monitor.html" class="active">Monitor</a>
    <a href="selection.html">Selection</a>
  </nav>
</div>

<div class="configbar">
  <div class="config-row">
    <span class="config-label">ASINs</span>
    <div class="config-inputs">
      <input type="text" id="asin0" placeholder="ASIN 1" value="">
      <input type="text" id="asin1" placeholder="ASIN 2" value="">
      <input type="text" id="asin2" placeholder="ASIN 3" value="">
      <input type="text" id="asin3" placeholder="ASIN 4" value="">
      <input type="text" id="asin4" placeholder="ASIN 5" value="">
    </div>
  </div>
  <div class="config-row">
    <span class="config-label">Keywords</span>
    <div class="config-inputs">
      <input type="text" id="kw0" placeholder="Keyword 1" value="">
      <input type="text" id="kw1" placeholder="Keyword 2" value="">
      <input type="text" id="kw2" placeholder="Keyword 3" value="">
      <input type="text" id="kw3" placeholder="Keyword 4" value="">
      <input type="text" id="kw4" placeholder="Keyword 5" value="">
    </div>
    <div class="config-actions">
      <button class="btn btn-save btn-sm" onclick="saveConfig()">Save</button>
      <span class="config-hint" id="cfgHint"></span>
    </div>
  </div>
</div>

<div class="filters">
  <input type="text" id="sf" placeholder="Search ASIN or title..." oninput="render()">
  <select id="ss" onchange="render()">
    <option value="bsr">BSR up</option>
    <option value="price">Price dn</option>
    <option value="price_chg">Price Change</option>
    <option value="bsr_chg">BSR Change</option>
    <option value="rating">Rating</option>
    <option value="reviews">Reviews</option>
    <option value="title">Title A-Z</option>
  </select>
  <label><input type="checkbox" id="sc" onchange="render()"> Changes only</label>
  <button class="btn btn-sm" onclick="refresh()">Refresh</button>
  <button class="btn btn-sm btn-p" onclick="exportXlsx()">Export</button>
</div>

<div class="board-wrap">
<table class="board" id="board">
  <thead>
    <tr>
      <th onclick="sortBy('asin')">ASIN<span class="sort-indicator" id="ind-asin"></span></th>
      <th>Image</th>
      <th onclick="sortBy('title')">Title<span class="sort-indicator" id="ind-title"></span></th>
      <th onclick="sortBy('brand')">Brand<span class="sort-indicator" id="ind-brand"></span></th>
      <th onclick="sortBy('price')">Price<span class="sort-indicator" id="ind-price"></span></th>
      <th onclick="sortBy('price_chg')">Chg<span class="sort-indicator" id="ind-price_chg"></span></th>
      <th onclick="sortBy('bsr')">BSR<span class="sort-indicator" id="ind-bsr"></span></th>
      <th>Sub BSR</th>
      <th onclick="sortBy('rating')">Rating<span class="sort-indicator" id="ind-rating"></span></th>
      <th onclick="sortBy('reviews')">Reviews<span class="sort-indicator" id="ind-reviews"></span></th>
      <th>Seller</th>
      <th>Grp</th>
    </tr>
  </thead>
  <tbody id="boardBody"><tr><td colspan="12" class="loading">Loading...</td></tr></tbody>
</table>
</div>

<script>
window.MONITOR_EMBED = __DATA__;
</script>
</body>
</html>"""

JS = (
    "var _data=null,_charts={},_sortKey='bsr',_sortAsc=false,_filterText='',_changesOnly=false,_expandedAsin=null;"
    "function initMonitor(d){_data=d;loadConfig();render();}"
    "function refresh(){loadConfig();render();}"
    "function loadConfig(){try{var cfg=JSON.parse(localStorage.getItem('crossmart_cfg')||'{}');for(var i=0;i<5;i++){var ae=document.getElementById('asin'+i),ke=document.getElementById('kw'+i);if(ae&&cfg['asin'+i]!==undefined)ae.value=cfg['asin'+i]||'';if(ke&&cfg['kw'+i]!==undefined)ke.value=cfg['kw'+i]||'';}}}catch(e){}}"
    "function saveConfig(){var cfg={};for(var i=0;i<5;i++){var ae=document.getElementById('asin'+i),ke=document.getElementById('kw'+i);cfg['asin'+i]=ae?ae.value.trim():'';cfg['kw'+i]=ke?ke.value.trim():'';}localStorage.setItem('crossmart_cfg',JSON.stringify(cfg));var h=document.getElementById('cfgHint');if(h){h.textContent='Saved';setTimeout(function(){h.textContent='';},2000);}}"
    "function sortBy(key){if(_sortKey===key){_sortAsc=!_sortAsc;}else{_sortKey=key;_sortAsc=false;}render();}"
    "function updateSortIndicators(){['bsr','price','price_chg','bsr_chg','rating','reviews','title','brand','asin'].forEach(function(k){var el=document.getElementById('ind-'+k);if(!el)return;el.textContent=(k===_sortKey)?(_sortAsc?' down':' up'):'';});}"
    "function getAllAsins(){var all=[];if(!_data||!_data.groups)return all;_data.groups.forEach(function(g,gi){g.members.forEach(function(m){if(m.asin)all.push({m:m,g:g,gi:gi});});});return all;}"
    "function sortAsins(list){var key=_sortKey,asc=_sortAsc;list.sort(function(a,b){var va,vb;if(key==='title'){va=(a.m.title||'').toLowerCase();vb=(b.m.title||'').toLowerCase();return asc?va.localeCompare(vb):vb.localeCompare(va);}else if(key==='brand'){va=(a.m.brand||'').toLowerCase();vb=(b.m.brand||'').toLowerCase();return asc?va.localeCompare(vb):vb.localeCompare(va);}else if(key==='asin'){va=(a.m.asin||'');vb=(b.m.asin||'');return asc?va.localeCompare(vb):vb.localeCompare(va);}else if(key==='price'){va=a.m.price||0;vb=b.m.price||0;return asc?va-vb:vb-va;}else if(key==='price_chg'){va=getChange(a.m);vb=getChange(b.m);return asc?va-vb:vb-va;}else if(key==='bsr_chg'){va=a.m.bsr_change||0;vb=b.m.bsr_change||0;return asc?va-vb:vb-va;}else if(key==='rating'){va=parseFloat(a.m.rating)||0;vb=parseFloat(b.m.rating)||0;return asc?va-vb:vb-va;}else if(key==='reviews'){va=a.m.review_count||0;vb=b.m.review_count||0;return asc?va-vb:vb-va;}va=a.m.bsr||999999;vb=b.m.bsr||999999;return asc?va-vb:vb-va;});return list;}"
    "function filterAsins(list){var txt=_filterText.toLowerCase();if(_changesOnly)list=list.filter(function(it){return getChange(it.m)!==0;});if(!txt)return list;return list.filter(function(it){if((it.m.asin||'').toLowerCase().indexOf(txt)!==-1)return true;if((it.m.title||'').toLowerCase().indexOf(txt)!==-1)return true;if((it.m.brand||'').toLowerCase().indexOf(txt)!==-1)return true;return false;});}"
    "function render(){var tbody=document.getElementById('boardBody');if(!_data||!_data.groups){tbody.innerHTML='<tr><td colspan=\"12\" class=\"loading\">No data. Run sync_groups.py first.</td></tr>';return;}var sel=document.getElementById('ss');_sortKey=sel?sel.value:_sortKey;_filterText=(document.getElementById('sf')||{}).value||'';_changesOnly=(document.getElementById('sc')||{}).checked||false;updateSortIndicators();var list=filterAsins(sortAsins(getAllAsins()));if(list.length===0){tbody.innerHTML='<tr><td colspan=\"12\" class=\"loading\">No results found.</td></tr>';return;}var html='';list.forEach(function(item){var m=item.m,g=item.g;var ch=getChange(m),chClass=ch>0?'up':ch<0?'dn':'flat';var chTxt=ch===0?'0':(ch>0?'+'+ch.toFixed(2):ch.toFixed(2));var price=m.price?'$'+m.price.toFixed(2):'---';var bsr=m.bsr?'#'+m.bsr.toLocaleString():'---';var bsrSub=m.bsr_sub_rank?'#'+m.bsr_sub_rank.toLocaleString():'---';var rating=m.rating||'---';var reviews=m.review_count?m.review_count.toLocaleString():'---';var isExpanded=_expandedAsin===(m.asin||'');var arrow=isExpanded?'v':'>';var imgHTML=m.main_image?'<img src=\"'+m.main_image+'\" alt=\"'+e(m.asin||'')+'\">':'';html+='<tr>';html+='<td class=\"td-asin\" onclick=\"toggleDetail(\\''+e(m.asin||'')+'\\')\"><span class=\"expand-arrow\">'+arrow+'</span>'+(m.asin||'')+'</td>';html+='<td class=\"td-img\">'+imgHTML+'</td>';html+='<td class=\"td-title\" onclick=\"toggleDetail(\\''+e(m.asin||'')+'\\')\"><span class=\"expand-arrow\">'+arrow+'</span><div class=\"title-text\">'+e(m.title||'')+'</div></td>';html+='<td class=\"td-brand\">'+e(m.brand||'')+'</td>';html+='<td class=\"td-price\"><span class=\"price\">'+price+'</span>'+(m.list_price?'<span class=\"list\">$'+m.list_price.toFixed(2)+'</span>':'')+'</td>';html+='<td class=\"td-chg\"><span class=\"chg '+chClass+'\">'+chTxt+'</span></td>';html+='<td class=\"td-bsr\"><div class=\"bsr\">'+bsr+'</div></td>';html+='<td class=\"td-bsr\"><div class=\"bsr-sub\">'+bsrSub+'</div></td>';html+='<td class=\"td-rating\"><span class=\"rating\">* '+rating+'</span></td>';html+='<td class=\"td-reviews\">'+reviews+'</td>';html+='<td class=\"td-seller\" title=\"'+e(m.seller||'')+'\">'+e(m.seller||'---')+'</td>';html+='<td class=\"td-group\"><span class=\"grp-badge\" title=\"Group: '+g.main_asin+'\">'+g.members.length+'</span></td>';html+='</tr>';if(isExpanded){html+='<tr class=\"detail-row\"><td colspan=\"12\">';html+=buildDetailHTML(item);html+='</td></tr>';}});tbody.innerHTML=html;if(_expandedAsin)setTimeout(drawExpandedCharts,30);}"
    "function toggleDetail(asin){_expandedAsin=(_expandedAsin===asin)?null:asin;render();}"
    "function buildDetailHTML(item){var m=item.m,g=item.g;var ch=getChange(m),chClass=ch>0?'up':ch<0?'dn':'flat';var chTxt=ch===0?'stable':(ch>0?'+'+ch.toFixed(2):ch.toFixed(2));var price=m.price?'$'+m.price.toFixed(2):'---';var bsr=m.bsr?'#'+m.bsr.toLocaleString():'---';var bsrSub=m.bsr_sub_rank?'#'+m.bsr_sub_rank.toLocaleString():'---';var rating=m.rating||'---';var reviews=m.review_count?m.review_count.toLocaleString():'---';var isMain=m.asin===g.main_asin;var html='<div class=\"detail-expanded\">';html+='<div class=\"de-header\">';if(m.main_image)html+='<img src=\"'+m.main_image+'\" style=\"width:40px;height:40px;border-radius:6px;object-fit:cover;border:1px solid #eee;flex-shrink:0\">';html+='<div style=\"flex:1;min-width:0\">';html+='<div style=\"font-size:12px;font-weight:700;color:#007185\">'+(isMain?'* ':'')+m.asin+'</div>';html+='<div style=\"font-size:10px;color:#888;white-space:nowrap;overflow:hidden;text-overflow:ellipsis\">'+e(m.title||'')+'</div>';html+='</div>';html+='<span class=\"chg '+chClass+'\" style=\"padding:4px 10px;font-size:13px;font-weight:700;margin-left:auto\">'+chTxt+'</span></div>';html+='<div class=\"de-metrics\">';html+='<div class=\"de-m\"><div class=\"de-ml\">Price</div><div class=\"de-mv pc\">'+price+'</div></div>';html+='<div class=\"de-m\"><div class=\"de-ml\">BSR</div><div class=\"de-mv bsr\">'+bsr+'</div></div>';html+='<div class=\"de-m\"><div class=\"de-ml\">Sub BSR</div><div class=\"de-mv\" style=\"font-size:12px\">'+bsrSub+'</div></div>';html+='<div class=\"de-m\"><div class=\"de-ml\">Rating</div><div class=\"de-mv rt\">* '+rating+'</div></div>';html+='<div class=\"de-m\"><div class=\"de-ml\">Reviews</div><div class=\"de-mv\">'+reviews+'</div></div></div>';html+='<div class=\"de-chart-wrap\"><canvas id=\"de_chart_'+m.asin+'\"></canvas></div>';var h=m.history||[];if(h.length>0){var first=h[0]?(h[0].timestamp||''):'',last=h[h.length-1]?(h[h.length-1].timestamp||''):'';html+='<div class=\"de-history\">'+e(first)+' -> '+e(last)+' ('+h.length+' pts)</div>';}var others=g.members.filter(function(o){return o.asin&&o.asin!==m.asin;});if(others.length>0){html+='<div class=\"de-sub-header\">Group Members ('+others.length+' other'+(others.length>1?'s':'')+')</div><div class=\"de-members\">';others.forEach(function(o){var och=getChange(o),ochClass=och>0?'up':och<0?'dn':'flat';var ochTxt=och===0?'0':(och>0?'+'+och.toFixed(2):och.toFixed(2));var oprice=o.price?'$'+o.price.toFixed(2):'---';var obsr=o.bsr?'#'+o.bsr.toLocaleString():'---';var oisMain=o.asin===g.main_asin;html+='<div class=\"de-member'+(oisMain?' main-member':'')+'\">';html+=o.main_image?'<img src=\"'+o.main_image+'\" class=\"de-member-img\">':'<div class=\"de-member-img\" style=\"background:#eee;border-radius:4px\"></div>';html+='<div class=\"de-member-info\"><div class=\"de-member-name\">'+(oisMain?'* ':'')+o.asin+'</div><div class=\"de-member-title\">'+e(o.title||'')+'</div></div>';html+='<div class=\"de-member-chg\"><span style=\"font-size:10px;color:#888\">'+oprice+' . '+obsr+'</span> <span class=\"chg '+ochClass+'\">'+ochTxt+'</span></div></div>';});html+='</div>';}html+='</div>';return html;}"
    "function drawExpandedCharts(){var asin=_expandedAsin;if(!asin)return;var canvas=document.getElementById('de_chart_'+asin);if(!canvas)return;var item=null;if(_data&&_data.groups){outer:for(var gi=0;gi<_data.groups.length;gi++){var g=_data.groups[gi];for(var mi=0;mi<g.members.length;mi++){if(g.members[mi].asin===asin){item={m:g.members[mi],g:g,gi:gi};break outer;}}}}if(!item)return;var m=item.m,h=m.history||[],prices=[],bsrData=[];h.forEach(function(pt){if(pt.price!=null)prices.push(pt.price);if(pt.bsr!=null)bsrData.push(pt.bsr);});if(!prices.length&&!bsrData.length)return;var datasets=[];if(prices.length>1)datasets.push({label:'Price',data:prices,borderColor:'#B12704',backgroundColor:'rgba(177,39,4,.05)',borderWidth:2,fill:true,tension:0.3,pointRadius:2,yAxisID:'y'});if(bsrData.length>1)datasets.push({label:'BSR',data:bsrData,borderColor:'#067d62',backgroundColor:'transparent',borderWidth:2,fill:false,tension:0.3,pointRadius:2,yAxisID:'y1'});var cid='de_chart_'+asin;if(_charts[cid]){_charts[cid].destroy();_charts[cid]=null;}_charts[cid]=new Chart(canvas,{type:'line',data:{labels:h.map(function(){return '';}),datasets:datasets},options:{responsive:true,maintainAspectRatio:false,animation:{duration:200},plugins:{legend:{display:true,position:'top',labels:{font:{size:9},boxWidth:12,padding:4}},tooltip:{mode:'index',intersect:false}},scales:{x:{display:false},y:{position:'left',grid:{color:'rgba(0,0,0,.05)'},ticks:{font:{size:9},maxTicksLimit:4}},y1:{position:'right',grid:{display:false},ticks:{font:{size:9},maxTicksLimit:4}}}}});}"
    "function getChange(member){var h=member.history||[];if(h.length<2)return 0;var p1=null,p2=null;for(var i=h.length-1;i>=0;i--){if(h[i].price!=null&&p1===null)p1=h[i].price;else if(h[i].price!=null&&p2===null){p2=h[i].price;break;}}if(p1==null||p2==null)return 0;return Math.round((p1-p2)*100)/100;}"
    "function e(s){if(!s)return'';return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\"/g,'&quot;');}"
    "function exportXlsx(){if(!_data||!_data.groups)return;var wb=XLSX.utils.book_new();var rows=[['ASIN','Title','Brand','Price','List Price','Rating','Reviews','BSR','BSR Sub Rank','Category','Seller','Price Change','Last Updated']];_data.groups.forEach(function(g){g.members.forEach(function(m){var ch=getChange(m),h=m.history||[];var lastTs='';for(var i=h.length-1;i>=0;i--){if(h[i].price!=null||h[i].bsr!=null){lastTs=h[i].timestamp||'';break;}}rows.push([m.asin||'',(m.title||'').substring(0,80),m.brand||'',m.price||'',m.list_price||'',m.rating||'',m.review_count||'',m.bsr||'',m.bsr_sub_rank||'',(m.bsr_sub_category||'').substring(0,60),m.seller||'',ch,lastTs]);});});var ws=XLSX.utils.aoa_to_sheet(rows);ws['!cols']=[{wch:14},{wch:50},{wch:20},{wch:8},{wch:10},{wch:8},{wch:10},{wch:10},{wch:12},{wch:25},{wch:20},{wch:8},{wch:20}];XLSX.utils.book_append_sheet(wb,ws,'Monitor Data');XLSX.writeFile(wb,'crossmart_monitor_'+new Date().toISOString().substring(0,10)+'.xlsx');}"
    "initMonitor(window.MONITOR_EMBED||{});"
)

with open(DATA, 'r', encoding='utf-8') as f:
    raw_data = f.read()
safe_data = raw_data.replace('</script>', '<\\/script>')

html = HTML_PROLOG.replace('{CSS}', CSS)
html = html.replace('__DATA__', safe_data)

with open(OUT, 'w', encoding='utf-8', newline='') as f:
    f.write(html)
    f.write('<script>' + JS + '</script>')

print('Done. Size:', os.path.getsize(OUT))
