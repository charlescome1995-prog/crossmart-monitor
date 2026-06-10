#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_monitor_data.py - 从本地快照生成前端可用的 rawData JSON
写入 frontend/data/rawData.json，供 monitor.html 加载
支持与上次快照的 diff 比对
"""
import json, os, glob, sys, re, subprocess
from datetime import datetime

# 积加数据字段列表（用于清理关联竞品/关键词ASIN的积加字段）
JIKE_FIELDS = [
    'jike_sales', 'jike_orders', 'jike_units', 'jike_session',
    'jike_page_views', 'jike_conversion_rate', 'jike_rating', 'jike_reviews',
    'jike_main_seller_rank', 'jike_seller_rank', 'jike_listing_state',
    'jike_product_name', 'jike_acos', 'jike_ads_spend',
    'jike_fba_quantity', 'jike_fba_turnover', 'jike_gross_profit_rate',
]


def load_jike_data(asin):
    """从 processed/asin_ASIN/jike_latest.json 加载积加数据"""
    path = os.path.join(DATA_DIR, f'asin_{asin}', 'jike_latest.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        # 直接返回 dict（key 是 ASIN），不需要包装层
        return content if isinstance(content, dict) else {}
    except Exception:
        return {}


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
    v = safe_int(data.get('bsr_subrank'))  # bsr_subrank 在快照里是大类排名（如 111951）
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


def extract_sub_bsr(data):
    """从 bsr 字符串或 bsr_all_subranks 中提取小类排名（如 #213 in Antifungal Remedies）"""
    # 优先取 JS 新增的 bsr_all_subranks（第2项起为小类）
    all_sub = data.get('bsr_all_subranks', [])
    if isinstance(all_sub, list) and len(all_sub) >= 1:
        return safe_int(all_sub[0])  # 第一个小类排名
    # 回退：从 bsr 字符串解析第二个 #数字
    bsr_raw = data.get('bsr', '')
    if not bsr_raw:
        return None
    matches = re.findall(r'#(\d[\d,]*)', str(bsr_raw))
    if len(matches) >= 2:
        return safe_int(matches[1])
    return None


# ── Diff 比对逻辑 ────────────────────────────────────────────────

