(function() {
  var REPO = 'charlescome1995-prog/crossmart-monitor';
  var RAW_DATA_URL = 'https://raw.githubusercontent.com/' + REPO + '/main/frontend/data/rawData.json';
  var rawData = { updated: '', items: [], keywords: [] };
  var userConfiguredAsins = new Set();

  window.addEventListener('DOMContentLoaded', function() {
    var saved = localStorage.getItem('gh_token') || '';
    var ti = document.getElementById('ghTokenInput');
    if (ti && saved) ti.value = saved;
    // 顺序加载：先加载用户配置(填主输入框) → 再加载 rawData(回填关联ASIN)
    // 避免并行竞态：rawData 先到时主输入框还是空的，backfill 会全部跳过
    loadGitHubConfig().then(function() {
      loadRawData();
    });
  });

  function loadGitHubConfig() {
    var se = document.getElementById('configStatus');
    return fetch('https://raw.githubusercontent.com/' + REPO + '/main/backend/data/user_config.json?v=' + Date.now())
      .then(function(r) { if (!r.ok) throw new Error('Config not found'); return r.json(); })
      .then(function(cfg) {
        applyConfig(cfg);
        se.textContent = 'Config loaded';
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
    se.textContent = 'Loading...';
    se.style.background = '#fef3c7';
    se.style.color = '#92400e';
    fetch(RAW_DATA_URL + '?t=' + Date.now())
      .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function(d) {
        rawData = d;
        fillMainInputsFromRawData();
        backfillRelatedFromRawData();
        renderTable();
        // highlightTimeCell removed
        se.textContent = 'Data loaded';
        se.style.background = '#d1fae5';
        se.style.color = '#065f46';
      })
      .catch(function(e) {
        console.warn(e);
        se.textContent = 'Load failed';
        se.style.background = '#fee2e2';
        se.style.color = '#991b1b';
        renderTable();
        // highlightTimeCell removed
      });
  }

  function saveToken() {
    var ti = document.getElementById('ghTokenInput');
    var t = ti ? ti.value.trim() : '';
    if (!t) { alert('Please enter GitHub Token'); return; }
    localStorage.setItem('gh_token', t);
    alert('Token saved to browser. If api_server.py does not receive trigger, restart it in PowerShell with: $env:GH_TOKEN = your_token');
    loadRawData();
  }


  function fillMainInputsFromRawData() {
    // 当 user_config.json 为空（被重置）时，从 rawData 回填主 ASIN / 关键词输入框
    // 仅填空格，不覆盖用户已有值；保证配置被重置后输入框不会空白
    if (!rawData) return;
    var items = rawData.items || [];
    var keywords = rawData.keywords || [];

    // 主 ASIN：取 items 里 is_main 的，按顺序填入空的 in-asin-i
    var mainItems = items.filter(function(it) { return it && it.is_main && it.asin; });
    var ai = 0;
    for (var i = 0; i < 5 && ai < mainItems.length; i++) {
      var mainEl = document.getElementById('in-asin-' + i);
      if (!mainEl) continue;
      if (mainEl.value.trim()) continue; // 已有值不覆盖
      // 避免重复填入已存在于其他输入框的 ASIN
      mainEl.value = mainItems[ai].asin;
      userConfiguredAsins.add(mainItems[ai].asin);
      ai++;
    }

    // 关键词：按顺序填入空的 in-kw-i
    var ki = 0;
    for (var j = 0; j < 5 && ki < keywords.length; j++) {
      var kwEl = document.getElementById('in-kw-' + j);
      if (!kwEl) continue;
      if (kwEl.value.trim()) continue;
      var kwName = keywords[ki] && keywords[ki].keyword;
      if (kwName) kwEl.value = kwName;
      ki++;
    }
  }

  function backfillRelatedFromRawData() {
    // 把系统发现的关联 ASIN 回填到输入框（仅填空格，不覆盖用户手填值）
    if (!rawData) return;
    var items = rawData.items || [];
    var keywords = rawData.keywords || [];

    // 主ASIN → 关联竞品：以 in-asin-i 为错，从 items 里找到对应主ASIN 的 related_asins
    for (var i = 0; i < 5; i++) {
      var mainEl = document.getElementById('in-asin-' + i);
      if (!mainEl || !mainEl.value.trim()) continue;
      var mainAsin = mainEl.value.trim();
      var item = null;
      for (var k = 0; k < items.length; k++) {
        if (items[k].asin === mainAsin && items[k].is_main) { item = items[k]; break; }
      }
      if (!item) continue;
      var rel = item.related_asins || [];
      for (var ri = 0; ri < 5 && ri < rel.length; ri++) {
        var relEl = document.getElementById('rel-asin-' + i + '-' + ri);
        if (relEl && !relEl.value.trim()) {
          var relAsin = typeof rel[ri] === 'string' ? rel[ri] : (rel[ri] && rel[ri].asin) || '';
          if (relAsin) relEl.value = relAsin;
        }
      }
    }

    // 关键词 → Top ASINs：以 in-kw-i 为错，从 keywords 里找到对应关键词的 top_asins
    for (var j = 0; j < 5; j++) {
      var kwEl = document.getElementById('in-kw-' + j);
      if (!kwEl || !kwEl.value.trim()) continue;
      var kwName = kwEl.value.trim();
      var kwObj = null;
      for (var m = 0; m < keywords.length; m++) {
        if (keywords[m].keyword === kwName) { kwObj = keywords[m]; break; }
      }
      if (!kwObj) continue;
      var top = kwObj.top_asins || [];
      for (var rj = 0; rj < 5 && rj < top.length; rj++) {
        var relKwEl = document.getElementById('rel-kw-' + j + '-' + rj);
        if (relKwEl && !relKwEl.value.trim()) {
          var topAsin = typeof top[rj] === 'string' ? top[rj] : (top[rj] && top[rj].asin) || '';
          if (topAsin) relKwEl.value = topAsin;
        }
      }
    }
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
      alert('Please enter GitHub Token first'); return;
    }
    btn.disabled = true;
    btn.textContent = 'Triggering...';
    se.textContent = 'Writing config...';
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
        se.textContent = 'Written to GitHub, waiting for local script...';
        se.style.background = '#dbeafe';
        se.style.color = '#1e40af';
        btn.textContent = 'Polling';
        pollStatus(token);
      })
      .catch(function(e) {
        se.textContent = 'GitHub write failed: ' + e;
        se.style.background = '#fee2e2';
        se.style.color = '#991b1b';
        btn.disabled = false;
        btn.textContent = 'Run Now';
      });
  }

  function saveConfig() {
    var btn = document.getElementById('btnSaveConfig');
    var se = document.getElementById('configStatus');
    var token = (document.getElementById('ghTokenInput') || {}).value.trim();
    if (!token) { alert('Please enter GitHub Token first'); return; }
    btn.disabled = true;
    se.textContent = 'Saving...';
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
        se.textContent = 'Saved & pushed to cloud';
        se.style.background = '#d1fae5';
        se.style.color = '#065f46';
        btn.disabled = false;
      })
      .catch(function(e) {
        se.textContent = 'Save failed: ' + e;
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
          se.textContent = 'Polling... ' + (data.progress || '');
          se.style.background = '#dbeafe';
          se.style.color = '#1e40af';
          btn.textContent = 'Polling';
          pollTimer = setTimeout(function() { pollStatus(token); }, 30000);
        } else {
          se.textContent = 'Data updated, refresh page';
          se.style.background = '#d1fae5';
          se.style.color = '#065f46';
          btn.textContent = 'Done';
          btn.disabled = false;
          loadRawData();
        }
      })
      .catch(function() {
        var se = document.getElementById('configStatus');
        se.textContent = 'Waiting for cloud response... (30s)';
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
    if (!tb || !rawData.items) { tb.innerHTML = '<tr><td colspan="15" style="text-align:center;padding:20px;">No data</td></tr>'; return; }
    var searchTxt = (document.getElementById('searchInput') || {}).value || '';
    var sourceFilter = (document.getElementById('sourceFilter') || {}).value || 'ALL';
    var onlyChg = (document.getElementById('changeFilter') || {}).checked || false;
    searchTxt = searchTxt.toLowerCase();
    var html = '';
    rawData.items.forEach(function(item) {
      // 过滤逻辑：只保留用户配置的 ASIN、其 related ASIN、以及关键词带出的 ASIN（source_keyword 不为空）
      if (userConfiguredAsins.size > 0 && !userConfiguredAsins.has(item.asin) && !item.source_keyword) return;
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
      if (isStatusAnomaly) activeEvents.push({ cls: 'e-alert', txt: 'Status Anomaly' });
      if (isInfoAnomaly) activeEvents.push({ cls: 'e-alert', txt: 'Info Changed' });
      if (isCatAnomaly) activeEvents.push({ cls: 'e-alert', txt: 'Category Anomaly' });
      if (item.badges_lost && item.badges_lost.length) item.badges_lost.forEach(function(b) { activeEvents.push({ cls: 'e-alert', txt: 'Lost: ' + b }); });
      var chgClass = item.chg > 0 ? 'up' : (item.chg < 0 ? 'dn' : '');
      var chgText = item.chg !== 0 ? (item.chg > 0 ? '\u25B2 $' + Math.abs(item.chg) : '\u25BC $' + Math.abs(item.chg)) : '';
      var diff = item.diff || {};
      var diffHtml = buildDiffHtml(diff, item);
      var eventsHtml = activeEvents.length ? activeEvents.map(function(e) { return '<span class="e-tag ' + e.cls + '">' + e.txt + '</span>'; }).join('') : '<span class="e-none">No events</span>';
      var priceStr = item.price != null ? '$' + item.price : '-';
      var ratingStr = item.rating != null ? item.rating : '-';
      var reviewsStr = item.reviews != null ? item.reviews : '-';
      var mainBsrStr = item.main_bsr != null ? '#' + item.main_bsr : '-';
      var subBsrStr = item.sub_bsr != null ? ' / #' + item.sub_bsr : '';
      var variantHtml = item.variant_status && item.variant_status !== '正常' ? ' <span style="color:#d97706;font-size:12px;">Variant:' + item.variant_status + '</span>' : '';
      var statusClass = hasActiveAnomaly || isStale || item.is_stale ? 'changed' : 'stable';
      var statusText = item.is_stale ? 'Fetch failed·kept last' : (isStale ? 'Stale' : (hasActiveAnomaly ? 'Changed' : 'Normal'));
      var isStale = rawData.updated && (Date.now() - new Date(rawData.updated).getTime()) / 60000 >= 720;
      var badgeHtml = (item.badges_current && item.badges_current.length) ? '<div style="margin-top:3px">' + item.badges_current.map(function(b) { return '<span style="background:#fef3c7;color:#d97706;font-size:10px;padding:1px 5px;border-radius:3px;margin-right:3px;font-weight:700;">' + b + '</span>'; }).join('') + '</div>' : '';
      var dealHtml = item.deal_activity && item.deal_activity !== '\u65e0' ? '<div style="color:#d97706;font-size:12px;">Deal: ' + item.deal_activity + '</div>' : '';
      var couponHtml = item.coupon && item.coupon !== '\u65e0' ? '<div style="color:#059669;font-size:12px;">Coupon: ' + item.coupon + '</div>' : '';
      var primeHtml = item.prime_discount && item.prime_discount !== '\u672a\u5f00\u542f' ? '<div style="color:#7c3aed;font-size:12px;">Prime: ' + item.prime_discount + '</div>' : '';
      var badge1Text = item.source_keyword ? ('KW-' + item.source_keyword) : (item.monitor_type === 'KW' ? 'KW' : 'ASIN');
      // badge2 仅主ASIN和关联竞品显示；关键词ASIN的monitor_type本身就是KW，无需重复
      var badge2Text = item.source_keyword ? 'KW Competitor' : (item.logic_type || '');
      html += '<tr>' +
        '<td class="col-img"><img src="' + (item.img || '') + '"></td>' +
        '<td class="col-info"><div class="info-block">' +
          '<div><span class="badge ' + (item.source_keyword ? 'source-kw' : 'source-asin') + '">' + badge1Text + '</span>' + (badge2Text ? ' <span class="badge ' + (item.is_main ? 'main' : 'rel') + '">' + badge2Text + '</span>' : '') + '</div>' +
          '<div><a href="https://www.amazon.com/dp/' + (item.asin || '') + '" target="_blank" class="asin-link">' + (item.asin || '') + '</a> [' + (item.brand || '') + ']</div>' +
          '<div class="title-text" title="' + (item.title || '') + '">' + (item.title || '') + '</div>' +
          badgeHtml + dealHtml + couponHtml + primeHtml + variantHtml +
        '</div></td>' +
        '<td class="col-metrics"><div class="metrics-block">' +
          '<div>Price: <strong>' + priceStr + '</strong>' + (diff.price ? ' <span class="diff-arrow ' + diff.price.direction + '">' + (diff.price.direction === 'up' ? '\u2191' : (diff.price.direction === 'dn' ? '\u2193' : '\u2014')) + '</span> <span class="diff-val ' + diff.price.direction + '">' + diff.price.change + '</span>' : '') + '<span class="sparkline-wrap"><canvas id="sp_' + item.asin + '_price"></canvas></span></div>' +
          '<div>Rating: <strong>' + ratingStr + '</strong>' + (diff.rating ? ' <span class="diff-arrow ' + diff.rating.direction + '">' + (diff.rating.direction === 'up' ? '\u2191' : (diff.rating.direction === 'dn' ? '\u2193' : '\u2014')) + '</span> <span class="diff-val ' + diff.rating.direction + '">' + diff.rating.change + '</span>' : '') + ' <span style="color:#64748b;font-size:12px;">Reviews ' + reviewsStr + '</span><span class="sparkline-wrap"><canvas id="sp_' + item.asin + '_rating"></canvas></span></div>' +
          '<div>Main: <span class="cat-item">' + (item.main_cat || '-') + '</span> <strong>' + mainBsrStr + '</strong>' + (diff.bsr ? ' <span class="diff-arrow ' + diff.bsr.direction + '">' + (diff.bsr.direction === 'up' ? '\u2191' : (diff.bsr.direction === 'dn' ? '\u2193' : '\u2014')) + '</span> <span class="diff-val ' + diff.bsr.direction + '">' + diff.bsr.change + '</span>' : '') + '<span class="sparkline-wrap"><canvas id="sp_' + item.asin + '_main_bsr"></canvas></span></div>' +
          '<div>Sub: <span class="cat-item">' + (item.sub_cat || '-') + '</span> <strong>' + (item.sub_bsr != null ? '#' + item.sub_bsr : '-') + '</strong>' + (diff.sub_bsr ? ' <span class="diff-arrow ' + diff.sub_bsr.direction + '">' + (diff.sub_bsr.direction === 'up' ? '\u2191' : (diff.sub_bsr.direction === 'dn' ? '\u2193' : '\u2014')) + '</span> <span class="diff-val ' + diff.sub_bsr.direction + '">' + diff.sub_bsr.change + '</span>' : '') + '<span class="sparkline-wrap"><canvas id="sp_' + item.asin + '_sub_bsr"></canvas></span></div>' +
        '</div></td>' +
        '<td class="col-jike">' +
          (item.is_main ? (
            // 主 ASIN：积加数据为主，卖家精灵估算作为 fallback
            (item.jike_units != null || item.jike_sales != null || item.jike_orders != null ? (
              // 有积加真实数据
              '<div style="font-size:12px;line-height:1.4;">Units <strong>' + (item.jike_units != null ? item.jike_units.toLocaleString() : '-') + '</strong> <span style="background:#dbeafe;color:#1e40af;font-size:9px;padding:1px 4px;border-radius:3px;margin-left:3px;">Jike</span></div>' +
              '<div style="font-size:11px;color:#64748b;line-height:1.4;">Sales $' + (item.jike_sales != null ? item.jike_sales.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '-') + '</div>' +
              '<div style="font-size:11px;color:#64748b;line-height:1.4;">Margin ' + (item.jike_gross_profit_rate != null ? item.jike_gross_profit_rate + '%' : '-') + '</div>' +
              '<div style="font-size:11px;line-height:1.4;">ACOS ' + (item.jike_acos != null ? item.jike_acos + '%' : '-') + '</div>' +
              '<div style="font-size:11px;color:#64748b;line-height:1.4;">Ad Spend $' + (item.jike_ads_spend != null ? item.jike_ads_spend.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '-') + '</div>' +
              '<div style="font-size:11px;line-height:1.4;">FBA Stock ' + (item.jike_fba_quantity != null ? item.jike_fba_quantity.toLocaleString() : '-') + '</div>' +
              '<div style="font-size:11px;color:#64748b;line-height:1.4;">Turnover ' + (item.jike_fba_turnover != null ? item.jike_fba_turnover.toFixed(1) : '-') + '</div>'
            ) : (
              // 积加无数据，显示卖家精灵估算（明确标注来源）
              '<div style="font-size:11px;color:#92400e;line-height:1.4;margin-bottom:3px;">⚠️ No Jike data</div>' +
              (item.seller_units_30d != null || item.seller_revenue_30d != null ? (
                '<div style="font-size:12px;line-height:1.4;">Units <strong style="color:#92400e;">' + (item.seller_units_30d != null ? item.seller_units_30d.toLocaleString() : '-') + '</strong> <span style="background:#fef3c7;color:#92400e;font-size:9px;padding:1px 4px;border-radius:3px;margin-left:3px;">Seller Sprite est.</span></div>' +
                '<div style="font-size:11px;color:#92400e;line-height:1.4;">Sales ~$' + (item.seller_revenue_30d != null ? item.seller_revenue_30d.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '-') + '</div>' +
                '<div style="font-size:10px;color:#92400e;line-height:1.4;font-style:italic;">⚠️ Not Jike real data</div>'
              ) : '<span style="color:#cbd5e1;font-size:11px;">-</span>')
            ))
          ) : '<span style="color:#cbd5e1;font-size:11px;">-</span>') +
        '</td>' +
        '<td class="col-plugin-l">' +
          (item.lqs ? '<div><strong>LQS</strong> ' + item.lqs + '</div>' : '') +
          (item.variant_count ? '<div><strong>Variants</strong> ' + item.variant_count + '</div>' : '') +
        '</td>' +
        '<td class="col-plugin-m">' +
          (item.natural_keywords ? '<div>Natural <strong>' + item.natural_keywords + '</strong></div>' : '') +
          (item.ad_keywords ? '<div>Ad <strong>' + item.ad_keywords + '</strong></div>' : '') +
          (item.suggest_keywords ? '<div>Suggested <strong>' + item.suggest_keywords + '</strong></div>' : '') +
        '</td>' +
        '<td class="col-plugin-r">' +
          (item.traffic_keywords_top && item.traffic_keywords_top.length ?
            item.traffic_keywords_top.slice(0, 4).map(function(kw) {
              return '<div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="' + kw.keyword + ' (' + (kw.type||'') + ')">' +
                kw.keyword + ' <span style="color:#7c3aed;">' + (kw.traffic_pct || '') + '</span></div>';
            }).join('')
          : '<span style="color:#cbd5e1;">-</span>') +
        '</td>' +
        '<td class="col-time"><div class="status-indicator ' + statusClass + '">' + statusText + '</div>' +
          '<div style="margin-top:4px;color:#64748b;">' + (rawData.updated || '-') + '</div>' +
          (item.launch_date ? '<div style="margin-top:4px;color:#64748b;">Launch ' + item.launch_date + '</div>' : '') +
          (eventsHtml && eventsHtml.indexOf('e-none') === -1 ? '<div style="margin-top:4px;">' + eventsHtml + '</div>' : '') + '</td>' +
      '</tr>';
    });
    tb.innerHTML = html || '<tr><td colspan="15" style="text-align:center;padding:20px;">No matching data</td></tr>';
    // Draw sparklines for each item with history data
    rawData.items.forEach(function(item) {
      if (item.history_price && item.history_price.length >= 1) {
        var c = document.getElementById('sp_' + item.asin + '_price');
        if (c) drawSparkline(c, item.history_price, item.diff && item.diff.price && item.diff.price.direction === 'dn' ? '#dc2626' : '#059669');
      }
      if (item.history_main_bsr && item.history_main_bsr.length >= 1) {
        var c = document.getElementById('sp_' + item.asin + '_main_bsr');
        if (c) drawSparkline(c, item.history_main_bsr, item.diff && item.diff.bsr && item.diff.bsr.direction === 'dn' ? '#dc2626' : '#e94560');
      }
      if (item.history_sub_bsr && item.history_sub_bsr.length >= 1) {
        var c = document.getElementById('sp_' + item.asin + '_sub_bsr');
        if (c) drawSparkline(c, item.history_sub_bsr, '#7c3aed');
      }
      if (item.history_rating && item.history_rating.length >= 1) {
        var c = document.getElementById('sp_' + item.asin + '_rating');
        if (c) drawSparkline(c, item.history_rating, '#059669');
      }
    });
  }

  function drawSparkline(canvas, data, color) {
    if (!canvas || !data || data.length < 1) return;
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

  function buildDiffHtml(diff, item) {
    if (!diff || Object.keys(diff).length === 0) {
      // First-time ASIN: show absolute values
      var abs = [];
      if (item.price != null) abs.push('<div class="diff-item">Price: <span class="diff-val same">$' + item.price + '</span></div>');
      if (item.reviews != null) abs.push('<div class="diff-item">Reviews: <span class="diff-val same">' + item.reviews + '</span></div>');
      if (item.rating != null) abs.push('<div class="diff-item">Rating: <span class="diff-val same">' + item.rating + '</span></div>');
      if (item.main_bsr != null) abs.push('<div class="diff-item">BSR: <span class="diff-val same">#' + item.main_bsr + '</span></div>');
      if (item.sub_bsr != null) abs.push('<div class="diff-item">Sub: <span class="diff-val same">#' + item.sub_bsr + '</span></div>');
      return abs.length ? abs.join('') : '<span class="diff-none">-</span>';
    }
    var rows = [];
    if (diff.price) { var dir = diff.price.direction || 'same'; var arrow = dir === 'up' ? '\u2191' : (dir === 'dn' ? '\u2193' : '-'); rows.push('<div class="diff-item"><span class="diff-arrow ' + dir + '">' + arrow + '</span> Price: <span class="diff-val ' + dir + '">$' + diff.price.current + '</span></div>'); }
    if (diff.review_count) { var dir = diff.review_count.direction || 'same'; var arrow = dir === 'up' ? '\u2191' : (dir === 'dn' ? '\u2193' : '-'); rows.push('<div class="diff-item"><span class="diff-arrow ' + dir + '">' + arrow + '</span> Reviews: <span class="diff-val ' + dir + '">' + diff.review_count.change + '</span></div>'); }
    if (diff.rating) { var dir = diff.rating.direction || 'same'; var arrow = dir === 'up' ? '\u2191' : (dir === 'dn' ? '\u2193' : '-'); rows.push('<div class="diff-item"><span class="diff-arrow ' + dir + '">' + arrow + '</span> Rating: <span class="diff-val ' + dir + '">' + diff.rating.change + '</span></div>'); }
    if (diff.bsr) { var dir = diff.bsr.direction || 'same'; var arrow = dir === 'up' ? '\u2191' : (dir === 'dn' ? '\u2193' : '-'); rows.push('<div class="diff-item"><span class="diff-arrow ' + dir + '">' + arrow + '</span> BSR: <span class="diff-val ' + dir + '">' + diff.bsr.change + '</span></div>'); }
    if (diff.sub_bsr) { var dir = diff.sub_bsr.direction || 'same'; var arrow = dir === 'up' ? '\u2191' : (dir === 'dn' ? '\u2193' : '-'); rows.push('<div class="diff-item"><span class="diff-arrow ' + dir + '">' + arrow + '</span> Sub: <span class="diff-val ' + dir + '">' + diff.sub_bsr.change + '</span></div>'); }
    return rows.join('') || '<span class="diff-none">-</span>';
  }

  function exportToExcel() {
    var rows = [['ASIN', 'Type', 'Brand', 'Monitor Type', 'Logic Type', 'Status', 'Price', 'BSR', 'Rating', 'Reviews', 'LQS', 'Variants', 'Launch Date', 'Total KW', 'Natural KW', 'Ad KW', 'Suggested KW', 'Units', 'Sales', 'Margin', 'ACOS', 'Ad Spend', 'FBA Stock', 'Turnover', 'Data Source', 'Last Updated']];
    rawData.items.forEach(function(m) {
      var jikeUnits = m.jike_units != null ? m.jike_units : (m.seller_units_30d != null ? '(est.)' + m.seller_units_30d : '-');
      var jikeSales = m.jike_sales != null ? m.jike_sales : (m.seller_revenue_30d != null ? '(est.)' + m.seller_revenue_30d : '-');
      var jikeGrossProfit = m.jike_gross_profit_rate != null ? m.jike_gross_profit_rate + '%' : '-';
      var jikeAcos = m.jike_acos != null ? m.jike_acos + '%' : '-';
      var jikeAdsSpend = m.jike_ads_spend != null ? m.jike_ads_spend : '-';
      var jikeFbaQty = m.jike_fba_quantity != null ? m.jike_fba_quantity : '-';
      var jikeFbaTurnover = m.jike_fba_turnover != null ? m.jike_fba_turnover : '-';
      var jikeSource = (m.jike_units != null || m.jike_sales != null) ? 'Jike' : (m.seller_units_30d != null ? 'Seller Sprite est.' : 'None');
      rows.push([m.asin, m.monitor_type, m.brand || '', m.monitor_type, m.logic_type, m.listing_status, m.price, m.main_bsr, m.rating, m.reviews, m.lqs || '', m.variant_count || '', m.launch_date || '', m.total_keywords || '', m.natural_keywords || '', m.ad_keywords || '', m.suggest_keywords || '', jikeUnits, jikeSales, jikeGrossProfit, jikeAcos, jikeAdsSpend, jikeFbaQty, jikeFbaTurnover, jikeSource, rawData.updated]);
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