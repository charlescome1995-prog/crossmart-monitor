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
    'jike_net_profit_rate', 'jike_avg_daily_sales', 'jike_window',
    'jike_fba_turnover_unit',
]


def load_jike_data(asin):
    """
    从 processed/asin_ASIN/jike_latest.json 加载积加数据。

    **严格语义**：仅在积加 API 成功调用且返回有效字段时才返回数据。
    - 文件不存在 → 返回 {}
    - 文件存在但是 {}（API 调用失败 / 无数据） → 返回 {}
    - 文件含 _error 标记 → 返回含 _error 的 dict，sync 会把错误传递到前端
    - 卖家精灵 (sprite_*) 不再充作积加后备 — 积加数据只能从积加调用

    返回格式：始终是扁平的 {orderProductSales:..., unitsOrdered:..., ...}
    支持检测嵌套格式 {asin: data}（jike_client 原始格式）并自动解包。
    """
    path = os.path.join(DATA_DIR, f'asin_{asin}', 'jike_latest.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = json.load(f)
    except Exception:
        return {}

    # 错误标记：API 调用失败的 jike_latest.json → 保留 _error，sync 接过去处理
    if isinstance(content, dict) and content.get('_error'):
        return {'_error': content['_error'], '_failed_at': content.get('_failed_at', '')}

    # 嵌套格式：{asin: data} → unwrap 到 {data}
    if isinstance(content, dict) and asin in content and isinstance(content[asin], dict):
        content = content[asin]

    # 如果积加 API 返回了有效数据，返回
    if content and isinstance(content, dict) and any(content.values()):
        return content

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
    # ── helpers (defined before the None check so first-scrape branch can use them) ──
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

    if prev_data is None:
        # First scrape: show all current values as "no change yet" (direction=same, change=0)
        p_c = cf('price'); r_c = cf('rating'); rc_c = ci('review_count')
        b_c = extract_bsr(curr_data); sb_c = extract_sub_bsr(curr_data)
        diff = {}
        if p_c is not None:
            diff['price'] = {'current': p_c, 'prev': p_c, 'change': '0', 'pct': '0%', 'direction': 'same'}
        if r_c is not None:
            diff['rating'] = {'current': r_c, 'prev': r_c, 'change': '0', 'direction': 'same'}
        if rc_c is not None:
            diff['review_count'] = {'current': rc_c, 'prev': rc_c, 'change': '0', 'direction': 'same'}
        if b_c is not None:
            diff['bsr'] = {'current': b_c, 'prev': b_c, 'change': '0', 'direction': 'same'}
        if sb_c is not None:
            diff['sub_bsr'] = {'current': sb_c, 'prev': sb_c, 'change': '0', 'direction': 'same'}
        return diff

    diff = {}

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
    """从 history 列表中取出倒数第二个快照的 data（用于 diff）"""
    if len(history) == 0:
        return None
    snap = history[-2] if len(history) >= 2 else history[-1]
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
        bullets_changed = bool(prev_data.get('features', []) != data.get('features', []))
        description_changed = bool(prev_data.get('description', '') != data.get('description', ''))

    # 卖家变化
    seller_changed = False
    if prev_data:
        prev_seller = prev_data.get('soldBy', '') or prev_data.get('sold_by', '')
        curr_seller = data.get('soldBy', '') or data.get('sold_by', '')
        seller_changed = bool(prev_seller and curr_seller and prev_seller != curr_seller)

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
    jk_raw = jike_data if jike_data else {}
    # 检查是否为错误标记：是则所有积加字段返 None，同时用 jike_error 字段传递错误信息
    jike_error = jk_raw.get('_error') if isinstance(jk_raw, dict) else None
    jk = {} if jike_error else jk_raw

    return {
        "monitor_type": data.get("_asin_type") or "ASIN",
        "asin": asin,
        "is_main": not not data.get("_source_keyword"),
        "is_stale": bool(data.get("_stale")),
        "logic_type": ("稳定ASIN" if data.get("_asin_type") == "stable" else
                         "变化ASIN" if data.get("_asin_type") == "variable" else
                         "主监控"),
        "source_keyword": data.get("_source_keyword") or "",
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
        "seller_changed": seller_changed,
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
        "jike_fba_turnover_unit": "天",  # 2026-06-30 标注单位
        "jike_gross_profit_rate": jk.get('grossProfitRate') or jk.get('salesGrossProfitRate'),  # A:毛利率
        "jike_net_profit_rate": jk.get('salesNetProfitRate'),  # B:净利率
        "jike_avg_daily_sales": jk.get('averageDailySales'),  # 日均销量
        "jike_window": "昨日T+1",  # 2026-06-30 改为 1 天窗口（昨日，积加有 T+1 延迟）
        "jike_error": jike_error,  # 积加调用失败时的错误信息（None表示成功或未调用）

        # ── 卖家精灵插件数据 ──
        "lqs": data.get('sprite_lqs', ''),
        "variant_count": data.get('sprite_variant_count', ''),
        "launch_date": data.get('launch_date', '') or data.get('sprite_launch_date', ''),
        # 2026-06-30 防呆：1688 是 Alibaba 子站名，不可能是关键词数
        "total_keywords": '' if str(data.get('sprite_total_keywords', '')) == '1688' else data.get('sprite_total_keywords', ''),
        "natural_keywords": '' if str(data.get('sprite_natural_keywords', '')) == '1688' else data.get('sprite_natural_keywords', ''),
        "ad_keywords": '' if str(data.get('sprite_ad_keywords', '')) == '1688' else data.get('sprite_ad_keywords', ''),
        # 卖家精灵估算（与 jike_* 严格区分，不冒充积加真实数据；None 表示插件未抓到）
        "seller_units_30d": safe_int(data.get('sprite_sales_30d_parent', '')),
        "seller_revenue_30d": safe_float(data.get('sprite_revenue_30d', '')),
        "seller_avg_price": safe_float(data.get('sprite_avg_price', '')),
        "seller_rating": safe_float(data.get('sprite_rating', '')),
        "seller_review_count": safe_int(data.get('sprite_review_count', '')),
        "seller_bsr": safe_int(data.get('sprite_bsr_rank', '')),
        "seller_fba_fee": safe_float(data.get('sprite_fba_fee', '')),
        "suggest_keywords": '' if str(data.get('sprite_suggest_keywords', '')) == '1688' else data.get('sprite_suggest_keywords', ''),
        "traffic_keywords_top": data.get('sprite_traffic_keywords_top', []),
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

    # ── 变化对比：有历史则计算差值，无历史则返回 diff=0 ──
    history = _load_asin_history(asin)
    prev_data = get_prev_snapshot_data(history)
    diff = build_diff(rel_data, prev_data)

    # ── 历史轨迹：有快照则用真实历史，否则用当前值做单点占位 ──
    hist_price = []
    hist_rating = []
    if history:
        hist_main_bsr = [extract_bsr(h.get('data', h)) or main_bsr for h in history]
        hist_sub_bsr  = [extract_sub_bsr(h.get('data', h)) or sub_bsr for h in history]
        for h in history:
            hd = h.get('data', h)
            hist_price.append(safe_float(hd.get('price', '')) or price)
            hist_rating.append(safe_float(hd.get('rating', '')) or rating)
    else:
        hist_main_bsr = [main_bsr]
        hist_sub_bsr  = [sub_bsr]
        hist_price    = [price]
        hist_rating   = [rating]

    return {
        "monitor_type": "ASIN",
        "asin": asin,
        "is_main": False,
        "logic_type": "关联竞品",
        "title": rel_data.get('title', '')[:200],
        "brand": (rel_data.get('brand', '') if rel_data.get('brand') else '')[:60],
        "img": rel_data.get('main_image', '') or rel_data.get('img', ''),
        "price": price,
        "chg": 0.0,
        "rating": rating,
        "reviews": reviews,
        "diff": diff,
        "listing_status": (rel_data.get('listing_status', '') if rel_data.get('listing_status', '') else '') or "正常",
        "expected_listing_status": (rel_data.get('expected_listing_status', '') if rel_data.get('expected_listing_status', '') else '') or "正常",
        "title_changed": False,
        "img_changed": False,
        "bullets_changed": False,
        "description_changed": False,
        "variant_status": (rel_data.get('variant_status', '') if rel_data.get('variant_status', '') else '') or "正常",
        "variant_changed": False,
        "deal_activity": (rel_data.get('deal_activity', '') if rel_data.get('deal_activity', '') else '') or "无",
        "badges_current": rel_data.get('badges', []) or [],
        "badges_lost": [],
        "coupon": (rel_data.get('coupon', '') if rel_data.get('coupon', '') else '') or "无",
        "prime_discount": (rel_data.get('prime_discount', '') if rel_data.get('prime_discount', '') else '') or "未开启",
        "main_cat": main_cat,
        "expected_main_cat": main_cat,
        "main_bsr": main_bsr,
        "sub_cat": sub_cat or main_cat,
        "expected_sub_cat": sub_cat or main_cat,
        "sub_bsr": sub_bsr,
        "history_main_bsr": hist_main_bsr,
        "history_sub_bsr": hist_sub_bsr,
        "history_price": hist_price,
        "history_rating": hist_rating,
        "history_price": hist_price if history else [price],
        "history_rating": hist_rating if history else [rating],
        "events": [],

        # ── 卖家精灵插件数据 ──
        "lqs": rel_data.get('sprite_lqs', ''),
        "variant_count": rel_data.get('sprite_variant_count', ''),
        "launch_date": (rel_data.get('launch_date', '') if rel_data.get('launch_date', '') else '') or (rel_data.get('sprite_launch_date', '') if rel_data.get('sprite_launch_date', '') else '') or '',
        "total_keywords": '' if str(rel_data.get('sprite_total_keywords', '')) == '1688' else rel_data.get('sprite_total_keywords', ''),
        "natural_keywords": '' if str(rel_data.get('sprite_natural_keywords', '')) == '1688' else rel_data.get('sprite_natural_keywords', ''),
        "ad_keywords": '' if str(rel_data.get('sprite_ad_keywords', '')) == '1688' else rel_data.get('sprite_ad_keywords', ''),
        "suggest_keywords": '' if str(rel_data.get('sprite_suggest_keywords', '')) == '1688' else rel_data.get('sprite_suggest_keywords', ''),
        "traffic_keywords_top": rel_data.get('sprite_traffic_keywords_top', []) or [],
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
    # ── 变化对比：有历史则计算差值，无历史则返回 diff=0 ──
    # 优先用 latest.json（Phase A2 完整抓取），回退到关键词搜索结果（数据较少）
    curr_data_for_diff = sd if sd else {
        'price': a.get('price', ''),
        'rating': a.get('rating', ''),
        'review_count': a.get('reviews', ''),
        'bsr': bsr_raw,
    }
    kw_prev_data = get_prev_snapshot_data(history)
    kw_diff = build_diff(curr_data_for_diff, kw_prev_data)

    # ── 历史轨迹：有快照则用真实历史，否则用当前值做单点占位 ──
    if history:
        kw_hist_main_bsr = [h['bsr'] for h in history]
        kw_hist_sub_bsr  = [extract_sub_bsr(h) or (sub_bsr or 0) for h in history]
        kw_hist_price    = [h['price'] for h in history]
        kw_hist_rating   = [h['rating'] for h in history]
    else:
        kw_hist_main_bsr = [main_bsr or 0]
        kw_hist_sub_bsr  = [sub_bsr or 0]
        kw_hist_price    = [price]
        kw_hist_rating   = [rating]

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
        "diff": kw_diff,
        "listing_status": (sd.get('listing_status', '') if sd else '') or "正常",
        "expected_listing_status": (sd.get('expected_listing_status', '') if sd else '') or "正常",
        "title_changed": False,
        "img_changed": False,
        "bullets_changed": False,
        "description_changed": False,
        "variant_status": (sd.get('variant_status', '') if sd else '') or "正常",
        "variant_changed": False,
        "deal_activity": (sd.get('deal_activity', '') if sd else '') or "无",
        "badges_current": [],
        "badges_lost": [],
        "coupon": (sd.get('coupon', '') if sd else '') or "无",
        "prime_discount": (sd.get('prime_discount', '') if sd else '') or "未开启",
        "main_cat": main_cat,
        "expected_main_cat": main_cat,
        "main_bsr": main_bsr or 0,
        "sub_cat": sub_cat or '',
        "expected_sub_cat": sub_cat or '',
        "sub_bsr": sub_bsr or 0,
        "history_main_bsr": kw_hist_main_bsr,
        "history_sub_bsr": kw_hist_sub_bsr,
        "history_price": kw_hist_price,
        "history_rating": kw_hist_rating,
        "events": [],

        # ── 卖家精灵插件数据 ──
        "lqs": (sd.get('sprite_lqs', '') if sd else '') or '',
        "variant_count": (sd.get('sprite_variant_count', '') if sd else '') or '',
        "launch_date": (sd.get('launch_date', '') if sd else '') or (sd.get('sprite_launch_date', '') if sd else '') or '',
        "total_keywords": '' if (sd and str(sd.get('sprite_total_keywords', '')) == '1688') else ((sd.get('sprite_total_keywords', '') if sd else '') or ''),
        "natural_keywords": '' if (sd and str(sd.get('sprite_natural_keywords', '')) == '1688') else ((sd.get('sprite_natural_keywords', '') if sd else '') or ''),
        "ad_keywords": '' if (sd and str(sd.get('sprite_ad_keywords', '')) == '1688') else ((sd.get('sprite_ad_keywords', '') if sd else '') or ''),
        "suggest_keywords": '' if (sd and str(sd.get('sprite_suggest_keywords', '')) == '1688') else ((sd.get('sprite_suggest_keywords', '') if sd else '') or ''),
        "traffic_keywords_top": (sd.get('traffic_keywords_top', []) if sd else []) or [],
    }


def main():
    items = []
    seen_asins = {}  # {asin: item} 优先保留数据更完整的条目

    def _completeness(item):
        """评分函数：数据越完整分数越高"""
        score = 0
        if item.get('title'): score += 1
        if item.get('img'): score += 2      # 图片最重要，权重最高
        if item.get('price'): score += 1
        if item.get('rating'): score += 1
        if item.get('reviews'): score += 1
        if item.get('main_bsr'): score += 1
        return score

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
    config_keywords = []          # 当前 config 配置的关键词（保持顺序、去重）
    config_keywords_norm = {}     # {归一化目录名: 原始关键词} 用于匹配磁盘目录
    if os.path.exists(user_cfg_file):
        with open(user_cfg_file, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        for entry in cfg.get('asins', []):
            if entry.get('main'):
                user_mains.add(entry['main'].strip())
            for ra in entry.get('related', []):
                if ra.strip():
                    user_related.add(ra.strip())
        # 收集当前配置的关键词（按顺序、去重）
        _seen_kw = set()
        for kentry in cfg.get('keywords', []):
            kw_main = (kentry.get('main') or '').strip()
            if not kw_main:
                continue
            _norm = kw_main.lower()
            if _norm in _seen_kw:
                continue
            _seen_kw.add(_norm)
            config_keywords.append(kw_main)
            # 归一化为目录名样式：空格/斜杠 → 下划线，小写
            _dirkey = kw_main.replace(' ', '_').replace('/', '_').lower()
            config_keywords_norm[_dirkey] = kw_main
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
        # 判断 ASIN 来源：主ASIN > user_related > keyword，未设时按归属兑底
        asin_type = data.get('_asin_type', '')
        if asin in user_mains:
            # 主ASIN：保留全部 jike_* 字段；保持 build_rawdata_item 的默认 monitor_type/logic_type
            item['is_main'] = True
            item['source_keyword'] = ''
        elif asin in user_related:
            item['is_main'] = False
            # 关联竞品无积加数据，清理字段
            for jf in JIKE_FIELDS:
                item.pop(jf, None)
            # 只有 _asin_type 未设时才覆盖（保持默认）
            if not asin_type:
                item['monitor_type'] = 'ASIN'
                item['logic_type'] = '关联竞品'
        elif asin in kw_asins:
            item['is_main'] = False
            item['source_keyword'] = kw_asins[asin]
            # 关键词 ASIN 无积加数据，清理字段
            for jf in JIKE_FIELDS:
                item.pop(jf, None)
            # 只有 _asin_type 未设时才覆盖为 KW（build_rawdata_item 已处理 stable/variable）
            if not asin_type:
                item['monitor_type'] = 'KW'
                item['logic_type'] = '关键词-' + kw_asins[asin]
        # 否则保持 build_rawdata_item 默认值（主监控），保留积加数据
        if asin not in seen_asins:
            seen_asins[asin] = item
        else:
            old_score = _completeness(seen_asins[asin])
            new_score = _completeness(item)
            if new_score > old_score:
                print(f"  [去重] {asin} 保留更完整数据（{old_score}→{new_score}）")
                seen_asins[asin] = item
            else:
                print(f"  [去重] {asin} 数据不足（{new_score}<{old_score}），跳过")

        # 每个关联ASIN也作为独立行输出（仅输出 config 中指定的关联ASIN）
        if related_asins:
            rt_data = data.get('_related_asins', [])
            rt_map = {r.get('asin', ''): r for r in rt_data}
            for ra in meta['related_asins']:
                asin_key = ra.get('asin', '')
                if asin_key in user_related:
                    rt = rt_map.get(asin_key, {})
                    rel_item = build_related_item(asin_key, rt)
                    if asin_key not in seen_asins:
                        seen_asins[asin_key] = rel_item
                    else:
                        old_score = _completeness(seen_asins[asin_key])
                        new_score = _completeness(rel_item)
                        if new_score > old_score:
                            print(f"  [去重] {asin_key} 关联竞品保留更完整数据（{old_score}→{new_score}）")
                            seen_asins[asin_key] = rel_item
                        else:
                            print(f"  [去重] {asin_key} 关联竞品数据不足（{new_score}<{old_score}），跳过")

        if related_asins:
            print(f'  related={len(related_asins)}', end='')
        print()

    # ── 关键词数据（先收集 kw_asins，再标记到 ASIN items） ────
    # 只输出当前 user_config 配置的关键词，按 config 顺序，去重，忽略磁盘上残留的旧关键词目录
    keywords_data = []
    kw_asins = {}  # {asin: keyword} for ASINs found via keyword search
    all_kw_dirs = sorted(glob.glob(os.path.join(DATA_DIR, 'kw_*')))
    # 建立 归一化目录名 → 目录路径 的映射
    dir_by_norm = {}
    for d in all_kw_dirs:
        _norm = os.path.basename(d).replace('kw_', '').lower()
        dir_by_norm[_norm] = d

    if config_keywords:
        # 按 config 顺序选取对应目录（无配置则回退到全部目录，保持兼容）
        ordered_dirs = []
        for _dirkey in config_keywords_norm:
            d = dir_by_norm.get(_dirkey)
            if d:
                ordered_dirs.append(d)
            else:
                print(f'  [SYNC] 关键词 "{config_keywords_norm[_dirkey]}" 暂无抓取目录，跳过')
        kw_dirs = ordered_dirs
        skipped = [os.path.basename(d) for d in all_kw_dirs if d not in ordered_dirs]
        if skipped:
            print(f'[SYNC] 忽略 {len(skipped)} 个非当前配置的旧关键词目录: {skipped}')
    else:
        kw_dirs = all_kw_dirs
    print(f'[SYNC] Using {len(kw_dirs)} keyword directories (config has {len(config_keywords)} keywords)')

    _emitted_kw = set()  # 防止重复输出同一关键词
    for d in kw_dirs:
        kw = os.path.basename(d).replace('kw_', '').replace('_', ' ')
        if kw.lower() in _emitted_kw:
            continue
        _emitted_kw.add(kw.lower())
        latest_path = os.path.join(d, 'latest.json')
        if not os.path.exists(latest_path):
            continue
        with open(latest_path, 'r', encoding='utf-8') as f:
            latest = json.load(f)

        inner = latest.get('data', latest)
        top_asins = inner.get('top_asins', [])

        # Build enriched top_asins with full snapshot data
        _top_asins_full = []
        for _a in top_asins:
            _asin_key = _a.get('asin', '')
            _asin_dir = os.path.join(DATA_DIR, f'asin_{_asin_key}')
            _asin_latest = os.path.join(_asin_dir, 'latest.json')
            _sd = None
            if os.path.exists(_asin_latest):
                try:
                    with open(_asin_latest, 'r', encoding='utf-8') as _f:
                        _sd = json.load(_f).get('data', {})
                except:
                    pass
            _top_asins_full.append({
                "asin": _asin_key,
                "type": _a.get('type', ''),
                "rank": _a.get('rank', ''),
                "title": _a.get('title', '')[:200],
                "price": (_sd.get('price', '') if _sd else '') or _a.get('price', ''),
                "rating": (_sd.get('rating', '') if _sd else '') or _a.get('rating', ''),
                "reviews": (_sd.get('review_count', _sd.get('reviews', '')) if _sd else '') or _a.get('reviews', ''),
                "launch_date": (_sd.get('launch_date', '') if _sd else '') or '',
                "listing_status": (_sd.get('listing_status', '') if _sd else '') or '',
                "deal_activity": (_sd.get('deal_activity', '') if _sd else '') or '',
                "coupon": (_sd.get('coupon', '') if _sd else '') or '',
                "prime_discount": (_sd.get('prime_discount', '') if _sd else '') or '',
            })


        keywords_data.append({
            "keyword": kw,
            "top_asins": _top_asins_full,
        })
        for a in top_asins:
            asin_key = a.get('asin', '')
            if asin_key:
                kw_asins[asin_key] = {'keyword': kw, 'rank': a.get('rank', '')}
        print(f'  kw [{kw}]: {len(top_asins)} top ASINs')

    # keyword 来源已在主循环中标记完毕

    # ── 去重完成：将 seen_asins 字典写回 items 列表 ──
    items = list(seen_asins.values())

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
            # 先 pull --rebase 同步远程变更，避免 push 被拒
            pull = subprocess.run(['git', 'pull', '--rebase', '--autostash', 'origin', 'main'], capture_output=True, text=True, cwd=BASE)
            if pull.returncode != 0:
                print('⚠️ pull --rebase 失败:', pull.stderr[:200])
            push = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True, cwd=BASE)
            if push.returncode == 0:
                print('🚀 rawData.json 已推送至 GitHub')
            else:
                print('⚠️ 推送失败:', push.stderr[:200])
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