def build_diff(curr_data, prev_data):
    """
    比对当前快照与上次快照，生成 diff 字段。
    diff 格式：
      price:    {current, prev, change, pct, direction}
      rating:   {current, prev, change, direction}
      review_count: {current, prev, change, direction}
      bsr:      {current, prev, change, direction}
      variants: {current, prev, change, direction}
      deal_activity: {current, prev, direction}
      badges:   {current, prev, lost, gained, direction}
    """
    if prev_data is None:
        return {}

    diff = {}

    def cf(key, default=None):
        """safe_float from curr"""
        return safe_float(curr_data.get(key, ''), default)

    def pf(key, default=None):
        """safe_float from prev"""
        return safe_float(prev_data.get(key, ''), default)

    def ci(key, default=None):
        """safe_int from curr"""
        return safe_int(curr_data.get(key, curr_data.get(key.replace('_count', ''), '')), default)

    def pi(key, default=None):
        """safe_int from prev"""
        return safe_int(prev_data.get(key, prev_data.get(key.replace('_count', ''), '')), default)

    # 价格
    p_c = cf('price')
    p_p = pf('price')
    if p_c is not None and p_p is not None and p_p > 0:
        chg = round(p_c - p_p, 2)
        pct = round((p_c - p_p) / p_p * 100, 1)
        diff['price'] = {
            'current': p_c,
            'prev': p_p,
            'change': ('+' if chg >= 0 else '') + str(chg),
            'pct': ('+' if pct >= 0 else '') + str(pct) + '%',
            'direction': 'up' if chg > 0 else ('dn' if chg < 0 else 'same')
        }

    # 评分
    r_c = cf('rating')
    r_p = pf('rating')
    if r_c is not None and r_p is not None:
        chg = round(r_c - r_p, 1)
        diff['rating'] = {
            'current': r_c,
            'prev': r_p,
            'change': ('+' if chg >= 0 else '') + str(chg),
            'direction': 'up' if chg > 0 else ('dn' if chg < 0 else 'same')
        }

    # 评论数
    rc_c = ci('review_count')
    rc_p = pi('review_count')
    if rc_c is not None and rc_p is not None:
        chg = rc_c - rc_p
        diff['review_count'] = {
            'current': rc_c,
            'prev': rc_p,
            'change': ('+' if chg >= 0 else '') + str(chg),
            'direction': 'up' if chg > 0 else ('dn' if chg < 0 else 'same')
        }

    # BSR 大类排名
    b_c = extract_bsr(curr_data)
    b_p = extract_bsr(prev_data)
    if b_c is not None and b_p is not None:
        chg = b_c - b_p  # 排名数字增加 = 跌（差值为正 = 排名变差）
        diff['bsr'] = {
            'current': b_c,
            'prev': b_p,
            'change': ('+' if chg >= 0 else '') + str(abs(chg)),
            'direction': 'up' if chg < 0 else ('dn' if chg > 0 else 'same')
        }

    # BSR 小类排名（子分类）
    sb_c = extract_sub_bsr(curr_data)
    sb_p = extract_sub_bsr(prev_data)
    if sb_c is not None and sb_p is not None:
        chg = sb_c - sb_p
        diff['sub_bsr'] = {
            'current': sb_c,
            'prev': sb_p,
            'change': ('+' if chg >= 0 else '') + str(abs(chg)),
            'direction': 'up' if chg < 0 else ('dn' if chg > 0 else 'same')
        }

    # 变体
    v_c = curr_data.get('variants', '')
    v_p = prev_data.get('variants', '')
    if v_c != v_p:
        diff['variants'] = {
            'current': v_c,
            'prev': v_p,
            'direction': 'changed'
        }

    # Deal 状态
    d_c = curr_data.get('deal_activity', '无')
    d_p = prev_data.get('deal_activity', '无')
    if d_c != d_p:
        diff['deal_activity'] = {
            'current': d_c,
            'prev': d_p,
            'direction': 'changed'
        }

    # 徽章
    b_c2 = curr_data.get('badges', []) or []
    b_p2 = prev_data.get('badges', []) or []
    if b_c2 != b_p2:
        lost = [b for b in b_p2 if b not in b_c2]
        gained = [b for b in b_c2 if b not in b_p2]
        diff['badges'] = {
            'current': b_c2,
            'prev': b_p2,
            'lost': lost,
            'gained': gained,
            'direction': 'changed' if lost or gained else 'same'
        }

    return diff


def get_prev_snapshot_data(history):
    """从 history 列表中取出倒数第二个快照的 data"""
    if len(history) < 2:
        return None
    snap = history[-2]
    if isinstance(snap, dict) and 'data' in snap:
        return snap['data']
    if isinstance(snap, dict):
        return snap
    return None


def _calc_badges_lost(current_badges, prev_badges):
    """计算本次相比上次丢失的标识"""
    if not prev_badges:
        return []
    curr = set(current_badges) if isinstance(current_badges, list) else set()
    prev = set(prev_badges) if isinstance(prev_badges, list) else set()
    lost = list(prev - curr)
    return lost


# ── 构建函数 ────────────────────────────────────────────────────

