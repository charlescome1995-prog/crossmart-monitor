#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_monitor_data.py - 从本地快照生成前端可用的 rawData JSON
写入 frontend/data/rawData.json，供 monitor.html 加载
"""
import json, os, glob, sys, re, subprocess
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


def load_asin_meta(asin):
    """加载 ASIN 的 _meta.json（关联ASIN列表）"""
    meta_path = os.path.join(DATA_DIR, f'asin_{asin}', '_meta.json')
    if not os.path.exists(meta_path):
        return None
    with open(meta_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_rawdata_item(asin, data, history, related_asins=None):
    """构建前端 rawData.items 格式"""
    price = safe_float(data.get('price', '')) or 0
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

    item = {
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

    if related_asins:
        item["related_asins"] = related_asins

    return item


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

        # 关联ASIN数据：meta（固定来源）+ latest里的实时数据
        related_asins = []
        meta = load_asin_meta(asin)
        if meta and meta.get('related_asins'):
            realtime_map = {}
            rt_data = data.get('_related_asins', [])
            if rt_data:
                for r in rt_data:
                    realtime_map[r.get('asin', '')] = r
            for ra in meta['related_asins']:
                asin_key = ra.get('asin', '')
                rt = realtime_map.get(asin_key, {})
                related_asins.append({
                    "asin": asin_key,
                    "source": ra.get('source', ''),
                    "title": rt.get('title', ''),
                    "price": rt.get('price', ''),
                    "rating": rt.get('rating', ''),
                    "reviews": rt.get('reviews', ''),
                    "bsr": rt.get('bsr', ''),
                    "brand": rt.get('brand', ''),
                })

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

        item = build_rawdata_item(asin, data, all_snaps, related_asins if related_asins else None)
        items.append(item)
        print(f'  {asin}: price=${item["price"]} bsr=#{item["main_bsr"]} snaps={len(all_snaps)}', end='')
        if related_asins:
            print(f'  related={len(related_asins)}', end='')
        print()

    # ── 关键词数据 ──────────────────────────────────────────────────
    keywords_data = []
    kw_dirs = sorted(glob.glob(os.path.join(DATA_DIR, 'kw_*')))
    print(f'[SYNC] Found {len(kw_dirs)} keyword directories')

    for d in kw_dirs:
        kw = os.path.basename(d).replace('kw_', '').replace('_', ' ')
        latest_path = os.path.join(d, 'latest.json')
        if not os.path.exists(latest_path):
            continue
        with open(latest_path, 'r', encoding='utf-8') as f:
            latest = json.load(f)

        inner = latest.get('data', latest)
        top_asins = inner.get('top_asins', [])

        keywords_data.append({
            "keyword": kw,
            "top_asins": [
                {
                    "asin": a.get('asin', ''),
                    "type": a.get('type', ''),
                    "rank": a.get('rank', ''),
                    "title": a.get('title', ''),
                    "price": a.get('price', ''),
                    "rating": a.get('rating', ''),
                    "reviews": a.get('reviews', ''),
                }
                for a in top_asins
            ]
        })
        print(f'  kw [{kw}]: {len(top_asins)} top ASINs')

    output = {
        'updated': datetime.now().isoformat()[:19],
        'items': items,
        'keywords': keywords_data
    }

    os.makedirs(os.path.dirname(OUTPUT_RAW), exist_ok=True)
    with open(OUTPUT_RAW, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n✅ Written {len(items)} items + {len(keywords_data)} keywords to {OUTPUT_RAW}')

    # ── 自动推送到 GitHub ──────────────────────────────────────────
    try:
        subprocess.run(['git', 'add', OUTPUT_RAW], capture_output=True, cwd=BASE)
        diff = subprocess.run(['git', 'diff', '--cached', '--stat'], capture_output=True, text=True, cwd=BASE)
        if diff.stdout.strip():
            subprocess.run(['git', 'commit', '-m', 'auto: sync rawData.json with keywords'], capture_output=True, cwd=BASE)
            result = subprocess.run(['git', 'push'], capture_output=True, text=True, cwd=BASE)
            if result.returncode == 0:
                print('🚀 rawData.json 已推送至 GitHub')
            else:
                print('⚠️ 推送失败:', result.stderr[:200])
        else:
            print('ℹ️ rawData.json 无变化，跳过推送')
    except Exception as e:
        print(f'⚠️ Git 推送异常: {e}')


if __name__ == '__main__':
    main()