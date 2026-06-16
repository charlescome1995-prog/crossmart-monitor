(function() {
  var REPO = 'charlescome1995-prog/crossmart-monitor';
  var RAW_DATA_URL = 'https://raw.githubusercontent.com/' + REPO + '/main/frontend/data/rawData.json';
  var rawData = { updated: '', items: [], keywords: [] };
  var userConfiguredAsins = new Set();

  window.addEventListener('DOMContentLoaded', function() {
    var saved = localStorage.getItem('gh_token') || '';
    var ti = document.getElementById('ghTokenInput');
    if (ti && saved) ti.value = saved;
    loadGitHubConfig();
    loadRawData();
  });

  function loadGitHubConfig() {
    var se = document.getElementById('configStatus');
    fetch('https://raw.githubusercontent.com/' + REPO + '/main/backend/data/user_config.json?v=' + Date.now())
      .then(function(r) { if (!r.ok) throw new Error('Config not found'); return r.json(); })
      .then(function(cfg) {
        applyConfig(cfg);
        se.textContent = '配置加载成功';
        se.style.background = '#d1fae5';
        se.style.color = '#065f46';
      })
      .catch(function() {
        // silent fail, use defaults
      });
  }

  function applyConfig(cfg) {
    if (cfg && cfg.asins) {
      cfg.asins.forEach(function(row, i) {
        if (i < 5) {
          var mainEl = document.getElementById('in-asin-' + i);
          if (mainEl && row.main) {
            mainEl.value = row.main;
            userConfiguredAsins.add(row.main);
          }
          if (row.related) {
            row.related.forEach(function(val, ri) {
              if (ri < 5) {
                var relEl = document.getElementById('rel-asin-' + i + '-' + ri);
                if (relEl) {
                  relEl.value = val;
                  userConfiguredAsins.add(val);
                }
              }
            });
          }
        }
      });
    }
    if (cfg && cfg.keywords) {
      cfg.keywords.forEach(function(row, i) {
        if (i < 5) {
          var kwEl = document.getElementById('in-kw-' + i);
          if (kwEl && row.main) kwEl.value = row.main;
          if (row.related) {
            row.related.forEach(function(val, ri) {
              if (ri < 5) {
                var relEl = document.getElementById('rel-kw-' + i + '-' + ri);
                if (relEl) relEl.value = val;
              }
            });
          }
        }
      });
    }
  }

  function loadRawData() {
    var se = document.getElementById('configStatus');
    se.textContent = '加载中...';
    se.style.background = '#fef3c7';
    se.style.color = '#92400e';
    fetch(RAW_DATA_URL + '?t=' + Date.now())
      .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function(d) {
        rawData = d;
        renderTable();
        highlightTimeCell();
        se.textContent = '数据加载成功';
        se.style.background = '#d1fae5';
        se.style.color = '#065f46';
      })
      .catch(function(e) {
        console.warn(e);
        se.textContent = '加载失败';
        se.style.background = '#fee2e2';
        se.style.color = '#991b1b';
        renderTable();
        highlightTimeCell();
      });
  }

  function saveToken() {
    var ti = document.getElementById('ghTokenInput');
    var t = ti ? ti.value.trim() : '';
    if (!t) { alert('请输入 GitHub Token'); return; }
    localStorage.setItem('gh_token', t);
    alert('Token saved to browser. If api_server.py does not receive trigger, restart it in PowerShell with: $env:GH_TOKEN = your_token');
    loadRawData();
  }


  function getRelatedVals(type, streamIdx) {
    var vals = [];
    for (var r = 0; r < 5; r++) {
      var el = document.getElementById('rel-' + type + '-' + streamIdx + '-' + r);
      if (el && el.value.trim()) vals.push(el.value.trim());
    }
    return vals;
  }

  
  function triggerMonitor() {
    var btn = document.getElementById('btnTrigger');
    var se = document.getElementById('configStatus');
    var token = (document.getElementById('ghTokenInput') || {}).value.trim();
    if (!token) {
      alert('请先输入 GitHub Token'); return;
    }
    btn.disabled = true;
    btn.textContent = '\u89e6\u53d1\u4e2d...';
    se.textContent = '\u6b63\u5728\u5199\u5165\u914d\u7f6e...';
    se.style.background = '#fef3c7';
    se.style.color = '#92400e';

    var asins = [], kws = [];
    for (var i = 0; i < 5; i++) {
      var mainA = (document.getElementById('in-asin-' + i) || {}).value || '';
      if (mainA.trim()) asins.push({ main: mainA.trim(), related: getRelatedVals('asin', i) });
    }
    for (var j = 0; j < 5; j++) {
      var mainK = (document.getElementById('in-kw-' + j) || {}).value || '';
      if (mainK.trim()) kws.push({ main: mainK.trim(), related: getRelatedVals('kw', j) });
    }
    var cfg = { asins: asins, keywords: kws };
    var trigger = { status: 'pending', triggered_at: new Date().toISOString(), progress: '' };


    putFile('backend/data/user_config.json', cfg, token)
      .then(function() { return putFile('backend/data/trigger.json', trigger, token); })
      .then(function() {
        se.textContent = '\u5df2\u5199\u5165 GitHub\uff0c\u7b49\u5f85\u672c\u5730\u811a\u672c\u54cd\u5e94...';
        se.style.background = '#dbeafe';
        se.style.color = '#1e40af';
        btn.textContent = '\u8f6e\u8be2\u4e2d';
        pollStatus(token);
      })
      .catch(function(e) {
        se.textContent = 'GitHub \u5199\u5165\u5931\u8d25: ' + e;
        se.style.background = '#fee2e2';
        se.style.color = '#991b1b';
        btn.disabled = false;
        btn.textContent = '\u7acb\u5373\u62e8\u53d6';
      });
  }

  function saveConfig() {
    var btn = document.getElementById('btnSaveConfig');
    var se = document.getElementById('configStatus');
    var token = (document.getElementById('ghTokenInput') || {}).value.trim();
    if (!token) { alert('请先输入 GitHub Token'); return; }
    btn.disabled = true;
    se.textContent = '\u6b63\u5728\u4fdd\u5b58...';
    se.style.background = '#fef3c7';
    se.style.color = '#92400e';

    var asins = [], kws = [];
    for (var i = 0; i < 5; i++) {
      var mainA = (document.getElementById('in-asin-' + i) || {}).value || '';
      if (mainA.trim()) asins.push({ main: mainA.trim(), related: getRelatedVals('asin', i) });
    }
    for (var j = 0; j < 5; j++) {
      var mainK = (document.getElementById('in-kw-' + j) || {}).value || '';
      if (mainK.trim()) kws.push({ main: mainK.trim(), related: getRelatedVals('kw', j) });
    }
    var cfg = { asins: asins, keywords: kws };
    putFile('backend/data/user_config.json', cfg, token)
      .then(function() {
        se.textContent = '\u5df2\u4fdd\u5b58\u5e76\u63a8\u9001\u5230\u4e91\u7aef';
        se.style.background = '#d1fae5';
        se.style.color = '#065f46';
        btn.disabled = false;
      })
      .catch(function(e) {
        se.textContent = '\u4fdd\u5b58\u5931\u8d25: ' + e;
        se.style.background = '#fee2e2';
        se.style.color = '#991b1b';
        btn.disabled = false;
      });
  }

  var pollTimer = null;
  function pollStatus(token) {
    if (pollTimer) clearTimeout(pollTimer);
    fetch('https://raw.githubusercontent.com/' + REPO + '/main/backend/data/trigger.json?t=' + Date.now())
      .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function(data) {
        var se = document.getElementById('configStatus');
        var btn = document.getElementById('btnTrigger');
        if (data.status === 'pending') {
          se.textContent = '\u8f6e\u8be2\u4e2d... ' + (data.progress || '');
          se.style.background = '#dbeafe';
          se.style.color = '#1e40af';
          btn.textContent = '\u8f6e\u8be2\u4e2d';
          pollTimer = setTimeout(function() { pollStatus(token); }, 30000);
        } else {
          se.textContent = '\u6570\u636e\u5df2\u66f4\u65b0\uff0c\u5237\u65b0\u9875\u9762';
          se.style.background = '#d1fae5';
          se.style.color = '#065f46';
          btn.textContent = '\u5df2\u5b8c\u6210';
          btn.disabled = false;
          loadRawData();
        }
      })
      .catch(function() {
        var se = document.getElementById('configStatus');
        se.textContent = '\u7b49\u5f85\u4e91\u7aef\u54cd\u5e94... (30s)';
        pollTimer = setTimeout(function() { pollStatus(token); }, 30000);
      });
  }


  function b64enc(str) {
    return btoa(unescape(encodeURIComponent(str)));
  }

  function putFile(path, content, token, retryCount) {
    var url = 'https://api.github.com/repos/' + REPO + '/contents/' + path;
    return fetch(url, { headers: { 'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github.v3+json' } })
      .then(function(r) { return r.ok ? r.json() : {}; })
      .then(function(d) {
        return fetch(url, {
          method: 'PUT',
          headers: { 'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: 'user: trigger capture', content: b64enc(JSON.stringify(content)), sha: d.sha || '' })
        });
      })
      .then(function(r) {
        if (!r.ok) {
          if (r.status === 409 && (!retryCount || retryCount < 1)) {
            return putFile(path, content, token, 1);
          }
          throw new Error('API ' + r.status);
        }
      });
  }

  function putFiles(files, token) {
    // files: [{path, content}, ...] — 并行 PUT（两次 PUT 同时发出）
    var API = 'https://api.github.com/repos/' + REPO + '/contents/';
    return Promise.all(files.map(function(f) {
      return fetch(API + f.path, { headers: { 'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github.v3+json' } })
        .then(function(r) { return r.json(); })
        .then(function(d) { f.sha = d.sha || ''; return f; });
    }))
    .then(function(filesWithSha) {
      return Promise.all(filesWithSha.map(function(f) {
        return fetch(API + f.path, {
          method: 'PUT',
          headers: { 'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: 'user: trigger capture', content: b64enc(JSON.stringify(f.content)), sha: f.sha })
        }).then(function(r) { if (!r.ok) throw new Error('API ' + r.status); });
      }));
    });
  }

  function renderTable() {
    var tb = document.getElementById('tableBody');
    if (!tb || !rawData.items) { tb.innerHTML = '<tr><td colspan="15" style="text-align:center;padding:20px;">暂无数据</td></tr>'; return; }
    var searchTxt = (document.getElementById('searchInput') || {}).value || '';
    var sourceFilter = (document.getElementById('sourceFilter') || {}).value || 'ALL';
    var onlyChg = (document.getElementById('changeFilter') || {}).checked || false;
    searchTxt = searchTxt.toLowerCase();
    var html = '';
    rawData.items.forEach(function(item) {
      if (userConfiguredAsins.size > 0 && !userConfiguredAsins.has(item.asin)) return;
      var isStatusAnomaly = item.listing_status !== item.expected_listing_status;
      var isCatAnomaly = item.main_cat !== item.expected_main_cat || item.sub_cat !== item.expected_sub_cat;
      var isInfoAnomaly = item.title_changed || item.img_changed || item.bullets_changed || item.description_changed;
      var isVariantAnomaly = item.variant_changed;
      var hasActiveAnomaly = item.chg !== 0 || isStatusAnomaly || isCatAnomaly || isInfoAnomaly || isVariantAnomaly || (item.badges_lost && item.badges_lost.length > 0);
      if (sourceFilter === 'ASIN' && item.source_keyword) return;
      if (sourceFilter === 'KW' && !item.source_keyword) return;
      if (searchTxt && !item.asin.toLowerCase().includes(searchTxt) && !(item.title && item.title.toLowerCase().includes(searchTxt))) return;
      if (onlyChg && !hasActiveAnomaly) return;
      // 显示所有 monitor_type（包括 KW 关键词ASIN）
      var activeEvents = (item.events || []).slice();
      if (isStatusAnomaly) activeEvents.push({ cls: 'e-alert', txt: '商品状态异常' });
      if (isInfoAnomaly) activeEvents.push({ cls: 'e-alert', txt: '商品信息变化' });
      if (isCatAnomaly) activeEvents.push({ cls: 'e-alert', txt: '分类异常' });
      if (item.badges_lost && item.badges_lost.length) item.badges_lost.forEach(function(b) { activeEvents.push({ cls: 'e-alert', txt: '丢失: ' + b }); });
      var chgClass = item.chg > 0 ? 'up' : (item.chg < 0 ? 'dn' : '');
      var chgText = item.chg !== 0 ? (item.chg > 0 ? '\u25B2 $' + Math.abs(item.chg) : '\u25BC $' + Math.abs(item.chg)) : '';
      var diff = item.diff || {};
      var diffHtml = buildDiffHtml(diff);
      var eventsHtml = activeEvents.length ? activeEvents.map(function(e) { return '<span class="e-tag ' + e.cls + '">' + e.txt + '</span>'; }).join('') : '<span class="e-none">无事件</span>';
      var priceStr = item.price != null ? '$' + item.price : '-';
      var ratingStr = item.rating != null ? item.rating : '-';
      var reviewsStr = item.reviews != null ? item.reviews : '-';
      var mainBsrStr = item.main_bsr != null ? '#' + item.main_bsr : '-';
      var subBsrStr = item.sub_bsr != null ? ' / #' + item.sub_bsr : '';
      var variantHtml = item.variant_status && item.variant_status !== '正常' ? ' <span style="color:#d97706;font-size:12px;">变体:' + item.variant_status + '</span>' : '';
      var statusClass = hasActiveAnomaly ? 'changed' : 'stable';
      var statusText = hasActiveAnomaly ? '有变化' : '正常';
      var badgeHtml = (item.badges_current && item.badges_current.length) ? '<div style="margin-top:3px">' + item.badges_current.map(function(b) { return '<span style="background:#fef3c7;color:#d97706;font-size:10px;padding:1px 5px;border-radius:3px;margin-right:3px;font-weight:700;">' + b + '</span>'; }).join('') + '</div>' : '';
      var dealHtml = item.deal_activity && item.deal_activity !== '\u65e0' ? '<div style="color:#d97706;font-size:12px;">Deal: ' + item.deal_activity + '</div>' : '';
      var couponHtml = item.coupon && item.coupon !== '\u65e0' ? '<div style="color:#059669;font-size:12px;">代金券: ' + item.coupon + '</div>' : '';
      var primeHtml = item.prime_discount && item.prime_discount !== '\u672a\u5f00\u542f' ? '<div style="color:#7c3aed;font-size:12px;">Prime: ' + item.prime_discount + '</div>' : '';
      var badge1Text = item.source_keyword ? ('KW-' + item.source_keyword) : (item.monitor_type === 'KW' ? 'KW' : 'ASIN');
      // badge2 仅主ASIN和关联竞品显示；关键词ASIN的monitor_type本身就是KW，无需重复
      var badge2Text = item.source_keyword ? '\u5173\u952e\u8bcd\u7ade\u54c1' : (item.logic_type || '');
      html += '<tr>' +
        '<td class="col-img"><img src="' + (item.img || '') + '"></td>' +
        '<td class="col-info"><div class="info-block">' +
          '<div><span class="badge ' + (item.source_keyword ? 'source-kw' : 'source-asin') + '">' + badge1Text + '</span>' + (badge2Text ? ' <span class="badge ' + (item.is_main ? 'main' : 'rel') + '">' + badge2Text + '</span>' : '') + '</div>' +
          '<div><a href="https://www.amazon.com/dp/' + (item.asin || '') + '" target="_blank" class="asin-link">' + (item.asin || '') + '</a> [' + (item.brand || '') + ']</div>' +
          '<div class="title-text" title="' + (item.title || '') + '">' + (item.title || '') + '</div>' +
          badgeHtml + dealHtml + couponHtml + primeHtml + variantHtml +
        '</div></td>' +
        '<td class="col-metrics"><div class="metrics-block">' +
          '<div>价格: <strong>' + priceStr + '</strong>' + (diff.price ? ' <span class="diff-arrow ' + diff.price.direction + '">' + (diff.price.direction === 'up' ? '\u2191' : (diff.price.direction === 'dn' ? '\u2193' : '\u2014')) + '</span> <span class="diff-val ' + diff.price.direction + '">' + diff.price.change + '</span>' : '') + '<span class="sparkline-wrap"><canvas id="sp_' + item.asin + '_price"></canvas></span></div>' +
          '<div>评分: <strong>' + ratingStr + '</strong>' + (diff.rating ? ' <span class="diff-arrow ' + diff.rating.direction + '">' + (diff.rating.direction === 'up' ? '\u2191' : (diff.rating.direction === 'dn' ? '\u2193' : '\u2014')) + '</span> <span class="diff-val ' + diff.rating.direction + '">' + diff.rating.change + '</span>' : '') + ' <span style="color:#64748b;font-size:12px;">评论 ' + reviewsStr + '</span></div>' +
          '<div>大类: <span class="cat-item">' + (item.main_cat || '-') + '</span> <strong>' + mainBsrStr + '</strong>' + (diff.bsr ? ' <span class="diff-arrow ' + diff.bsr.direction + '">' + (diff.bsr.direction === 'up' ? '\u2191' : (diff.bsr.direction === 'dn' ? '\u2193' : '\u2014')) + '</span> <span class="diff-val ' + diff.bsr.direction + '">' + diff.bsr.change + '</span>' : '') + '<span class="sparkline-wrap"><canvas id="sp_' + item.asin + '_main_bsr"></canvas></span></div>' +
          '<div>小类: <span class="cat-item">' + (item.sub_cat || '-') + '</span> <strong>' + (item.sub_bsr != null ? '#' + item.sub_bsr : '-') + '</strong>' + (diff.sub_bsr ? ' <span class="diff-arrow ' + diff.sub_bsr.direction + '">' + (diff.sub_bsr.direction === 'up' ? '\u2191' : (diff.sub_bsr.direction === 'dn' ? '\u2193' : '\u2014')) + '</span> <span class="diff-val ' + diff.sub_bsr.direction + '">' + diff.sub_bsr.change + '</span>' : '') + '<span class="sparkline-wrap"><canvas id="sp_' + item.asin + '_sub_bsr"></canvas></span></div>' +
        '</div></td>' +
        '<td class="col-jike">' +
          (item.is_main ? (
            '<div style="font-size:12px;line-height:1.4;">销量 <strong>' + (item.jike_units != null ? item.jike_units.toLocaleString() : '-') + '</strong></div>' +
            '<div style="font-size:11px;color:#64748b;line-height:1.4;">销售额 $' + (item.jike_sales != null ? item.jike_sales.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '-') + '</div>' +
            '<div style="font-size:11px;color:#64748b;line-height:1.4;">毛利率 ' + (item.jike_gross_profit_rate != null ? item.jike_gross_profit_rate + '%' : '-') + '</div>' +
            '<div style="font-size:11px;line-height:1.4;">ACOS ' + (item.jike_acos != null ? item.jike_acos + '%' : '-') + '</div>' +
            '<div style="font-size:11px;color:#64748b;line-height:1.4;">广告费 $' + (item.jike_ads_spend != null ? item.jike_ads_spend.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '-') + '</div>' +
            '<div style="font-size:11px;line-height:1.4;">FBA库存 ' + (item.jike_fba_quantity != null ? item.jike_fba_quantity.toLocaleString() : '-') + '</div>' +
            '<div style="font-size:11px;color:#64748b;line-height:1.4;">周转 ' + (item.jike_fba_turnover != null ? item.jike_fba_turnover.toFixed(1) : '-') + '</div>'
          ) : '<span style="color:#cbd5e1;font-size:11px;">-</span>') +
        '</td>' +
        '<td class="col-plugin-l">' +
          (item.lqs ? '<div><strong>LQS</strong> ' + item.lqs + '</div>' : '') +
          (item.variant_count ? '<div><strong>变体</strong> ' + item.variant_count + '</div>' : '') +
        '</td>' +
        '<td class="col-plugin-m">' +
          (item.natural_keywords ? '<div>自然 <strong>' + item.natural_keywords + '</strong></div>' : '') +
          (item.ad_keywords ? '<div>广告 <strong>' + item.ad_keywords + '</strong></div>' : '') +
          (item.suggest_keywords ? '<div>推荐 <strong>' + item.suggest_keywords + '</strong></div>' : '') +
        '</td>' +
        '<td class="col-plugin-r">' +
          (item.traffic_keywords_top && item.traffic_keywords_top.length ?
            item.traffic_keywords_top.slice(0, 4).map(function(kw) {
              return '<div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="' + kw.keyword + ' (' + (kw.type||'') + ')">' +
                kw.keyword + ' <span style="color:#7c3aed;">' + (kw.traffic_pct || '') + '</span></div>';
            }).join('')
          : '<span style="color:#cbd5e1;">-</span>') +
        '</td>' +
        '<td class="col-time"><div>' + (rawData.updated || '-') + '</div>' +
          (item.launch_date ? '<div style="margin-top:4px;color:#64748b;">上架 ' + item.launch_date + '</div>' : '') +
          (eventsHtml && eventsHtml.indexOf('e-none') === -1 ? '<div style="margin-top:4px;">' + eventsHtml + '</div>' : '') + '</td>' +
      '</tr>';
    });
    tb.innerHTML = html || '<tr><td colspan="15" style="text-align:center;padding:20px;">没有匹配数据</td></tr>';
    // Draw sparklines for each item with history data
    rawData.items.forEach(function(item) {
      if (item.history_price && item.history_price.length > 1) {
        var c = document.getElementById('sp_' + item.asin + '_price');
        if (c) drawSparkline(c, item.history_price, item.diff && item.diff.price && item.diff.price.direction === 'dn' ? '#dc2626' : '#059669');
      }
      if (item.history_main_bsr && item.history_main_bsr.length > 1) {
        var c = document.getElementById('sp_' + item.asin + '_main_bsr');
        if (c) drawSparkline(c, item.history_main_bsr, item.diff && item.diff.bsr && item.diff.bsr.direction === 'dn' ? '#dc2626' : '#e94560');
      }
      if (item.history_sub_bsr && item.history_sub_bsr.length > 1) {
        var c = document.getElementById('sp_' + item.asin + '_sub_bsr');
        if (c) drawSparkline(c, item.history_sub_bsr, '#7c3aed');
      }
    });
  }

  // 渲染完成后检测更新时间是否异常（>12h未更新标红）
  function highlightTimeCell() {
    var tc = document.getElementById('timeCell');
    if (!tc || !rawData.updated) return;
    var msAgo = Date.now() - new Date(rawData.updated).getTime();
    var minAgo = msAgo / 60000;
    if (minAgo >= 720) {
      tc.style.color = '#dc2626';
      tc.innerHTML = '\u274c ' + rawData.updated;
    } else if (minAgo >= 30) {
      tc.style.color = '#d97706';
    } else {
      tc.style.color = '#059669';
    }
  }

  function drawSparkline(canvas, data, color) {
    if (!canvas || !data || data.length < 2) return;
    var ctx = canvas.getContext('2d');
    var w = canvas.width = 60;
    var h = canvas.height = 28;
    var min = Math.min.apply(null, data);
    var max = Math.max.apply(null, data);
    var range = max - min || 1;
    var stepX = (w - 4) / (data.length - 1);
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    data.forEach(function(v, i) {
      var x = 2 + i * stepX;
      var y = h - 2 - ((v - min) / range) * (h - 4);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  function buildDiffHtml(diff) {
    if (!diff || Object.keys(diff).length === 0) return '<span class="diff-none">-</span>';
    var rows = [];
    if (diff.price) { var dir = diff.price.direction || 'same'; var arrow = dir === 'up' ? '\u2191' : (dir === 'dn' ? '\u2193' : '-'); rows.push('<div class="diff-item"><span class="diff-arrow ' + dir + '">' + arrow + '</span> 价格: <span class="diff-val ' + dir + '">$' + diff.price.current + '</span></div>'); }
    if (diff.review_count) { var dir = diff.review_count.direction || 'same'; var arrow = dir === 'up' ? '\u2191' : (dir === 'dn' ? '\u2193' : '-'); rows.push('<div class="diff-item"><span class="diff-arrow ' + dir + '">' + arrow + '</span> 评论: <span class="diff-val ' + dir + '">' + diff.review_count.change + '</span></div>'); }
    if (diff.rating) { var dir = diff.rating.direction || 'same'; var arrow = dir === 'up' ? '\u2191' : (dir === 'dn' ? '\u2193' : '-'); rows.push('<div class="diff-item"><span class="diff-arrow ' + dir + '">' + arrow + '</span> 评分: <span class="diff-val ' + dir + '">' + diff.rating.change + '</span></div>'); }
    if (diff.bsr) { var dir = diff.bsr.direction || 'same'; var arrow = dir === 'up' ? '\u2191' : (dir === 'dn' ? '\u2193' : '-'); rows.push('<div class="diff-item"><span class="diff-arrow ' + dir + '">' + arrow + '</span> BSR: <span class="diff-val ' + dir + '">' + diff.bsr.change + '</span></div>'); }
    if (diff.sub_bsr) { var dir = diff.sub_bsr.direction || 'same'; var arrow = dir === 'up' ? '\u2191' : (dir === 'dn' ? '\u2193' : '-'); rows.push('<div class="diff-item"><span class="diff-arrow ' + dir + '">' + arrow + '</span> 小类: <span class="diff-val ' + dir + '">' + diff.sub_bsr.change + '</span></div>'); }
    return rows.join('') || '<span class="diff-none">-</span>';
  }

  function exportToExcel() {
    var rows = [['ASIN', '类型', '品牌', '监控类型', '逻辑类型', '商品状态', '价格', 'BSR', '评分', '评论数', 'LQS', '变体数', '上架日期', '总词数', '自然词数', '广告词数', '描荐词数', '销量(积加)', '销售额(积加)', '毛利率(积加)', 'ACOS(积加)', '广告费(积加)', 'FBA库存(积加)', '库存周转(积加)', '最后更新']];
    rawData.items.forEach(function(m) {
      var jikeUnits = m.jike_units != null ? m.jike_units : '-';
      var jikeSales = m.jike_sales != null ? m.jike_sales : '-';
      var jikeGrossProfit = m.jike_gross_profit_rate != null ? m.jike_gross_profit_rate + '%' : '-';
      var jikeAcos = m.jike_acos != null ? m.jike_acos + '%' : '-';
      var jikeAdsSpend = m.jike_ads_spend != null ? m.jike_ads_spend : '-';
      var jikeFbaQty = m.jike_fba_quantity != null ? m.jike_fba_quantity : '-';
      var jikeFbaTurnover = m.jike_fba_turnover != null ? m.jike_fba_turnover : '-';
      rows.push([m.asin, m.monitor_type, m.brand || '', m.monitor_type, m.logic_type, m.listing_status, m.price, m.main_bsr, m.rating, m.reviews, m.lqs || '', m.variant_count || '', m.launch_date || '', m.total_keywords || '', m.natural_keywords || '', m.ad_keywords || '', m.suggest_keywords || '', jikeUnits, jikeSales, jikeGrossProfit, jikeAcos, jikeAdsSpend, jikeFbaQty, jikeFbaTurnover, rawData.updated]);
    });
    var ws = XLSX.utils.aoa_to_sheet(rows);
    var wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Monitor');
    XLSX.writeFile(wb, 'Monitor_' + (rawData.updated || 'unknown').replace(/[: ]/g, '_') + '.xlsx');
  }

  document.getElementById('searchInput').addEventListener('input', renderTable);
  document.getElementById('sourceFilter').addEventListener('change', renderTable);
  document.getElementById('changeFilter').addEventListener('change', renderTable);
  document.getElementById('btnTrigger').addEventListener('click', triggerMonitor);
  document.getElementById('btnSaveConfig').addEventListener('click', saveConfig);
  document.getElementById('btnSaveToken').addEventListener('click', saveToken);
  document.getElementById('btnExport').addEventListener('click', exportToExcel);
})();