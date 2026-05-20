#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
notify.py - CrossMart 监控变化通知推送器
支持: 钉钉机器人 (Webhook)

用法:
  python backend/notify.py                        # 读取最新数据，检查变化并推送
  python backend/notify.py --test                  # 发送测试消息
  python backend/notify.py --set-dingtalk URL      # 配置钉钉Webhook
"""
import sys, os, json, urllib.request, hashlib, base64, hmac, time
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, '..', 'frontend', 'data', 'notify_config.json')
DATA_PATH = os.path.join(BASE, '..', 'frontend', 'data', 'monitor-data.json')
THRESHOLD_PRICE_PCT = 3.0   # 价格波动超过此百分比才推送
THRESHOLD_BSR = 50          # BSR 变动超过此值才推送


def load_config():
    default = {
        "dingtalk_webhook": "",       # 钉钉机器人 Webhook URL
        "dingtalk_secret": "",        # 钉钉加签密钥（如未启用签名留空）
        "enabled": True,
        "push_all": False,            # True=每次都推，False=仅变化时推
    }
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                default.update(loaded)
    except:
        pass
    return default


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 通知配置已保存: {CONFIG_PATH}")


def dingtalk_sign(timestamp, secret):
    """钉钉加签"""
    string_to_sign = f'{timestamp}\n{secret}'
    hmac_code = hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
    return urllib.parse.quote(base64.b64encode(hmac_code))


def send_dingtalk(message, webhook_url, secret=''):
    """通过钉钉机器人发送消息"""
    if not webhook_url:
        print("  ⚠️ 未配置钉钉Webhook，跳过推送")
        return False

    url = webhook_url
    if secret:
        timestamp = str(round(time.time() * 1000))
        sign = dingtalk_sign(timestamp, secret)
        url = f'{webhook_url}&timestamp={timestamp}&sign={sign}'

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "📊 CrossMart 监控通知",
            "text": message
        }
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        if result.get('errcode') == 0:
            print("  ✅ 钉钉推送成功")
            return True
        else:
            print(f"  ⚠️ 钉钉推送失败: {result}")
            return False
    except Exception as e:
        print(f"  ⚠️ 钉钉推送失败: {e}")
        return False


def check_changes():
    """检查最新数据中的变化，返回需要推送的消息列表"""
    if not os.path.exists(DATA_PATH):
        print("  ⚠️ 监控数据文件不存在")
        return []

    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    asins = data.get('asins', [])
    messages = []
    updated = data.get('updated', '')

    for a in asins:
        changes = []
        has_history = a.get('history') and len(a['history']) >= 2

        price_pct = a.get('price_change_pct', 0) or 0
        bsr_chg = a.get('bsr_change', 0) or 0

        if has_history and abs(price_pct) >= THRESHOLD_PRICE_PCT:
            direction = "📈 上涨" if price_pct > 0 else "📉 下跌"
            changes.append(f"{direction} **{abs(price_pct):.1f}%** (${a.get('price', '?'):.2f})")

        if has_history and abs(bsr_chg) >= THRESHOLD_BSR:
            direction = "🟢 改善" if bsr_chg < 0 else "🔴 恶化"
            changes.append(f"BSR {direction}: **{abs(bsr_chg)}** 位 (当前 #{a.get('bsr', '?'):,})")

        if not changes:
            continue

        # 构建单条消息
        title = a.get('title', '') or ''
        brand = a.get('brand', '') or ''
        msg = (
            f"### 🔔 ASIN 变化提醒\n\n"
            f"**{brand}** — [{title[:60]}](https://www.amazon.com/dp/{a['asin']})\n"
            f"**ASIN**: `{a['asin']}`\n"
            f"**变化**:\n"
        )
        for c in changes:
            msg += f"- {c}\n"
        msg += f"\n---\n"
        msg += f"🕐 数据截至: {updated[:16]}"

        messages.append(msg)

    return messages


def build_summary_message(cfg):
    """构建全量摘要消息（无变化时用）"""
    if not os.path.exists(DATA_PATH):
        return None
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    asins = data.get('asins', [])
    updated = data.get('updated', '')

    total = len(asins)
    price_changed = sum(1 for a in asins if abs((a.get('price_change_pct') or 0)) >= THRESHOLD_PRICE_PCT)
    bsr_changed = sum(1 for a in asins if abs((a.get('bsr_change') or 0)) >= THRESHOLD_BSR)
    top_asins = sorted(asins, key=lambda x: abs((x.get('price_change_pct') or 0)), reverse=True)[:5]

    msg = (
        f"### 📊 CrossMart 监控摘要\n\n"
        f"**检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"**监控ASIN**: {total} 个\n"
        f"**价格波动**: {price_changed} 个\n"
        f"**BSR变化**: {bsr_changed} 个\n\n"
    )

    if top_asins:
        msg += "**变化幅度前5**:\n"
        for a in top_asins:
            pct = a.get('price_change_pct', 0) or 0
            bsr = a.get('bsr_change', 0) or 0
            if abs(pct) > 0.01 or abs(bsr) > 0:
                msg += f"- {a['asin']} | 价格 {'+' if pct >= 0 else ''}{pct:.1f}% | BSR {'+' if bsr >= 0 else ''}{bsr}\n"

    msg += f"\n🕐 数据截至: {updated[:16]}"
    msg += f"\n🔗 [查看面板](https://charlescome1995-prog.github.io/crossmart-monitor/monitor.html)"
    return msg


def main():
    cfg = load_config()
    if not cfg.get('enabled', True):
        print("  ⏸️ 通知已禁用")
        return

    webhook = cfg.get('dingtalk_webhook', '')
    if not webhook:
        print("  ⚠️ 未配置钉钉Webhook，请运行 --set-dingtalk")
        return

    messages = check_changes()

    if messages:
        print(f"  📢 发现 {len(messages)} 条变化通知，开始推送...")
        for msg in messages:
            send_dingtalk(msg, webhook, cfg.get('dingtalk_secret', ''))
            time.sleep(0.5)
    elif cfg.get('push_all', False):
        print("  📢 无显著变化，推送摘要...")
        summary = build_summary_message(cfg)
        if summary:
            send_dingtalk(summary, webhook, cfg.get('dingtalk_secret', ''))
    else:
        print("  ✅ 无显著变化，跳过推送")


if __name__ == '__main__':
    import urllib.parse

    if '--set-dingtalk' in sys.argv:
        idx = sys.argv.index('--set-dingtalk')
        if idx + 1 >= len(sys.argv):
            print("用法: python backend/notify.py --set-dingtalk <WEBHOOK_URL> [--secret <SECRET>]")
            sys.exit(1)
        webhook = sys.argv[idx + 1]
        secret = ''
        if '--secret' in sys.argv:
            secret = sys.argv[sys.argv.index('--secret') + 1]
        cfg = load_config()
        cfg['dingtalk_webhook'] = webhook
        cfg['dingtalk_secret'] = secret
        save_config(cfg)
        print("请发送一条测试消息验证配置...")
        send_dingtalk("### 🔔 CrossMart 监控通知\n\n**✅ 钉钉推送已就绪**\n\n⏰ " + datetime.now().strftime('%Y-%m-%d %H:%M') + "\n\n发送者: CrossMart 监控系统", webhook, secret)

    elif '--test' in sys.argv:
        cfg = load_config()
        msg = (
            "### 🔔 CrossMart 通知测试\n\n"
            "**✅ 系统运行正常**\n\n"
            "⏰ " + datetime.now().strftime('%Y-%m-%d %H:%M') + "\n\n"
            "监控ASIN: 15个 | 今日变化: ——"
        )
        send_dingtalk(msg, cfg.get('dingtalk_webhook', ''), cfg.get('dingtalk_secret', ''))

    else:
        main()
