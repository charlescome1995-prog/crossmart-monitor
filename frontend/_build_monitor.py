#!/usr/bin/env python3
"""Build the new monitor.html from scratch."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'monitor.html')
DATA = os.path.join(BASE, 'data', 'monitor-data.json')

CSS = """/* ─── Top Bar ─── */
.topbar{background:#131921;color:#fff;display:flex;align-items:center;justify-content:space-between;height:48px;padding:0 24px;position:sticky;top:0;z-index:100}
.topbar .brand{font-weight:700;font-size:16px}
.topbar nav{display:flex;gap:14px;font-size:13px}
.topbar nav a{color:rgba(255,255,255,.75);text-decoration:none;padding:4px 0;border-bottom:2px solid transparent;transition:.15s}
.topbar nav a:hover,.topbar nav a.active{color:#fff;border-bottom-color:#e94560}

/* ─── Filter Bar ─── */
.filters{background:#fff;padding:8px 16px;display:flex;gap:8px;align-items:center;border-bottom:1px solid #d5d9d9;position:sticky;top:48px;z-index:99;box-shadow:0 1px 3px rgba(0,0,0,.04);flex-wrap:wrap}
.filters input{padding:5px 10px;border:1px solid #d5d9d9;border-radius:6px;font-size:12px;width:140px}
.filters select{padding:5px 10px;border:1px solid #d5d9d9;border-radius:6px;font-size:12px}
.filters label{font-size:12px;color:#555;display:flex;align-items:center;gap:4px;cursor:pointer}
.btn{display:inline-flex;align-items:center;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;cursor:pointer;border:none;transition:.15s;background:#e6e8ea;color:#0f1111}
.btn:hover{background:#d5d9d9}
.btn-p{background:#ffd814;color:#0f1111}.btn-p:hover{background:#f7ca00}
.btn-sm{padding:3px 8px;font-size:10px}

/* ─── 11-Card Grid ─── */
.board{padding:12px;display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.summary-card{background:#fff;border:2px solid #e94560;border-radius:12px;padding:14px 16px;cursor:pointer;transition:.15s;position:relative;overflow:hidden}
.summary-card:hover{border-color:#c03250;transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,.1)}
.summary-card .sc-badge{position:absolute;top:10px;right:10px;font-size:9px;font-weight:700;background:#e94560;color:#fff;padding:2px 7px;border-radius:10px}
.summary-card .sc-title{font-size:11px;color:#888;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px}
.summary-card .sc-num{font-size:28px;font-weight:800;color:#131921;line-height:1}
.summary-card .sc-meta{font-size:11px;color:#888;margin-top:4px}
.summary-card .sc-icons{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap}
.summary-card .sc-icon{display:flex;align-items:center;gap:3px;font-size:10px;color:#555}
.summary-card .sc-icon .dot{width:8px;height:8px;border-radius:50%;background:#ccc;flex-shrink:0}
.summary-card .sc-icon .dot.up{background:#059669}
.summary-card .sc-icon .dot.dn{background:#dc2626}

.asin-card{background:#fff;border:1px solid #d5d9d9;border-radius:10px;padding:14px;cursor:pointer;transition:.15s;position:relative}
.asin-card:hover{border-color:#007185;transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,.08)}
.asin-card.selected{border-color:#007185;box-shadow:0 0 0 2px #00718533}
.asin-card .ac-top{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px}
.asin-card .ac-img{width:48px;height:48px;border-radius:6px;overflow:hidden;flex-shrink:0;background:#f5f5f5;display:flex;align-items:center;justify-content:center}
.asin-card .ac-img img{width:48px;height:48px;object-fit:cover}
.asin-card .ac-img .ph{font-size:20px;color:#ccc}
.asin-card .ac-info{flex:1;min-width:0}
.asin-card .ac-asin{font-size:10px;font-weight:700;color:#007185;background:#effaff;padding:1px 5px;border-radius:3px;display:inline-block;margin-bottom:3px}
.asin-card .ac-title{font-size:11px;font-weight:600;color:#0f1111;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.asin-card .ac-brand{font-size:10px;color:#888;margin-top:2px}
.asin-card .ac-price-row{display:flex;align-items:baseline;gap:6px;margin-top:6px;flex-wrap:wrap}
.asin-card .ac-price{font-size:16px;font-weight:700;color:#B12704}
.asin-card .ac-list{font-size:10px;color:#888;text-decoration:line-through}
.asin-card .ac-change{font-size:10px;font-weight:600;padding:1px 5px;border-radius:3px}
.asin-card .ac-change.up{color:#059669;background:#f0fdf4}
.asin-card .ac-change.dn{color:#dc2626;background:#fef2f2}
.asin-card .ac-change.flat{color:#999;background:#f5f5f5}
.asin-card .ac-metrics{display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-top:8px}
.asin-card .ac-metric{padding:5px 7px;background:#f9f9f9;border-radius:5px}
.asin-card .ac-metric .ml{font-size:9px;color:#888;font-weight:500;text-transform:uppercase}
.asin-card .ac-metric .mv{font-size:13px;font-weight:700;color:#131921}
.asin-card .ac-metric .mv.rt{color:#d99536}
.asin-card .ac-metric .mv.bsr{color:#067d62}
.asin-card .ac-badge{position:absolute;top:8px;left:8px;width:18px;height:18px;border-radius:50%;background:#e94560;color:#fff;font-size:9px;font-weight:700;display:flex;align-items:center;justify-content:center}

/* ─── Detail View (expanded card) ─── */
.detail-overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:200;display:none;align-items:center;justify-content:center;padding:20px}
.detail-overlay.open{display:flex}
.detail-panel{background:#fff;border-radius:14px;width:100%;max-width:900px;max-height:90vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.3)}
.detail-hdr{padding:16px 20px;border-bottom:1px solid #eee;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:#fff;z-index:10;border-radius:14px 14px 0 0}
.detail-hdr .dh-title{font-size:14px;font-weight:700;color:#131921}
.detail-hdr .dh-sub{font-size:11px;color:#888;margin-top:2px}
.detail-hdr .dh-close{width:32px;height:32px;border-radius:50%;background:#f5f5f5;border:none;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center}
.detail-hdr .dh-close:hover{background:#e0e0e0}
.detail-body{padding:0}
.detail-group{padding:14px 20px;border-bottom:1px solid #f0f2f2}
.detail-group:last-child{border-bottom:none}
.detail-group.main-g{background:#fffbe6}
.detail-group .dg-name{display:flex;align-items:center;gap:8px;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #eee;flex-wrap:wrap}
.detail-group .dg-name .asinh{font-size:12px;font-weight:700;color:#007185}
.detail-group .dg-name .asintitle{font-size:10px;color:#888;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:100px}
.detail-metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-bottom:10px}
.dm{background:#f9f9f9;border-radius:8px;padding:8px 10px;text-align:center}
.dm .dml{font-size:9px;color:#888;font-weight:600;text-transform:uppercase;margin-bottom:3px}
.dm .dmv{font-size:15px;font-weight:800;color:#131921;word-break:break-all}
.dm .dmv.pc{color:#B12704}.dm .dmv.rt{color:#d99536}.dm .dmv.bsr{color:#067d62}
.detail-chart-wrap{padding:0 4px;height:120px}
.detail-chart-wrap canvas{max-height:120px!important}
.detail-history{margin-top:8px;font-size:10px;color:#aaa;text-align:right}

/* Loading / empty */
.loading{text-align:center;padding:40px;color:#999;font-size:13px}
.err-wrap{text-align:center;padding:40px;color:#555;font-size:13px}
.err-wrap .btn{margin-top:14px;padding:8px 20px;font-size:13px;border-radius:20px}

@media(max-width:768px){
  .board{grid-template-columns:repeat(auto-fill,minmax(180px,1fr))}
  .detail-metrics{grid-template-columns:repeat(3,1fr)}
}
"""

HTML_PROLOG = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CrossMart Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7"></script>
<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
<style>
%(CSS)s
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

<div class="filters">
  <input type="text" id="sf" placeholder="&#x1F50D; Search ASIN or title..." oninput="render()">
  <select id="ss" onchange="render()">
    <option value="bsr">BSR &#x2B06;</option>
    <option value="price_chg">Price Change</option>
    <option value="bsr_chg">BSR Change</option>
    <option value="price">Price &#x2B07;</option>
  </select>
  <label><input type="checkbox" id="sc" onchange="render()"> Changes only</label>
  <button class="btn btn-sm" onclick="refresh()">&#x1F504; Refresh</button>
  <button class="btn btn-sm btn-p" onclick="exportXlsx()">&#x1F4E5; Export Excel</button>
</div>

<div id="board" class="board"><div class="loading">&#x231B; Loading...</div></div>

<div id="detail" class="detail-overlay" onclick="if(event.target===this)closeDetail()">
  <div class="detail-panel">
    <div class="detail-hdr">
      <div>
        <div class="dh-title" id="dtTitle">ASIN Detail</div>
        <div class="dh-sub" id="dtSub"></div>
      </div>
      <button class="dh-close" onclick="closeDetail()">&#x2715;</button>
    </div>
    <div id="dtBody" class="detail-body"></div>
  </div>
</div>

<script>
window.MONITOR_EMBED = __DATA__;
</script>
</body>
</html>"""

JS = """
/* global MONITOR_EMBED, Chart, XLSX */
var _data = null;
var _charts = {};

function initMonitor(data) {
  _data = data;
  render();
}

function refresh() {
  initMonitor(window.MONITOR_EMBED || {});
}

function render() {
  var board = document.getElementById('board');
  if (!_data || !_data.groups) {
    board.innerHTML = '<div class="loading">No data. Run sync_groups.py first.</div>';
    return;
  }
  var groups = _data.groups || [];
  var totalUp = 0, totalDn = 0;
  var allAsins = [];
  groups.forEach(function(g){
    g.members.forEach(function(m){
      var c = getChange(m);
      if(c>0) totalUp++; else if(c<0) totalDn++;
      allAsins.push(m);
    });
  });

  var lastUpd = _data.updated || '';
  var html = '<div class="summary-card" onclick="openSummaryDetail()">' +
    '<div class="sc-badge">SUMMARY</div>' +
    '<div class="sc-title">All Monitored ASINs</div>' +
    '<div class="sc-num">' + allAsins.length + '</div>' +
    '<div class="sc-meta">Updated: ' + lastUpd + '</div>' +
    '<div class="sc-icons">' +
    '<div class="sc-icon"><div class="dot up"></div>Up ' + totalUp + '</div>' +
    '<div class="sc-icon"><div class="dot dn"></div>Down ' + totalDn + '</div>' +
    '</div></div>\n';

  groups.forEach(function(g, gi) {
    var main = g.members[0] || {};
    var ch = getChange(main);
    var chClass = ch > 0 ? 'up' : ch < 0 ? 'dn' : 'flat';
    var chTxt = ch === 0 ? '0' : (ch > 0 ? '+' + ch : String(ch));
    var price = main.price ? '$' + main.price.toFixed(2) : '---';
    var bsr = main.bsr ? '#' + main.bsr.toLocaleString() : '---';
    var rating = main.rating || '---';
    var reviews = main.review_count ? main.review_count.toLocaleString() : '---';
    var imgPH = '<div class="ph">&#128722;</div>';
    var imgHTML = main.main_image
      ? '<img src="' + main.main_image + '">'
      : imgPH;

    html += '<div class="asin-card" data-gi="' + gi + '" onclick="openDetail(' + gi + ')">' +
      '<div class="ac-badge">' + g.members.length + '</div>' +
      '<div class="ac-top">' +
      '<div class="ac-img">' + imgHTML + '</div>' +
      '<div class="ac-info">' +
      '<div class="ac-asin">' + (main.asin||'') + '</div>' +
      '<div class="ac-title">' + e(main.title||'') + '</div>' +
      '<div class="ac-brand">' + e(main.brand||'') + '</div>' +
      '</div></div>' +
      '<div class="ac-price-row">' +
      '<span class="ac-price">' + price + '</span>' +
      (main.list_price ? '<span class="ac-list">$' + main.list_price.toFixed(2) + '</span>' : '') +
      '<span class="ac-change ' + chClass + '">' + chTxt + '</span>' +
      '</div>' +
      '<div class="ac-metrics">' +
      '<div class="ac-metric"><div class="ml">BSR</div><div class="mv bsr">' + bsr + '</div></div>' +
      '<div class="ac-metric"><div class="ml">Rating</div><div class="mv rt">&#9733; ' + rating + '</div></div>' +
      '<div class="ac-metric"><div class="ml">Reviews</div><div class="mv">' + reviews + '</div></div>' +
      '<div class="ac-metric"><div class="ml">Seller</div><div class="mv" style="font-size:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + e(main.seller||'---') + '</div></div>' +
      '</div></div>\n';
  });

  board.innerHTML = html;
}

function openDetail(gi) {
  var g = _data && _data.groups ? _data.groups[gi] : null;
  if (!g) return;
  document.getElementById('dtTitle').textContent = 'Group: ' + (g.main_asin||'');
  document.getElementById('dtSub').textContent = g.members.length + ' ASINs in group';
  var html = '';
  g.members.forEach(function(m) {
    var ch = getChange(m);
    var chClass = ch > 0 ? 'up' : ch < 0 ? 'dn' : 'flat';
    var chTxt = ch === 0 ? 'stable' : (ch > 0 ? '+' + ch : String(ch));
    var price = m.price ? '$' + m.price.toFixed(2) : '---';
    var bsr = m.bsr ? '#' + m.bsr.toLocaleString() : '---';
    var bsrSub = m.bsr_sub_rank ? '#' + m.bsr_sub_rank.toLocaleString() : '';
    var rating = m.rating || '---';
    var reviews = m.review_count ? m.review_count.toLocaleString() : '---';
    var isMain = m.asin === g.main_asin;
    var lastTs = getLastTs(m);

    html += '<div class="detail-group' + (isMain ? ' main-g' : '') + '">';
    html += '<div class="dg-name">';
    html += '<span class="asinh">' + (isMain ? '&#9733; ' : '') + (m.asin||'') + '</span>';
    html += '<span class="asintitle">' + e(m.title||'') + '</span>';
    html += '<span class="ac-change ' + chClass + '" style="margin-left:auto">' + chTxt + '</span>';
    html += '</div>';
    html += '<div class="detail-metrics">';
    html += '<div class="dm"><div class="dml">Price</div><div class="dmv pc">' + price + '</div></div>';
    html += '<div class="dm"><div class="dml">BSR</div><div class="dmv bsr">' + bsr + '</div></div>';
    html += '<div class="dm"><div class="dml">Sub BSR</div><div class="dmv" style="font-size:12px">' + bsrSub + '</div></div>';
    html += '<div class="dm"><div class="dml">Rating</div><div class="dmv rt">&#9733; ' + rating + '</div></div>';
    html += '<div class="dm"><div class="dml">Reviews</div><div class="dmv">' + reviews + '</div></div>';
    html += '</div>';
    if (m.bsr_sub_category) {
      html += '<div style="font-size:9px;color:#888;margin-bottom:8px">' + e(m.bsr_sub_category) + '</div>';
    }
    html += '<div class="detail-chart-wrap"><canvas id="c_' + (m.asin||'') + '"></canvas></div>';
    if (lastTs) html += '<div class="detail-history">Last updated: ' + lastTs + '</div>';
    html += '</div>';
  });
  document.getElementById('dtBody').innerHTML = html;
  document.getElementById('detail').classList.add('open');
  setTimeout(function() {
    g.members.forEach(function(m) { drawSparkline('c_' + (m.asin||''), m.history||[]); });
  }, 60);
}

function openSummaryDetail() {
  if (!_data || !_data.groups) return;
  document.getElementById('dtTitle').textContent = 'All Monitored ASINs';
  var all = [];
  _data.groups.forEach(function(g){ g.members.forEach(function(m){ all.push(m); }); });
  document.getElementById('dtSub').textContent = all.length + ' ASINs across ' + _data.groups.length + ' groups';
  var html = '';
  all.forEach(function(m) {
    var ch = getChange(m);
    var chClass = ch > 0 ? 'up' : ch < 0 ? 'dn' : 'flat';
    var chTxt = ch === 0 ? 'stable' : (ch > 0 ? '+' + ch : String(ch));
    var price = m.price ? '$' + m.price.toFixed(2) : '---';
    var bsr = m.bsr ? '#' + m.bsr.toLocaleString() : '---';
    var rating = m.rating || '---';
    var reviews = m.review_count ? m.review_count.toLocaleString() : '---';
    var imgHTML = m.main_image ? '<img src="' + m.main_image + '" style="width:32px;height:32px;border-radius:4px;object-fit:cover;margin-right:8px;flex-shrink:0">' : '';

    html += '<div class="detail-group">';
    html += '<div class="dg-name" style="align-items:center">';
    html += imgHTML;
    html += '<span class="asinh">' + (m.asin||'') + '</span>';
    html += '<span class="asintitle">' + e(m.title||'') + '</span>';
    html += '<span class="ac-change ' + chClass + '" style="margin-left:auto">' + chTxt + '</span>';
    html += '</div>';
    html += '<div class="detail-metrics">';
    html += '<div class="dm"><div class="dml">Price</div><div class="dmv pc">' + price + '</div></div>';
    html += '<div class="dm"><div class="dml">BSR</div><div class="dmv bsr">' + bsr + '</div></div>';
    html += '<div class="dm"><div class="dml">Rating</div><div class="dmv rt">&#9733; ' + rating + '</div></div>';
    html += '<div class="dm"><div class="dml">Reviews</div><div class="dmv">' + reviews + '</div></div>';
    html += '<div class="dm"><div class="dml">Seller</div><div class="dmv" style="font-size:10px">' + e(m.seller||'---') + '</div></div>';
    html += '</div>';
    html += '<div class="detail-chart-wrap"><canvas id="cs_' + (m.asin||'') + '"></canvas></div>';
    html += '</div>';
  });
  document.getElementById('dtBody').innerHTML = html;
  document.getElementById('detail').classList.add('open');
  setTimeout(function() {
    all.forEach(function(m){ drawSparkline('cs_' + (m.asin||''), m.history||[]); });
  }, 60);
}

function closeDetail() {
  document.getElementById('detail').classList.remove('open');
  Object.keys(_charts).forEach(function(k){ if(_charts[k]){ _charts[k].destroy(); _charts[k]=null; } });
}

function drawSparkline(cid, history) {
  var canvas = document.getElementById(cid);
  if (!canvas) return;
  if (_charts[cid]) { _charts[cid].destroy(); _charts[cid] = null; }
  var prices = [], bsrData = [];
  history.forEach(function(h) {
    if (h.price != null) prices.push(h.price);
    if (h.bsr != null) bsrData.push(h.bsr);
  });
  if (!prices.length && !bsrData.length) return;
  var datasets = [];
  if (prices.length > 1) {
    datasets.push({ label:'Price', data:prices, borderColor:'#B12704', backgroundColor:'rgba(177,39,4,.04)', borderWidth:1.5, fill:true, tension:0.3, pointRadius:0, yAxisID:'y' });
  }
  if (bsrData.length > 1) {
    datasets.push({ label:'BSR', data:bsrData, borderColor:'#067d62', backgroundColor:'transparent', borderWidth:1.5, fill:false, tension:0.3, pointRadius:0, yAxisID:'y1' });
  }
  _charts[cid] = new Chart(canvas, {
    type:'line',
    data:{ labels:history.map(function(){return '';}), datasets:datasets },
    options:{
      responsive:true, maintainAspectRatio:false, animation:false,
      plugins:{ legend:{display:false}, tooltip:{enabled:false} },
      scales:{
        x:{display:false},
        y:{position:'left', grid:{color:'rgba(0,0,0,.05)'}, ticks:{font:{size:9}, maxTicksLimit:3}},
        y1:{position:'right', grid:{display:false}, ticks:{font:{size:9}, maxTicksLimit:3}}
      }
    }
  });
}

function getChange(member) {
  var h = member.history || [];
  if (h.length < 2) return 0;
  var p1 = null, p2 = null;
  for (var i = h.length - 1; i >= 0; i--) {
    if (h[i].price != null && p1 === null) p1 = h[i].price;
    else if (h[i].price != null && p2 === null) { p2 = h[i].price; break; }
  }
  if (p1 == null || p2 == null) return 0;
  return Math.round((p1 - p2) * 100) / 100;
}

function getLastTs(member) {
  var h = member.history || [];
  for (var i = h.length - 1; i >= 0; i--) {
    if (h[i].price != null || h[i].bsr != null) return h[i].timestamp || '';
  }
  return '';
}

function e(s) {
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function exportXlsx() {
  if (!_data || !_data.groups) return;
  var wb = XLSX.utils.book_new();
  var rows = [['ASIN','Title','Brand','Price','List Price','Rating','Reviews','BSR','BSR Sub Rank','Category','Seller','Price Change','Last Updated']];
  _data.groups.forEach(function(g) {
    g.members.forEach(function(m) {
      var ch = getChange(m);
      rows.push([
        m.asin||'', (m.title||'').substring(0,80), m.brand||'',
        m.price||'', m.list_price||'', m.rating||'',
        m.review_count||'', m.bsr||'', m.bsr_sub_rank||'',
        (m.bsr_sub_category||'').substring(0,60), m.seller||'',
        ch, getLastTs(m)
      ]);
    });
  });
  var ws = XLSX.utils.aoa_to_sheet(rows);
  ws['!cols'] = [{wch:14},{wch:50},{wch:20},{wch:8},{wch:10},{wch:8},{wch:10},{wch:10},{wch:12},{wch:25},{wch:20},{wch:8},{wch:20}];
  XLSX.utils.book_append_sheet(wb, ws, 'Monitor Data');
  XLSX.writeFile(wb, 'crossmart_monitor_' + new Date().toISOString().substring(0,10) + '.xlsx');
}

initMonitor(window.MONITOR_EMBED || {});
"""

with open(DATA, 'r', encoding='utf-8') as f:
    raw_data = f.read()

# Escape any </script> sequences in data to prevent premature script closure
safe_data = raw_data.replace('</script>', '<\\/script>')

html = (HTML_PROLOG % {'CSS': CSS}).replace('__DATA__', safe_data) + '\n<script>\n' + JS + '\n</script>'

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)

print('Written:', OUT)