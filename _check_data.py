#!/usr/bin/env python3
import json
d = json.load(open('frontend/data/monitor-data.json', 'r', encoding='utf-8'))
print('ASINs:', len(d['asins']))
print('Updated:', d['updated'][:19])
print('First ASIN:')
item = d['asins'][0]
for k, v in item.items():
    if isinstance(v, str) and len(v) > 100:
        print(f'  {k}: {v[:80]}...')
    elif isinstance(v, list):
        print(f'  {k}: [{len(v)} items]')
    elif isinstance(v, dict):
        print(f'  {k}: {{...}}')
    else:
        print(f'  {k}: {v}')
