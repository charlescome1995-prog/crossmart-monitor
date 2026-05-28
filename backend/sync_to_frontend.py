# -*- coding: utf-8 -*-
"""
sync_to_frontend.py - 从本地快照生成前端 monitor-data.json（含历史趋势）
"""
import json, os, glob, sys, re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'backend', 'data', 'processed')
OUTPUT = os.path.join(BASE, '..', 'frontend', 'data', 'monitor-data.json')


def parse_ts(ts_val):
    """Parse various timestamp formats to ISO string"""
    if not ts_val:
        return ''
    ts = str(ts_val)
    m = re.match(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', ts)
    if m:
        return f'{m.group(1)}-{m.group(2)}-{m.group(3)}T{m.group(4)}:{m.group(5)}:{m.group(6)}'
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.isoformat()[:19]
    except:
        return ts


def safe_float(v, default=None):
    if v is None:
        return default
    s = str(v).replace('$', '').replace(',', '').strip()
    if not s:
        return default
    try:
        return float(s)
    except:
        return default


def safe_int(v, default=None):
    """从数字、字符串或带逗号的数字字符串中提取int"""
    if v is None:
        return default
    s = str(v).replace(',', '').strip()
    if not s or s == '-':
        return default
    try:
        return int(float(s))
    except:
        return default


def extract_bsr(data):
    """从snapshot data中提取BSR数字，按优先级尝试多个字段"""
    # 1. bsr_sub_rank 最干净
    v = safe_int(data.get('bsr_sub_rank'))
    if v is not None:
        return v
    # 2. bsr 字段可能有字符串，从中提取第一个数字
    bsr_raw = data.get('bsr', '')
    if bsr_raw:
        m = re.search(r'#([\d,]+)', str(bsr_raw))
        if m:
            return safe_int(m.group(1))
        m = re.search(r'([\d,]+)', str(bsr_raw))
        if m:
            return safe_int(m.group(1))
    return None


def main():
    items = []

    asin_dirs = sorted(glob.glob(os.path.join(DATA_DIR, 'asin_*')))
    print(f'Found {len(asin_dirs)} ASIN directories')

    for d in asin_dirs:
        asin = os.path.basename(d).replace('asin_', '')

        # Read latest
        latest_path = os.path.join(d, 'latest.json')
        if not os.path.exists(latest_path):
            continue
        with open(latest_path, 'r', encoding='utf-8') as f:
            latest = json.load(f)

        data = latest.get('data', latest)

        # Gather all snapshots + latest into history
        snapshots = sorted(glob.glob(os.path.join(d, 'snapshot_*.json')))
        all_snaps = []
        seen_keys = set()

        def add_snap(snap_data, snap_ts):
            """Parse one snapshot dict and append to all_snaps"""
            ts = parse_ts(snap_data.get('timestamp', snap_ts))
            if not ts or ts in seen_keys:
                return
            seen_keys.add(ts)
            sd = snap_data.get('data', snap_data)
            all_snaps.append({
                'timestamp': ts,
                'price': safe_float(sd.get('price', '')),
                'bsr': extract_bsr(sd),
                'rating': safe_float(sd.get('rating', '')),
                'review_count': safe_int(sd.get('review_count', sd.get('reviews', '')))
            })

        for sp in snapshots:
            with open(sp, 'r', encoding='utf-8') as f:
                snap = json.load(f)
            add_snap(snap, sp)

        # Add latest as a snapshot if not already included
        add_snap(latest, None)

        # Sort chronologically
        all_snaps.sort(key=lambda x: x['timestamp'])
        history = all_snaps

        # Current values
        price = safe_float(data.get('price', ''))
        list_price = safe_float(data.get('list_price', ''))
        rating = safe_float(data.get('rating', ''))
        review_count = safe_int(data.get('review_count', data.get('reviews', '')))
        bsr = extract_bsr(data)

        # Calculate change from first to last snapshot
        price_change = 0
        bsr_change = 0
        price_change_pct = 0
        bsr_change_pct = 0

        if len(history) >= 2:
            first, last = history[0], history[-1]
            if first['price'] is not None and last['price'] is not None and first['price'] > 0:
                price_change = round(last['price'] - first['price'], 2)
                price_change_pct = round((last['price'] - first['price']) / first['price'] * 100, 1)
            if first['bsr'] is not None and last['bsr'] is not None and first['bsr'] > 0 and last['bsr'] > 0:
                bsr_change = last['bsr'] - first['bsr']
                bsr_change_pct = round((last['bsr'] - first['bsr']) / first['bsr'] * 100, 1)

        item = {
            'asin': asin,
            'title': data.get('title', data.get('product_title', '')),
            'brand': data.get('brand', ''),
            'main_image': data.get('main_image', data.get('img', '')),
            'price': price,
            'list_price': list_price,
            'rating': rating,
            'review_count': review_count,
            'bsr': bsr,
            'bsr_sub_rank': extract_bsr(data),
            'bsr_sub_category': data.get('bsr_sub_category', ''),
            'seller': data.get('sold_by', data.get('seller', '')),
            'history': history,
            'price_change': price_change,
            'bsr_change': bsr_change,
            'price_change_pct': price_change_pct,
            'bsr_change_pct': bsr_change_pct,
        }
        items.append(item)
        print(f'  {asin}: ${price} | bsr=#{bsr} | snaps={len(history)} | priceΔ={price_change_pct}% | bsrΔ={bsr_change}')

    output = {
        'updated': datetime.now().isoformat()[:19],
        'asins': items
    }

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n✅ Written {len(items)} ASINs to {OUTPUT}')


if __name__ == '__main__':
    main()
