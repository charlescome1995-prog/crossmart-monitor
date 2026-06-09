#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dingtalk_notifier.py - 钉钉预警推送
条件：
  1. ACOS 超过 40%
  2. FBA 库存少于 14 天
"""
import json, os, sys, subprocess, re

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'data', 'processed')

# 钉钉机器人 Webhook（从 user_config.json 读取，不硬编码）
CONFIG_FILE = os.path.join(BASE, 'data', 'user_config.json')
WEBHOOK_URL = None

# 预警阈值
ACOS_THRESHOLD = 40.0       # ACOS > 40% 预警
INVENTORY_DAYS_THRESHOLD = 14  # FBA 库存 < 14 天预警


def load_webhook_url():
    global WEBHOOK_URL
    if WEBHOOK_URL:
        return WEBHOOK_URL
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        WEBHOOK_URL = cfg.get('dingtalk_webhook_url') or cfg.get('webhook_url')
        return WEBHOOK_URL
    except Exception:
        return None


def send_dingtalk(message):
    """发送钉钉消息（无签字版本）"""
    url = load_webhook_url()
    if not url:
        print('[DingTalk] 未配置 webhook_url，跳过推送')
        return False

    # 构造请求体（text 类型）
    payload = {
        "msgtype": "text",
        "text": {
            "content": message
        }
    }

    # 尝试用 requests，发不了则用 PowerShell
    try:
        import requests
        resp = requests.post(url, json=payload, timeout=10)
        result = resp.json()
        if result.get('errcode') == 0:
            print('[DingTalk] ✅ 推送成功')
            return True
        else:
            print(f'[DingTalk] ❌ 推送失败: {result}')
            return False
    except ImportError:
        # 没有 requests，用 PowerShell Invoke-WebRequest
        import json as _json
        body = _json.dumps(payload)
        cmd = [
            'powershell', '-NoProfile', '-Command',
            f'(Invoke-WebRequest -Uri "{url}" -Method Post -ContentType "application/json" -Body \'{body}\' -TimeoutSec 10).Content'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            resp_data = json.loads(result.stdout.strip())
            if resp_data.get('errcode') == 0:
                print('[DingTalk] ✅ 推送成功')
                return True
            else:
                print(f'[DingTalk] ❌ 推送失败: {resp_data}')
                return False
        except Exception as e:
            print(f'[DingTalk] ❌ 解析响应失败: {e}, raw: {result.stdout[:200]}')
            return False
    except Exception as e:
        print(f'[DingTalk] ❌ 推送异常: {e}')
        return False


def check_and_notify():
    """
    遍历所有 ASIN 的积加数据，检查预警条件并推送钉钉
    返回是否发送了预警
    """
    url = load_webhook_url()
    if not url:
        print('[Alert] 未配置钉钉 Webhook，跳过')
        return False

    alerts = []
    asin_dirs = sorted(glob.glob(os.path.join(DATA_DIR, 'asin_*')))
    print(f'[Alert] 检查 {len(asin_dirs)} 个 ASIN...')

    for d in asin_dirs:
        asin = os.path.basename(d).replace('asin_', '')
        jike_path = os.path.join(d, 'jike_latest.json')
        if not os.path.exists(jike_path):
            continue

        try:
            with open(jike_path, 'r', encoding='utf-8') as f:
                jike_raw = json.load(f)
        except Exception:
            continue

        # 支持两种格式：顶层 key 是 ASIN，或直接是数据对象
        jike = None
        if isinstance(jike_raw, dict):
            if asin in jike_raw:
                jike = jike_raw[asin]
            elif 'acos' in jike_raw:
                jike = jike_raw

        if not jike:
            continue

        acos = _safe_float(jike.get('acos'))
        fba_qty = _safe_float(jike.get('fbaQuantity'))
        avg_daily = _safe_float(jike.get('averageDailySales'))
        product_name = jike.get('productName', asin)
        # 从 _raw 中取更准确的数据
        raw = jike.get('_raw', {})
        if raw:
            acos = acos if acos is not None else _safe_float(raw.get('acos'))
            fba_qty = fba_qty if fba_qty is not None else _safe_float(raw.get('fbaQuantity'))
            avg_daily = avg_daily if avg_daily is not None else _safe_float(raw.get('averageDailySales'))
            product_name = raw.get('productName', product_name)

        # 清理商品名
        product_name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(product_name))[:50]

        # 条件1：ACOS > 40%
        if acos is not None and acos > ACOS_THRESHOLD:
            alerts.append(
                f"🔥 ACOS预警\n"
                f"ASIN: {asin}\n"
                f"商品名: {product_name}\n"
                f"ACOS: {acos:.1f}%（阈值>{ACOS_THRESHOLD}%）"
            )

        # 条件2：FBA 库存 < 14 天
        if fba_qty is not None and avg_daily is not None and avg_daily > 0:
            inventory_days = fba_qty / avg_daily
            if inventory_days < INVENTORY_DAYS_THRESHOLD:
                alerts.append(
                    f"📦 库存预警\n"
                    f"ASIN: {asin}\n"
                    f"商品名: {product_name}\n"
                    f"库存: {int(fba_qty)}件 / {inventory_days:.1f}天（阈值<{INVENTORY_DAYS_THRESHOLD}天）\n"
                    f"日均销量: {avg_daily:.1f}件"
                )

    if not alerts:
        print('[Alert] 无预警')
        return False

    # 合并消息发送（钉钉每条消息独立）
    for alert in alerts:
        send_dingtalk(alert)

    print(f'[Alert] 共推送 {len(alerts)} 条预警')
    return True


def _safe_float(v):
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


import glob

if __name__ == '__main__':
    check_and_notify()