def load_asin_meta(asin):
    """加载 ASIN 的 _meta.json（关联ASIN列表）"""
    meta_path = os.path.join(DATA_DIR, f'asin_{asin}', '_meta.json')
    if not os.path.exists(meta_path):
        return None
    with open(meta_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_bsr_categories(bsr_raw):
    """从 bsr 字符串解析大类和小类分类名"""
    # 格式: "Best Sellers Rank: #111,951 in Health & Household (See Top 100 in Health & Household)\n#213 in Antifungal Remedies"
    if not bsr_raw:
        return '', ''
    lines = str(bsr_raw).split('\n')
    main_cat = ''
    sub_cat = ''
    if lines:
        # 第一行：大类分类名
        m = re.search(r'in\s+([A-Za-z& ]+?)\s*\(', lines[0])
        if m:
            main_cat = m.group(1).strip()
    if len(lines) > 1:
        # 第二行：小类分类名
        m = re.search(r'#\d+\s+in\s+([^\n]+)', lines[1])
        if m:
            sub_cat = m.group(1).strip().rstrip(')')
    return main_cat, sub_cat


def build_rawdata_item(asin, data, history, related_asins=None, jike_data=None):
    """构建前端 rawData.items 格式（主ASIN或关联ASIN）"""
    price = safe_float(data.get('price', '')) or 0
    rating = safe_float(data.get('rating', '')) or 0
    review_count = safe_int(data.get('review_count', data.get('reviews', ''))) or 0
    main_bsr = extract_bsr(data)   # 大类排名
    sub_bsr = extract_sub_bsr(data)  # 小类排名
    title = data.get('title', data.get('product_title', ''))
    brand = data.get('brand', '')
    # 从 bsr 字符串解析大类和小类分类名
    bsr_raw = data.get('bsr', '')
    main_cat, sub_cat = parse_bsr_categories(bsr_raw)

    # ── 与上轮快照的变更检测 ──────────────────────────────────────
    prev_data = get_prev_snapshot_data(history)

    # 商品上下架状态（来自页面实际数据）
    listing_status = data.get('availability', data.get('listing_status', '正常'))

    # 标题变化
    title_changed = False
    if prev_data:
        prev_title = prev_data.get('title', '') or prev_data.get('product_title', '')
        curr_title = data.get('title', '') or data.get('product_title', '')
        title_changed = bool(prev_title and curr_title and prev_title != curr_title)

    # 主图变化
    img_changed = False
    if prev_data:
        prev_img = prev_data.get('main_image', '') or prev_data.get('img', '')
        curr_img = data.get('main_image', '') or data.get('img', '')
        img_changed = bool(prev_img and curr_img and prev_img != curr_img)

    # bullets / description 变化
    bullets_changed = False
    description_changed = False
    if prev_data:
        bullets_changed = bool(prev_data.get('bullets', []) != data.get('bullets', []))
        description_changed = bool(prev_data.get('description', '') != data.get('description', ''))

    # 变体关系变化
    variant_changed = False
    variant_status = "正常"
    if prev_data:
        prev_var = prev_data.get('variants', '')
        curr_var = data.get('variants', '')
        if curr_var != prev_var:
            variant_changed = True
            variant_status = "已变更"

    diff = build_diff(data, prev_data)

    # 积加数据（主ASIN有，关联ASIN无）
    jk = jike_data.get(asin, {}) if jike_data else {}

    return {
        "monitor_type": "ASIN",
        "asin": asin,
        "is_main": True,
        "logic_type": "主监控",
        "source_keyword": "",
        "title": title[:200],
        "brand": brand[:60] if brand else '',
        "img": data.get('main_image', data.get('img', '')),
        "price": price,
        "chg": 0.0,
        "rating": rating,
        "reviews": review_count,
        "diff": diff,
        "listing_status": listing_status,
        "expected_listing_status": "正常",
        "title_changed": title_changed,
        "img_changed": img_changed,
        "bullets_changed": bullets_changed,
        "description_changed": description_changed,
        "variant_status": variant_status,
        "variant_changed": variant_changed,
        "deal_activity": data.get('deal_activity', '无') or '无',
        "badges_current": data.get('badges', []) or [],
        "badges_lost": _calc_badges_lost(data.get('badges', []), prev_data.get('badges', []) if prev_data else []),
        "coupon": data.get('coupon', '无') or '无',
        "prime_discount": data.get('prime_discount', '未开启') or '未开启',
        "main_cat": main_cat,
        "expected_main_cat": main_cat,
        "main_bsr": main_bsr or 0,
        "sub_cat": sub_cat or '',
        "expected_sub_cat": sub_cat or '',
        "sub_bsr": sub_bsr or 0,
        "history_main_bsr": [h.get('bsr') or main_bsr for h in history] if history else [main_bsr or 0],
        "history_sub_bsr": [extract_sub_bsr(h) or sub_bsr for h in history] if history else [sub_bsr or 0],
        "history_price": [h.get('price') for h in history] if history else [price],
        "history_rating": [h.get('rating') for h in history] if history else [rating],
        "events": [],
        "related_asins": related_asins if related_asins else [],
                # 积加数据字段（仅主ASIN有，关联竞品/关键词ASIN不含此字段）
        "jike_sales": jk.get('orderProductSales'),
        "jike_orders": jk.get('orders'),
        "jike_units": jk.get('unitsOrdered'),
        "jike_session": jk.get('sessions'),
        "jike_page_views": jk.get('pageViews'),
        "jike_conversion_rate": jk.get('cvr'),
        "jike_rating": jk.get('star'),
        "jike_reviews": jk.get('reviewQuantity'),
        "jike_main_seller_rank": jk.get('mainSellerRank'),
        "jike_seller_rank": jk.get('sellerRank'),
        "jike_listing_state": jk.get('listingState'),
        "jike_product_name": jk.get('productName'),
        "jike_acos": jk.get('acos'),
        "jike_ads_spend": jk.get('adsSpend'),
        "jike_fba_quantity": jk.get('fbaQuantity'),
        "jike_fba_turnover": jk.get('fbaTurnover'),
        "jike_gross_profit_rate": jk.get('salesGrossProfitRate') or (jk.get('_raw') or {}).get('grossProfitRate'),
    }


def build_related_item(asin, rel_data, main_asin=None):
    """构建关联ASIN的独立items"""
    price = safe_float(rel_data.get('price', '')) or 0
    rating = safe_float(rel_data.get('rating', '')) or 0
    reviews = safe_int(rel_data.get('reviews', '')) or 0
    bsr_raw = rel_data.get('bsr', '')
    main_bsr = extract_bsr(rel_data) or 0
    sub_bsr = extract_sub_bsr(rel_data) or 0
    main_cat, sub_cat = parse_bsr_categories(bsr_raw)
    if not main_cat:
        main_cat = sub_cat

    return {
        "monitor_type": "ASIN",
        "asin": asin,
        "is_main": False,
        "logic_type": "关联竞品",
        "title": rel_data.get('title', '')[:200],
        "brand": rel_data.get('brand', '')[:60] if rel_data.get('brand') else '',
        "img": rel_data.get('img', ''),
        "price": price,
        "chg": 0.0,
        "rating": rating,
        "reviews": reviews,
        "diff": {},
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
        "sub_cat": sub_cat or main_cat,
        "expected_sub_cat": sub_cat or main_cat,
        "sub_bsr": sub_bsr,
        "history_main_bsr": [main_bsr],
        "history_sub_bsr": [sub_bsr],
        "events": [],
    }


def _load_asin_history(asin):
    """加载 ASIN 的历史快照（如果存在 asin_ 目录）"""
    d = os.path.join(DATA_DIR, f'asin_{asin}')
    if not os.path.isdir(d):
        return []
    snaps = sorted(glob.glob(os.path.join(d, 'snapshot_*.json')))
    history = []
    for sp in snaps:
        with open(sp, 'r', encoding='utf-8') as f:
            s = json.load(f)
        sd = s.get('data', s)
        history.append({
            'price': safe_float(sd.get('price', '')),
            'bsr': extract_bsr(sd),
            'rating': safe_float(sd.get('rating', '')),
            'timestamp': s.get('timestamp', '')
        })
    return history


def build_keyword_item(kw, a):
    """构建关键词找到的 ASIN 的独立 items"""
    asin_key = a.get('asin', '')
    # 尝试从 ASIN 独立目录加载完整数据（Phase A2 抓取后才有）
    asin_dir = os.path.join(DATA_DIR, f'asin_{asin_key}')
    asin_latest_path = os.path.join(asin_dir, 'latest.json')
    sd = None
    if os.path.exists(asin_latest_path):
        with open(asin_latest_path, 'r', encoding='utf-8') as f:
            sd = json.load(f).get('data', {})
    # 优先用快照数据，回退到关键词搜索结果
    snap_price = safe_float(sd.get('price', '') if sd else '')
    snap_rating = safe_float(sd.get('rating', '') if sd else '')
    snap_reviews = safe_int(sd.get('review_count', sd.get('reviews', '') if sd else '') if sd else '')
    price = snap_price if snap_price is not None else (safe_float(a.get('price', '')) or 0)
    rating = snap_rating if snap_rating is not None else (safe_float(a.get('rating', '')) or 0)
    reviews = snap_reviews if snap_reviews is not None else (safe_int(a.get('reviews', '')) or 0)
    bsr_raw = sd.get('bsr', '') if sd else ''
    main_bsr = extract_bsr({'bsr': bsr_raw}) if bsr_raw else None
    sub_bsr = extract_sub_bsr({'bsr': bsr_raw}) if bsr_raw else None
    main_cat, sub_cat = parse_bsr_categories(bsr_raw)
    if not main_cat and sd:
        main_cat = sd.get('bsr_subcategory', '') or ''
    # 历史快照
    history = _load_asin_history(asin_key)
    history_main_bsr = [h['bsr'] for h in history] if history else []
    history_sub_bsr = []
    for h in history:
        hs = extract_sub_bsr(h)
        history_sub_bsr.append(hs if hs is not None else (sub_bsr or 0))
    history_price = [h['price'] for h in history] if history else []
    history_rating = [h['rating'] for h in history] if history else []
    return {
        "monitor_type": "KW",
        "asin": asin_key,
        "is_main": False,
        "logic_type": f"关键词-{kw}",
        "title": a.get('title', '')[:200],
        "brand": (sd.get('brand', '') if sd else '')[:60] or a.get('brand', '')[:60] if a.get('brand') else '',
        "img": (sd.get('main_image', '') if sd else '') or a.get('main_image', a.get('img', '')),
        "price": price,
        "chg": 0.0,
        "rating": rating,
        "reviews": reviews,
        "diff": {},
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
        "main_bsr": main_bsr or 0,
        "sub_cat": sub_cat or '',
        "expected_sub_cat": sub_cat or '',
        "sub_bsr": sub_bsr or 0,
        "history_main_bsr": history_main_bsr,
        "history_sub_bsr": history_sub_bsr,
        "history_price": history_price,
        "history_rating": history_rating,
        "events": [],
    }


def main():
    items = []

    # ── 加载关键词竞品映射（ASIN → keyword）───────────────────────────────
    kw_related_file = os.path.join(os.path.dirname(DATA_DIR), 'keyword_related_asins.json')
    kw_asins = {}  # {asin: keyword}
    if os.path.exists(kw_related_file):
        with open(kw_related_file, 'r', encoding='utf-8') as f:
            kw_raw = json.load(f)
        for kw_name, asin_list in kw_raw.items():
            for a in asin_list:
                aasin = a.get('asin', '') if isinstance(a, dict) else (a if isinstance(a, str) else '')
                if aasin:
                    kw_asins[aasin] = kw_name

    # ── 加载 user_config related ASIN 集合（优先级高于关键词）────────────
    user_cfg_file = os.path.join(os.path.dirname(DATA_DIR), 'user_config.json')
    user_related = set()
    user_mains = set()
    if os.path.exists(user_cfg_file):
        with open(user_cfg_file, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        for entry in cfg.get('asins', []):
            if entry.get('main'):
                user_mains.add(entry['main'].strip())
            for ra in entry.get('related', []):
                if ra.strip():
                    user_related.add(ra.strip())
    # valid_asins = 主ASIN + 关联ASIN + keyword 竞品（只处理 config 中出现的）
    kw_only_asins = set(kw_asins.keys())
    valid_asins = user_mains | user_related | kw_only_asins
    print(f'[SYNC] Valid ASINs: {len(valid_asins)} (mains={len(user_mains)}, related={len(user_related)}, keyword={len(kw_only_asins)})')

    asin_dirs = sorted(glob.glob(os.path.join(DATA_DIR, 'asin_*')))
    print(f'[SYNC] Found {len(asin_dirs)} ASIN directories, filtering to config...')

    for d in asin_dirs:
        asin = os.path.basename(d).replace('asin_', '')
        latest_path = os.path.join(d, 'latest.json')
        if not os.path.exists(latest_path):
            continue
        with open(latest_path, 'r', encoding='utf-8') as f:
            latest = json.load(f)

        data = latest.get('data', latest)

        # 关联ASIN数据
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

        # 加载历史快照
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
                'review_count': safe_int(sd.get('review_count', sd.get('reviews', ''))),
                'data': sd
            })

        for sp in snapshots:
            with open(sp, 'r', encoding='utf-8') as f:
                snap = json.load(f)
            add_snap(snap, sp)
        add_snap(latest, None)
        all_snaps.sort(key=lambda x: x['timestamp'])

        # 跳过不在 config 中的 ASIN
        if asin not in valid_asins:
            continue

        # 加载积加数据（仅主ASIN有积加数据文件）
        jike_data = load_jike_data(asin)

        item = build_rawdata_item(asin, data, all_snaps, jike_data=jike_data)
        # 判断 ASIN 来源：user_related > keyword > 主ASIN
        if asin in user_related:
            item['monitor_type'] = 'ASIN'
            item['logic_type'] = '关联竞品'
            item['is_main'] = False
            # 关联竞品无积加数据，清理字段
            for jf in JIKE_FIELDS:
                item.pop(jf, None)
        elif asin in kw_asins:
            item['monitor_type'] = 'KW'
            item['logic_type'] = '关键词-' + kw_asins[asin]
            item['source_keyword'] = kw_asins[asin]
            item['is_main'] = False
            # 关键词 ASIN 无积加数据，清理字段
            for jf in JIKE_FIELDS:
                item.pop(jf, None)
        # 否则保持 build_rawdata_item 默认值（主监控），保留积加数据
        items.append(item)

        # 每个关联ASIN也作为独立行输出（仅输出 config 中指定的关联ASIN）
        if related_asins:
            rt_data = data.get('_related_asins', [])
            rt_map = {r.get('asin', ''): r for r in rt_data}
            for ra in meta['related_asins']:
                asin_key = ra.get('asin', '')
                if asin_key in user_related:
                    rt = rt_map.get(asin_key, {})
                    rel_item = build_related_item(asin_key, rt)
                    items.append(rel_item)

        if related_asins:
            print(f'  related={len(related_asins)}', end='')
        print()

    # ── 关键词数据（先收集 kw_asins，再标记到 ASIN items） ────
    keywords_data = []
    kw_asins = {}  # {asin: keyword} for ASINs found via keyword search
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
        for a in top_asins:
            asin_key = a.get('asin', '')
            if asin_key:
                kw_asins[asin_key] = {'keyword': kw, 'rank': a.get('rank', '')}
        print(f'  kw [{kw}]: {len(top_asins)} top ASINs')

    # keyword 来源已在主循环中标记完毕

    output = {
        'updated': datetime.now().isoformat()[:19],
        'items': items,
        'keywords': keywords_data
    }

    os.makedirs(os.path.dirname(OUTPUT_RAW), exist_ok=True)
    with open(OUTPUT_RAW, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n✅ Written {len(items)} items + {len(keywords_data)} keywords to {OUTPUT_RAW}')

    # ── 自动推送到 GitHub ────────────────────────────────────────
    try:
        subprocess.run(['git', 'add', OUTPUT_RAW], capture_output=True, cwd=BASE)
        diff = subprocess.run(['git', 'diff', '--cached', '--stat'], capture_output=True, text=True, cwd=BASE)
        if diff.stdout.strip():
            subprocess.run(['git', 'commit', '-m', 'auto: sync rawData.json with keywords + diff'], capture_output=True, cwd=BASE)
            result = subprocess.run(['git', 'push'], capture_output=True, text=True, cwd=BASE)
            if result.returncode == 0:
                print('🚀 rawData.json 已推送至 GitHub')
            else:
                print('⚠️ 推送失败:', result.stderr[:200])
        else:
            print('ℹ️ rawData.json 无变化，跳过推送')
    except Exception as e:
        print(f'⚠️ Git 推送异常: {e}')

    # ── 钉钉预警检查 ─────────────────────────────────────────────
    try:
        from dingtalk_notifier import check_and_notify
        check_and_notify()
    except Exception as e:
        print(f'⚠️ 钉钉预警异常: {e}')


if __name__ == '__main__':
    main()