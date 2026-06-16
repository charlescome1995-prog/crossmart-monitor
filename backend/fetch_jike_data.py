#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_jike_data.py - 获取积加数据
优先调用积加 API，API 不可用时（IP 不在白名单等）用插件数据作为后备
生成 processed/asin_ASIN/jike_latest.json
"""
import sys, os, json, time, re
sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = PROJECT_ROOT  # PROJECT_ROOT = 项目根目录 = crossmart-monitor/
DATA_DIR = os.path.join(BASE, 'backend', 'data', 'processed')
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'backend'))
import jike_client

from jike_client import get_jike_data_for_asins, load_config

JIKE_FIELDS = [
    'jike_sales', 'jike_orders', 'jike_units', 'jike_session',
    'jike_page_views', 'jike_conversion_rate', 'jike_rating', 'jike_reviews',
    'jike_main_seller_rank', 'jike_seller_rank', 'jike_listing_state',
    'jike_product_name', 'jike_acos', 'jike_ads_spend',
    'jike_fba_quantity', 'jike_fba_turnover', 'jike_gross_profit_rate',
]


def _load_snapshot(asin):
    """从 latest.json 加载快照数据"""
    path = os.path.join(DATA_DIR, f'asin_{asin}', 'latest.json')
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        snap = json.load(f)
    return snap.get('data', {})


def _build_sprite_fallback(asin):
    """
    从快照的 sprite_ 字段构建积加格式的后备数据
    插件字段 → 积加字段映射
    """
    data = _load_snapshot(asin)
    if not data:
        return {}

    # 检查是否有 sprite_ 字段（插件数据）
    sprite_keys = [k for k in data.keys() if k.startswith('sprite_')]
    if not sprite_keys:
        return {}

    s = {}
    # 销量(30天父体) → unitsOrdered
    raw_sales = data.get('sprite_sales_30d_parent', '')
    if raw_sales:
        s['unitsOrdered'] = int(raw_sales.replace(',', '')) if raw_sales.replace(',', '').isdigit() else None
    else:
        raw_sales = data.get('sprite_unitsOrdered', '')
        s['unitsOrdered'] = int(raw_sales) if raw_sales and raw_sales.isdigit() else None

    # 销售额 → orderProductSales
    raw_rev = data.get('sprite_revenue_30d', '')
    if raw_rev:
        s['orderProductSales'] = float(raw_rev.replace(',', '')) if raw_rev.replace(',', '').replace('.', '').isdigit() else None
    else:
        raw_rev = data.get('sprite_orderProductSales', '')
        s['orderProductSales'] = float(raw_rev) if raw_rev and raw_rev.replace(',', '').replace('.', '').isdigit() else None

    # 订单量（插件无此字段，设为 None）
    s['orders'] = None

    # 毛利率 → grossProfitRate / salesGrossProfitRate
    raw_margin = data.get('sprite_gross_margin', '')
    if raw_margin and '%' in raw_margin:
        try:
            s['salesGrossProfitRate'] = float(raw_margin.replace('%', ''))
        except:
            s['salesGrossProfitRate'] = None
    else:
        s['salesGrossProfitRate'] = None

    # FBA费用 → fbaFee（不是积加标准字段，但前端不用）
    raw_fba = data.get('sprite_fba_fee', '')
    s['fbaFee'] = float(raw_fba) if raw_fba and raw_fba.replace('.', '').isdigit() else None

    # 配送类型 → fulfillment
    s['fulfillment'] = data.get('sprite_fulfillment', '')

    # 卖家精灵的其他字段也一并传入（前端直接从 sprite_ 字段读取）
    s['_sprite'] = {
        'lqs': data.get('sprite_lqs', ''),
        'variant_count': data.get('sprite_variant_count', ''),
        'launch_date': data.get('sprite_launch_date', data.get('launch_date', '')),
        'total_keywords': data.get('sprite_total_keywords', ''),
        'natural_keywords': data.get('sprite_natural_keywords', ''),
        'ad_keywords': data.get('sprite_ad_keywords', ''),
        'suggest_keywords': data.get('sprite_suggest_keywords', ''),
        'traffic_keywords_top': data.get('sprite_traffic_keywords_top', []),
        'sales_30d_parent': data.get('sprite_sales_30d_parent', ''),
        'revenue_30d': data.get('sprite_revenue_30d', ''),
        'gross_margin': data.get('sprite_gross_margin', ''),
    }

    return s


def fetch_for_asins(asin_list):
    """
    主入口：获取 ASIN 列表的积加数据
    优先 API，失败则插件后备
    返回: {asin: {积加字段...}}
    """
    config = load_config()
    if not config or not config.get('appId'):
        print('[积加] 未配置 appId，使用插件后备')
        return _fetch_all_from_sprite(asin_list)

    try:
        print('[积加] 尝试调用积加 API...')
        jike_data = get_jike_data_for_asins(asin_list)
        # 检查是否有有效数据（API 可能返回空列表）
        valid_asins = [a for a in asin_list if jike_data.get(a)]
        if valid_asins:
            print(f'[积加] API 返回 {len(valid_asins)} 个 ASIN 的数据')
            return jike_data
        print('[积加] API 返回空数据，尝试插件后备')
    except Exception as e:
        err_msg = str(e)
        # 检查是否是 IP 白名单错误
        if '40302' in err_msg or '无访问权限' in err_msg:
            print(f'[积加] API IP 无权限: {e}，使用插件后备')
        elif '400' in err_msg:
            print(f'[积加] API 凭证错误: {e}，使用插件后备')
        else:
            print(f'[积加] API 调用失败: {e}，使用插件后备')

    # API 不可用 → 从插件数据构建后备
    return _fetch_all_from_sprite(asin_list)


def _fetch_all_from_sprite(asin_list):
    """从快照的插件字段构建后备积加数据"""
    result = {}
    for asin in asin_list:
        asin = asin.strip()
        if not asin:
            continue
        fallback = _build_sprite_fallback(asin)
        if fallback:
            print(f'[积加后备] ASIN {asin}: 销量={fallback.get("unitsOrdered")}, 销售额={fallback.get("orderProductSales")}')
        else:
            print(f'[积加后备] ASIN {asin}: 无插件数据')
        result[asin] = fallback
    return result


def save_jike_latest(asin, jike_data):
    """保存单个 ASIN 的积加数据到 jike_latest.json"""
    d = os.path.join(DATA_DIR, f'asin_{asin}')
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, 'jike_latest.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(jike_data, f, ensure_ascii=False, indent=2)
    print(f'[积加] 已保存 jike_latest.json → {asin}')


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--asins', default='', help='逗号分隔的ASIN列表')
    parser.add_argument('--all', action='store_true', help='处理所有有快照的ASIN')
    args = parser.parse_args()

    if args.all:
        asins = []
        for d in os.listdir(DATA_DIR):
            if d.startswith('asin_'):
                asins.append(d.replace('asin_', ''))
    elif args.asins:
        asins = [a.strip() for a in args.asins.split(',') if a.strip()]
    else:
        print('用法: python fetch_jike_data.py --asins B0XXXXXXX,B0YYYYYYY')
        print('   或: python fetch_jike_data.py --all')
        return

    if not asins:
        print('无 ASIN 可处理')
        return

    print(f'处理 {len(asins)} 个 ASIN: {asins}')
    jike_data = fetch_for_asins(asins)

    for asin, data in jike_data.items():
        save_jike_latest(asin, data)

    print(f'\n✅ 完成，{len(jike_data)} 个 ASIN')


if __name__ == '__main__':
    main()