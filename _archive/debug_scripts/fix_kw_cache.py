#!/usr/bin/env python3
"""Fix keyword_related_asins.json — 把被锁死成 1 个的缓存恢复成 top_asins 全部 ASIN"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')

DATA = os.path.join(os.path.dirname(__file__), 'data')
KW_REL = os.path.join(DATA, 'keyword_related_asins.json')
KW_PROC = os.path.join(DATA, 'processed', 'kw_Makeup_Remover', 'latest.json')

with open(KW_PROC, 'r', encoding='utf-8') as f:
    kw_latest = json.load(f)

top_asins = kw_latest.get('top_asins', [])
print('Found {} top_asins in kw_Makeup_Remover/latest.json:'.format(len(top_asins)))
for a in top_asins:
    print('  - {} | {}'.format(a.get('asin', ''), a.get('title', '')[:50]))

# 读取旧缓存（如果有）
old = {}
if os.path.exists(KW_REL):
    with open(KW_REL, 'r', encoding='utf-8') as f:
        old = json.load(f)

# 合并：旧缓存 + 新增 top_asins
new_map = {}
for kw_name, asin_list in old.items():
    for a in asin_list:
        asin = a.get('asin', '') if isinstance(a, dict) else a
        if asin:
            new_map[asin] = a if isinstance(a, dict) else {'asin': asin, 'name': ''}

added = 0
for a in top_asins:
    asin = a.get('asin', '')
    if asin and asin not in new_map:
        new_map[asin] = {'asin': asin, 'name': a.get('title', '')[:60]}
        added += 1

new_data = {}
for kw_name in old.keys():
    new_data[kw_name] = list(new_map.values())

with open(KW_REL, 'w', encoding='utf-8') as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)

print('\nFixed! Added {} new ASINs. Total in cache: {}'.format(added, len(new_map)))
print('Wrote {}'.format(KW_REL))