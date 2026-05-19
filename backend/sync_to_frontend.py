# -*- coding: utf-8 -*-
"""
sync_to_frontend.py - 从本地快照生成前端 monitor-data.json（含历史趋势）
"""
import json, os, glob, sys, re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'data', 'processed')
OUTPUT = os.path.join(BASE, '..', 'frontend', 'data', 'monitor-data.json')

def parse_ts(ts_val):
    """Parse various timestamp formats to ISO string"""
    if not ts_val:
        return ''
    ts = str(ts_val)
    # Format: 20260518_212002
    m = re.match(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', ts)
    if m:
        return f'{m.group(1)}-{m.group(2)}-{m.group(3)}T{m.group(4)}:{m.group(5)}:{m.group(6)}'
    # Try ISO format
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
    if v is None:
        return default
    s = str(v).replace(',', '').strip()
    if not s or s == '-':
        return default
    try: 
        return int(float(s))
    except: 
        return default

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
        if 'data' in latest and isinstance(data, dict):
            pass
        elif 'asin' in latest:
            data = latest
        
        # Build snapshots history
        snapshots = sorted(glob.glob(os.path.join(d, 'snapshot_*.json')))
        
        # Also include latest as a snapshot
        all_snaps = []
        seen_ts = set()
        
        for sp in snapshots:
            with open(sp, 'r', encoding='utf-8') as f:
                snap = json.load(f)
            sd = snap.get('data', snap)
            if 'data' in snap and isinstance(sd, dict):
                pass
            ts = parse_ts(snap.get('timestamp', ''))
            if ts and ts not in seen_ts:
                seen_ts.add(ts)
                all_snaps.append({
                    'timestamp': ts,
                    'price': safe_float(sd.get('price', '')),
                    'bsr': safe_int(sd.get('bsr', '')),
                    'rating': safe_float(sd.get('rating', '')),
                    'review_count': safe_int(sd.get('review_count', sd.get('reviews', '')))
                })
        
        # Build history from snapshots (chronological)
        all_snaps.sort(key=lambda x: x['timestamp'])
        history = all_snaps
        
        # Use sub_rank for snapshot BSR too (it's the clean number)
        for sp in snapshots:
            with open(sp, 'r', encoding='utf-8') as f:
                snap = json.load(f)
            sd = snap.get('data', snap)
            ts = parse_ts(snap.get('timestamp', ''))
            if ts and ts not in seen_ts:
                seen_ts.add(ts)
                bsr_val = safe_int(sd.get('bsr_sub_rank', ''))
                if bsr_val is None:
                    bsr_val = safe_int(sd.get('bsr', ''))
                all_snaps.append({
                    'timestamp': ts,
                    'price': safe_float(sd.get('price', '')),
                    'bsr': bsr_val,
                    'rating': safe_float(sd.get('rating', '')),
                    'review_count': safe_int(sd.get('review_count', sd.get('reviews', '')))
                })
        
        # Deduplicate
        seen2 = set()
        deduped = []
        for s in all_snaps:
            key = s['timestamp']
            if key not in seen2:
                seen2.add(key)
                deduped.append(s)
        deduped.sort(key=lambda x: x['timestamp'])
        history = deduped
        
        # Also ensure current entry is in history
        has_current = any(h['timestamp'] == '' for h in history) or len(history) == 0
        
        # Current values - bsr_sub_rank is cleaner than bsr
        price = safe_float(data.get('price', ''))
        list_price = safe_float(data.get('list_price', ''))
        rating = safe_float(data.get('rating', ''))
        review_count = safe_int(data.get('review_count', data.get('reviews', '')))
        bsr_raw = data.get('bsr_sub_rank', '')
        bsr = safe_int(bsr_raw) if bsr_raw else safe_int(data.get('bsr', ''))
        
        # Calculate change from history
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
            'bsr_sub_rank': safe_int(data.get('bsr_sub_rank', '')),
            'bsr_sub_category': data.get('bsr_sub_category', ''),
            'seller': data.get('sold_by', data.get('seller', '')),
            'history': history,
            'price_change': price_change,
            'bsr_change': bsr_change,
            'price_change_pct': price_change_pct,
            'bsr_change_pct': bsr_change_pct,
        }
        items.append(item)
        print(f'  {asin}: {price} | snapshots={len(history)} | priceΔ={price_change_pct}% | bsrΔ={bsr_change}')
    
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
