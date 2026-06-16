#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词 ASIN 发现与缓存管理
"""
import sys, os, json, time, re
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from browser.cdp_bridge import CDPBrowser
from browser.amazon_browser import AmazonBrowser
from browser.asin_monitor import extract_asin_data, extract_sprite_plugin_data
from browser.snapshot_storage import save_asin_snapshot

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'data', 'processed')
os.makedirs(DATA_DIR, exist_ok=True)

def _kw_dir(keyword):
    safe = re.sub(r'[^a-zA-Z0-9]', '_', keyword)[:40]
    d = os.path.join(DATA_DIR, 'keyword_' + safe)
    os.makedirs(d, exist_ok=True)
    return d

def _load_json(path, default=None):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def _save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def parse_search_page_asins(browser):
    js = '''(() => {
        var asins = [];
        var seen = new Set();
        var cards = document.querySelectorAll("[data-asin]:not([data-asin=\"\"]):not([data-asin-template]), .s-result-item[data-asin]");
        cards.forEach((el, i) => {
            var asin = el.getAttribute("data-asin") || "";
            if (asin && asin.startsWith("B0") && asin.length === 10 && !seen.has(asin)) {
                seen.add(asin);
                var sp = !!(
                    el.querySelector(".s-sponsored-info") ||
                    el.querySelector("[class*=sponsored]") ||
                    el.closest("[class*=sponsored]") ||
                    el.querySelector(".a-badge-container")
                );
                asins.push({ asin: asin, rank: i + 1, sponsored: sp });
            }
        });
        if (asins.length < 3) {
            var body = document.body.innerText || "";
            var found = body.match(/B[A-Z0-9]{9,10}/g) || [];
            found.forEach((a) => {
                if (a.startsWith("B0") && !seen.has(a)) {
                    seen.add(a);
                    asins.push({ asin: a, rank: asins.length + 1, sponsored: false });
                }
            });
        }
        return JSON.stringify(asins.slice(0, 20));
    })()'''
    try:
        raw = browser.eval(js)
        if raw:
            return json.loads(raw) if isinstance(raw, str) else raw
    except Exception as e:
        print('JS err: ' + str(e))
    return []

def search_keyword_top5(browser, keyword, max_asins=5):
    print('  [search] ' + keyword)
    amazon = AmazonBrowser(browser)
    amazon.browse_homepage()
    time.sleep(1)
    amazon.search(keyword)
    time.sleep(3)
    for attempt in range(10):
        asins = parse_search_page_asins(browser)
        if len(asins) >= 3:
            print('    found ' + str(len(asins)) + ' (' + str(attempt+1) + ' tries)')
            return asins[:max_asins]
        time.sleep(1)
    asins = parse_search_page_asins(browser)
    print('    final ' + str(len(asins)))
    return asins[:max_asins]

THRESHOLD = 3

def classify_keyword_asins(keyword, new_asins):
    kw_dir = _kw_dir(keyword)
    hist = _load_json(os.path.join(kw_dir, 'history.json'), {'runs': []})
    stable = _load_json(os.path.join(kw_dir, 'stable.json'), {'keyword': keyword, 'stable_asins': []})
    new_list = [a['asin'] for a in new_asins]
    all_stable = stable.get('stable_asins', [])

    if not all_stable:
        seen = set()
        for run in hist.get('runs', []):
            seen.update(run.get('top5_asins', []))
        runs = hist.get('runs', [])
        if len(runs) >= THRESHOLD:
            recent = runs[-THRESHOLD:]
            cnt = {}
            for run in recent:
                for a in run.get('top5_asins', []):
                    cnt[a] = cnt.get(a, 0) + 1
            for a, c in cnt.items():
                if c >= THRESHOLD and a not in all_stable:
                    all_stable.append(a)
        not_stable = [a for a in new_list if a not in all_stable]
        variable = not_stable[0] if not_stable else None
        new_found = [a for a in new_list if a not in seen]
    else:
        not_stable = [a for a in new_list if a not in all_stable]
        variable = not_stable[0] if not_stable else None
        prev = hist['runs'][-1].get('top5_asins', []) if hist.get('runs') else []
        new_found = [a for a in not_stable if a not in prev]

    hist['runs'].append({
        'time': datetime.now().isoformat(),
        'top5_asins': new_list,
        'stable_at_this_run': list(all_stable),
        'variable_at_this_run': variable,
    })
    hist['runs'] = hist['runs'][-10:]
    _save_json(os.path.join(kw_dir, 'history.json'), hist)

    if all_stable and not stable.get('identified_at'):
        stable['identified_at'] = datetime.now().isoformat()
        stable['source'] = 'multiple_runs'
    stable['stable_asins'] = all_stable
    stable['keyword'] = keyword
    _save_json(os.path.join(kw_dir, 'stable.json'), stable)

    if variable:
        _save_json(os.path.join(kw_dir, 'variable.json'), {
            'keyword': keyword,
            'variable_asin': variable,
            'detected_at': datetime.now().isoformat(),
            'reason': 'not_in_stable',
            'also_new_found': new_found,
        })
    return {'stable': all_stable, 'variable': variable, 'all': new_list, 'new_found': new_found}

def fetch_asin_full(browser, asin, keyword, source='keyword'):
    print('    [fetch] ' + asin + ' (' + source + ')')
    try:
        amazon = AmazonBrowser(browser)
        amazon.search_for_asin(asin)
        browser.scroll_down(times=1, min_pause=0.3, max_pause=0.8)
        time.sleep(2)
        data = extract_asin_data(browser)
        if not data.get('title'):
            return {}
        plugin = extract_sprite_plugin_data(browser)
        if plugin:
            for k, v in plugin.items():
                data['sprite_' + k] = v
        data['_source_keyword'] = keyword
        data['_asin_type'] = source
        return data
    except Exception as e:
        print('    [fail] ' + asin + ': ' + str(e))
        return {}

def fetch_keyword_asins(keywords, browser=None):
    results = []
    close = False
    if browser is None:
        browser = CDPBrowser()
        browser.connect_tab(tab_url_filter='about:blank')
        if not browser.tab:
            browser.cmd('Target.createTarget', {'url': 'about:blank'})
            time.sleep(0.5)
            browser.connect_tab(tab_url_filter='about:blank')
        close = True
    try:
        for kw in keywords:
            print('=== ' + kw + ' ===')
            top5 = search_keyword_top5(browser, kw, max_asins=5)
            if not top5:
                continue
            cls = classify_keyword_asins(kw, top5)
            print('  stable=' + str(cls['stable']) + ' variable=' + str(cls['variable']))
            for info in top5:
                asin = info['asin']
                if asin in cls['stable']:
                    latest = _load_json(os.path.join(DATA_DIR, 'asin_' + asin, 'latest.json'), None)
                    if latest:
                        print('    [cache] ' + asin)
                        d = latest.get('data', {})
                        d['_source_keyword'] = kw
                        d['_asin_type'] = 'stable'
                        results.append({'asin': asin, 'keyword': kw, 'data': d, 'asin_type': 'stable'})
                        continue
                    typ = 'stable'
                elif asin == cls['variable']:
                    typ = 'variable'
                else:
                    typ = 'new'
                d = fetch_asin_full(browser, asin, kw, source=typ)
                if d and d.get('title'):
                    save_asin_snapshot(asin, d)
                    results.append({'asin': asin, 'keyword': kw, 'data': d, 'asin_type': typ})
                else:
                    print('    [empty] ' + asin)
    finally:
        if close:
            browser.close()
    return results