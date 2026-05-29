#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_monitor_data.py - 从本地快照生成前端可用的 rawData JSON
写入 frontend/data/rawData.json，供 monitor.html 加载
"""
import json, os, glob, sys, re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'data', 'processed')
OUTPUT_RAW = os.path.join(BASE, '..', 'frontend', 'data', 'rawData.json')


def parse_ts(ts_val):
    if not ts_val:
        return ''
    ts = str(ts_val)
    m = re.match(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', ts)
    if m:
        return f'{m.group(1)}-{m.group(2)}-{m.group(3)}T{m.group(4)}:{m.group(5)}:{m.group(6)}'
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00')).isoformat()[:19]
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
    v = safe_int(data.get('bsr_sub_rank'))
    if v is not None:
        return v
    bsr_raw = data.get('bsr', '')
    if bsr_raw:
        m = re.search(r'#([\d,]+)', str(bsr_raw))
        if m:
            return safe_int(m.group(1))
        m = re.search(r'([\d,]+)', str(bsr_raw))
        if m:
            return safe_int(m.group(1))
    return None


def build_rawdata_item(asin, data, history):
    """用 monitor-data.json 的数据构建前端 rawData.items 格式"""
    price = safe_float(data.get('price', '')) or 0
    list_price = safe_float(data.get('list_price', '')) or 0
    rating = safe_float(data.get('rating', '')) or 0
    review_count = safe_int(data.get('review_count', data.get('reviews', ''))) or 0
    bsr = extract_bsr(data)
    main_bsr = bsr or 0
    title = data.get('title', data.get('product_title', ''))
    brand = data.get('brand', '')
    main_cat = data.get('bsr_sub_category', '') or ''

    price_change = 0.0
    if len(history) >= 2:
        first_p = history[0].get('price')
        last_p = history[-1].get('price')
        if first_p and last_p and first_p > 0:
            price_change = round(last_p - first_p, 2)

    return {
        "monitor_type": "ASIN",
        "asin": asin,
        "is_main": True,
        "logic_type": "主监控",
        "title": title[:200],
        "brand": brand[:60] if brand else '',
        "img": data.get('main_image', data.get('img', '')),
        "price": price,
        "chg": price_change,
        "rating": rating,
        "reviews": review_count,
        "listing_status": "正常",
        "expected_listing_status": "正常",
        "title_changed": False,
        "img_changed": False,
        "bullets_changed": False,
        "description_changed": False,
        "variant_status": "正常",
        "variant_changed": False,
        "deal_activity": "无",
        "badges_current": [],
        "badges_lost": [],
        "coupon": "无",
        "prime_discount": "未开启",
        "main_cat": main_cat,
        "expected_main_cat": main_cat,
        "main_bsr": main_bsr,
        "sub_cat": main_cat,
        "expected_sub_cat": main_cat,
        "sub_bsr": main_bsr,
        "history_main_bsr": [h.get('bsr') or main_bsr for h in history] if history else [main_bsr],
        "history_sub_bsr": [],
        "events": []
    }


def main():
    items = []

    asin_dirs = sorted(glob.glob(os.path.join(DATA_DIR, 'asin_*')))
    print(f'[SYNC] Found {len(asin_dirs)} ASIN directories')

    for d in asin_dirs:
        asin = os.path.basename(d).replace('asin_', '')
        latest_path = os.path.join(d, 'latest.json')
        if not os.path.exists(latest_path):
            continue
        with open(latest_path, 'r', encoding='utf-8') as f:
            latest = json.load(f)

        data = latest.get('data', latest)

        snapshots = sorted(glob.glob(os.path.join(d, 'snapshot_*.json')))
        all_snaps = []
        seen_keys = set()

        def add_snap(snap_data, snap_ts):
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
        add_snap(latest, None)
        all_snaps.sort(key=lambda x: x['timestamp'])

        item = build_rawdata_item(asin, data, all_snaps)
        items.append(item)
        print(f'  {asin}: price=${item["price"]} bsr=#{item["main_bsr"]} snaps={len(all_snaps)}')

    output = {
        'updated': datetime.now().isoformat()[:19],
        'items': items
    }

    os.makedirs(os.path.dirname(OUTPUT_RAW), exist_ok=True)
    with open(OUTPUT_RAW, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n✅ Written {len(items)} items to {OUTPUT_RAW}')


if __name__ == '__main__':
    main()