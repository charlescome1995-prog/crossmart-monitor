#!/usr/bin/env python3
"""
sync_groups.py - 把分组数据（主ASIN+关联ASIN）同步到前端
同时抓取所有未监控的ASIN数据
"""
import json, os, glob, sys, re, time, urllib.request
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'data', 'processed')
RELATED_DIR = DATA_DIR
OUTPUT = os.path.join(BASE, '..', 'frontend', 'data', 'monitor-data.json')

MAIN_ASINS = ["B09V7Z4TJG", "B0CGB215HR", "B0DSLGHPPW", "B0F2J966QL", "B0GKFD9ZQW"]

def parse_ts(ts_val):
    if not ts_val: return ''
    ts = str(ts_val)
    m = re.match(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', ts)
    if m: return f'{m.group(1)}-{m.group(2)}-{m.group(3)}T{m.group(4)}:{m.group(5)}:{m.group(6)}'
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.isoformat()[:19]
    except: return ts

def safe_float(v, default=None):
    if v is None: return default
    s = str(v).replace('$', '').replace(',', '').strip()
    if not s: return default
    try: return float(s)
    except: return default

def safe_int(v, default=None):
    if v is None: return default
    s = str(v).replace(',', '').strip()
    if not s or s == '-': return default
    try: return int(float(s))
    except: return default

def extract_bsr(data):
    v = safe_int(data.get('bsr_sub_rank'))
    if v is not None: return v
    bsr_raw = data.get('bsr', '')
    if bsr_raw:
        m = re.search(r'#([\d,]+)', str(bsr_raw))
        if m: return safe_int(m.group(1))
        m = re.search(r'([\d,]+)', str(bsr_raw))
        if m: return safe_int(m.group(1))
    return None

def load_related(main_asin):
    """加载主ASIN的关联ASIN列表"""
    path = os.path.join(RELATED_DIR, 'related_%s.json' % main_asin)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            d = json.load(f)
        return d.get('related', [])
    return []

def load_asin_data(asin):
    """加载单个ASIN的latest快照"""
    snap_dir = os.path.join(DATA_DIR, 'asin_%s' % asin)
    latest_path = os.path.join(snap_dir, 'latest.json')
    if os.path.exists(latest_path):
        with open(latest_path, 'r', encoding='utf-8') as f:
            latest = json.load(f)
        return latest.get('data', latest)
    return {}

def load_history(asin):
    """加载单个ASIN的历史快照列表"""
    snap_dir = os.path.join(DATA_DIR, 'asin_%s' % asin)
    snaps = sorted(glob.glob(os.path.join(snap_dir, 'snapshot_*.json')))
    all_snaps = []
    seen_keys = set()

    def add_snap(path):
        with open(path, 'r', encoding='utf-8') as f:
            snap = json.load(f)
        ts = parse_ts(snap.get('timestamp', ''))
        if not ts or ts in seen_keys: return
        seen_keys.add(ts)
        sd = snap.get('data', snap)
        all_snaps.append({
            'timestamp': ts,
            'price': safe_float(sd.get('price', '')),
            'bsr': extract_bsr(sd),
            'rating': safe_float(sd.get('rating', '')),
            'review_count': safe_int(sd.get('review_count', sd.get('reviews', '')))
        })

    for sp in snaps:
        add_snap(sp)
    # Add latest
    latest_path = os.path.join(snap_dir, 'latest.json')
    if os.path.exists(latest_path): add_snap(latest_path)

    all_snaps.sort(key=lambda x: x['timestamp'])
    return all_snaps

def build_group(main_asin, related_asins):
    """为一个主ASIN构建完整的组数据"""
    # 主ASIN数据
    main_data = load_asin_data(main_asin)
    main_history = load_history(main_asin)
    main_price = safe_float(main_data.get('price', ''))
    main_bsr = extract_bsr(main_data)

    # 计算主ASIN自身的变化
    price_change = 0; bsr_change = 0; price_change_pct = 0; bsr_change_pct = 0
    if len(main_history) >= 2:
        first, last = main_history[0], main_history[-1]
        if first['price'] and last['price'] and first['price'] > 0:
            price_change = round(last['price'] - first['price'], 2)
            price_change_pct = round((last['price'] - first['price']) / first['price'] * 100, 1)
        if first['bsr'] and last['bsr'] and first['bsr'] > 0:
            bsr_change = last['bsr'] - first['bsr']
            bsr_change_pct = round((last['bsr'] - first['bsr']) / first['bsr'] * 100, 1)

    # 组成员：主ASIN + 关联ASIN
    all_members = [main_asin] + related_asins
    member_items = []

    for idx, asin in enumerate(all_members):
        asin_data = load_asin_data(asin)
        asin_history = load_history(asin)
        price = safe_float(asin_data.get('price', ''))
        bsr = extract_bsr(asin_data)
        rating = safe_float(asin_data.get('rating', ''))
        review_count = safe_int(asin_data.get('review_count', asin_data.get('reviews', '')))

        # 如果没有历史数据（未抓取），跳过变化计算
        if len(asin_history) >= 2:
            f2, l2 = asin_history[0], asin_history[-1]
            pc = round(l2['price'] - f2['price'], 2) if f2['price'] and l2['price'] and f2['price'] > 0 else 0
            pcp = round((l2['price'] - f2['price']) / f2['price'] * 100, 1) if f2['price'] and l2['price'] and f2['price'] > 0 else 0
            bc = l2['bsr'] - f2['bsr'] if f2['bsr'] and l2['bsr'] and f2['bsr'] > 0 else 0
            bcp = round((l2['bsr'] - f2['bsr']) / f2['bsr'] * 100, 1) if f2['bsr'] and l2['bsr'] and f2['bsr'] > 0 else 0
        else:
            pc = pcp = bc = bcp = 0

        has_history = len(asin_history) >= 2
        has_diff = (abs(pcp) >= 0.01) or (bc != 0)

        member_items.append({
            'asin': asin,
            'title': asin_data.get('title', asin_data.get('product_title', '')),
            'brand': asin_data.get('brand', ''),
            'main_image': asin_data.get('main_image', asin_data.get('img', '')),
            'price': price,
            'list_price': safe_float(asin_data.get('list_price', '')),
            'rating': rating,
            'review_count': review_count,
            'bsr': bsr,
            'bsr_sub_rank': extract_bsr(asin_data),
            'bsr_sub_category': asin_data.get('bsr_sub_category', ''),
            'seller': asin_data.get('sold_by', asin_data.get('seller', '')),
            'history': asin_history,
            'price_change': pc,
            'bsr_change': bc,
            'price_change_pct': pcp,
            'bsr_change_pct': bcp,
            'is_main': idx == 0,
            'has_history': has_history,
            'has_diff': has_diff,
        })

    return {
        'main_asin': main_asin,
        'members': member_items,
        'count': len(member_items),
    }

def main():
    groups = []
    all_asins_in_groups = set()

    for main in MAIN_ASINS:
        related = load_related(main)
        # 关联ASIN去重（排除也作为主ASIN的）
        filtered_related = [a for a in related if a not in MAIN_ASINS]
        # 如果关联不够4个，补充空白占位
        while len(filtered_related) < 4:
            filtered_related.append(None)
        filtered_related = filtered_related[:4]

        group = build_group(main, filtered_related)
        groups.append(group)

        for m in group['members']:
            all_asins_in_groups.add(m['asin'])

    output = {
        'updated': datetime.now().isoformat()[:19],
        'groups': groups,
        'total_asins': len(all_asins_in_groups),
    }

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print('Groups written to %s' % OUTPUT)
    for g in groups:
        print('  Group %s: %d members' % (g['main_asin'], g['count']))

if __name__ == '__main__':
    main()