#!/usr/bin/env python3
"""Dry-run classify_keyword_asins — 不抓取，只跑分类逻辑验证"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from browser.fetch_keyword_asins import classify_keyword_asins

kw = "Makeup Remover"
# 用 kw_Makeup_Remover/latest.json 里的 top_asins 当输入
kw_latest = os.path.join(os.path.dirname(__file__), 'data', 'processed', 'kw_Makeup_Remover', 'latest.json')
with open(kw_latest, 'r', encoding='utf-8') as f:
    top_asins = json.load(f).get('top_asins', [])

print('Input top_asins ({}):'.format(len(top_asins)))
for a in top_asins:
    print('  - {}'.format(a.get('asin', '')))

print('\nClassifying...')
result = classify_keyword_asins(kw, top_asins)
print('\nResult:')
print('  stable  = {}'.format(result.get('stable')))
print('  variable= {}'.format(result.get('variable')))
print('  new_found = {}'.format(result.get('new_found')))
print('  all     = {}'.format(result.get('all')))

# 检查写入的文件
kw_dir = os.path.join(os.path.dirname(__file__), 'data', 'processed', 'kw_' + kw.replace(' ', '_'))
print('\nKeyword cache dir: {}'.format(kw_dir))
for fn in ['stable.json', 'variable.json', 'history.json']:
    p = os.path.join(kw_dir, fn)
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            print('  {} = {}'.format(fn, json.load(f) if fn != 'history.json' else '({} runs)'.format(len(json.load(f).get('runs', [])))))
    else:
        print('  {} = MISSING'.format(fn))