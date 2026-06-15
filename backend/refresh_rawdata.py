"""刷新 frontend/data/rawData.json 的积加字段（手动触发）"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sync_monitor_data import load_jike_data, build_rawdata_item

RAW_PATH = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'data', 'rawData.json')

with open(RAW_PATH, 'r', encoding='utf-8') as f:
    raw = json.load(f)

# 找到 B0FVSS8SR1 的位置
target_idx = None
for i, item in enumerate(raw['items']):
    if item['asin'] == 'B0FVSS8SR1':
        target_idx = i
        break

if target_idx is None:
    print("B0FVSS8SR1 not found in rawData.json")
    sys.exit(1)

jike = load_jike_data('B0FVSS8SR1')
print("jike data loaded:", jike)

item = raw['items'][target_idx]
updated = build_rawdata_item('B0FVSS8SR1', item, [], jike_data=jike)
raw['items'][target_idx] = updated
raw['updated'] = '2026-06-09T16:06:00'

with open(RAW_PATH, 'w', encoding='utf-8') as f:
    json.dump(raw, f, ensure_ascii=False, indent=2)

print(f"Updated item {target_idx}:")
print(f"  jike_units: {updated.get('jike_units')}")
print(f"  jike_sales: {updated.get('jike_sales')}")
print(f"  jike_gross_profit_rate: {updated.get('jike_gross_profit_rate')}")
print(f"  jike_acos: {updated.get('jike_acos')}")
print(f"  jike_ads_spend: {updated.get('jike_ads_spend')}")
print(f"  jike_fba_quantity: {updated.get('jike_fba_quantity')}")
print(f"  jike_fba_turnover: {updated.get('jike_fba_turnover')}")
print("Done")