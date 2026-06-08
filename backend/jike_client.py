"""
积加 ERP API 客户端
API 文档: https://open.gerpgo.com/api/open
"""

import json
import time
import socket
import subprocess
import requests
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "data" / "jike_config.json"
TOKEN_CACHE_PATH = Path(__file__).parent / "data" / "jike_token_cache.json"

BASE_URL = "https://open.gerpgo.com/api/open"


# ─────────────────────────── VPN 切换 ───────────────────────────

def _wait_internet(timeout=20):
    """等待本地网络（VPN断开后）恢复正常"""
    for _ in range(timeout):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect(("8.8.8.8", 53))
            sock.close()
            return True
        except Exception:
            time.sleep(1)
    return False


def _kill_rabbitpro():
    """强制终止 RabbitPro"""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "RabbitPro.exe"],
            capture_output=True
        )
        time.sleep(3)
    except Exception as e:
        print(f"[VPN] taskkill 失败: {e}")


def _start_rabbitpro():
    """启动 RabbitPro（后台最小化）"""
    try:
        subprocess.Popen(
            [r"C:\Users\OPENPC\AppData\Local\Programs\RabbitPro\RabbitPro.exe",
             "--minimize"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)
    except Exception as e:
        print(f"[VPN] 启动 RabbitPro 失败: {e}")


class VPNSwitcher:
    """
    积加 API 调用期间自动切换到本地网络（关闭 VPN）。

    积加服务器要求请求来自白名单 IP 121.35.1.52，
    全局 VPN 会导致出口 IP 变化，需要在调用积加期间断开 VPN。

    用法：
        with VPNSwitcher():
            data = get_jike_data_for_asins(["B0FVSS8SR1"])
    """

    def __enter__(self):
        print("[VPN] 断开 VPN（积加需要白名单IP）...")
        _kill_rabbitpro()
        if not _wait_internet():
            raise Exception("[VPN] 断开后网络未恢复，请检查本地网络")
        print("[VPN] 已切换到本地网络")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("[VPN] 重启 VPN 服务...")
        _start_rabbitpro()
        print("[VPN] 请在 RabbitPro 界面手动点击连接")


# ─────────────────────────── 凭证 & Token ───────────────────────────

def load_config():
    """加载积加凭证配置"""
    if not CONFIG_PATH.exists():
        return None
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_token_cache(token, expires_at):
    """缓存 access_token"""
    TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump({"token": token, "expires_at": expires_at}, f)


def load_token_cache():
    """读取缓存的 access_token"""
    if not TOKEN_CACHE_PATH.exists():
        return None
    try:
        with open(TOKEN_CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if time.time() < data.get("expires_at", 0) - 300:
            return data.get("token")
    except Exception:
        pass
    return None


def invalidate_token_cache():
    """主动清除 token 缓存（401 时调用，强制重新获取）"""
    try:
        TOKEN_CACHE_PATH.unlink(missing_ok=True)
    except Exception:
        pass


def get_access_token(app_id: str, app_key: str) -> str:
    """获取 access_token，先查缓存，无效则重新请求"""
    cached = load_token_cache()
    if cached:
        return cached

    url = f"{BASE_URL}/oauth/token"
    payload = {
        "appId": app_id,
        "appKey": app_key,
        "grant_type": "client_credentials"
    }
    headers = {"Content-Type": "application/json"}

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    print(f"  [积加] token响应: code={result.get('code')}, data={str(result.get('data'))[:100]}")

    if result.get("code") != 0:
        raise Exception(f"获取 access_token 失败: {result}")

    data = result.get("data", {})
    token = data.get("access_token")
    expires_in = data.get("expires_in", 3600)

    save_token_cache(token, time.time() + expires_in)
    return token


# ─────────────────────────── 商品表现 API ───────────────────────────

def get_listing_analyze(asin_list: list, app_id: str, app_key: str,
                        market_list: list = None,
                        begin_date: str = None,
                        end_date: str = None):
    """调用商品表现接口（ASIN维度）"""
    import datetime

    today = datetime.date.today()
    if not end_date:
        end_date = today.strftime("%Y-%m-%d")
    if not begin_date:
        begin_date = (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")

    if market_list is None:
        market_list = [1]

    token = get_access_token(app_id, app_key)
    time.sleep(1.5)

    url = f"{BASE_URL}/operation/sts/listingAnalyzeMultiIndex/page"
    headers = {
        "Content-Type": "application/json",
        "accessToken": token
    }
    payload = {
        "groupByType": "asin",
        "showCurrencyType": "USD",
        "beginDate": begin_date,
        "endDate": end_date,
        "isShowTotal": False,
        "page": 1,
        "pagesize": 20,
        "marketList": market_list,
        "asinList": asin_list
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    result_json = resp.json()
    print(f"  [积加] 数据响应: code={result_json.get('code')}, rows={len(result_json.get('data',{}).get('rows',[]))}")
    return result_json


# ─────────────────────────── 主入口 ───────────────────────────

def get_jike_data_for_asins(asin_list: list, config_path: str = None):
    """
    对外主入口：给定 ASIN 列表，返回积加数据字典
    格式: { asin: { salesAmount, orders, session, pageViews, conversionRate, listingState } }

    Args:
        asin_list: ASIN 列表
        config_path: 配置文件路径，默认使用 jike_config.json

    Returns:
        dict: 每个 ASIN 的积加数据，ASIN 不在返回数据中则该 ASIN 值为 None
    """
    config = load_config()
    if not config:
        raise Exception("积加配置未找到，请先配置 APP_ID 和 APP_KEY")

    app_id = config.get("appId")
    app_key = config.get("appKey")
    if not app_id or not app_key:
        raise Exception("积加配置缺少 appId 或 appKey")

    # ── 积加 API 需要白名单 IP，调用期间关闭 VPN ──
    with VPNSwitcher():
        time.sleep(2)  # 批次间隔
        result = get_listing_analyze(asin_list, app_id, app_key)

        code = result.get("code")
        if code != 0:
            # 401 时清除缓存，下次重试可重新获取 token
            if code == 401 or code == 40005:
                invalidate_token_cache()
            rows = result.get("data", {}).get("rows", [])
            raise Exception(
                f"积加 API 返回错误: code={code}, "
                f"message={result.get('message','')}, rows={len(rows)}, "
                f"请检查凭证/权限/ASIN是否在积加系统注册"
            )

        rows = result.get("data", {}).get("rows", [])

        out = {}
        for row in rows:
            asin = row.get("asin", "")
            if not asin:
                continue
            sales_obj = row.get("salesAmount", {}) or {}
            out[asin] = {
                "salesAmount": sales_obj.get("currencyAmount") if isinstance(sales_obj, dict) else None,
                "orders": row.get("orders"),
                "session": row.get("session"),
                "pageViews": row.get("pageViews"),
                "conversionRate": row.get("conversionRate"),
                "listingState": row.get("listingState"),
                "_raw": row
            }

        return out


if __name__ == "__main__":
    config = load_config()
    if not config:
        print("未配置 jike_config.json，请先配置 APP_ID 和 APP_KEY")
    else:
        print("已配置 appId:", config.get("appId"))
        try:
            with VPNSwitcher():
                token = get_access_token(config["appId"], config["appKey"])
                print("access_token 获取成功:", token[:20] + "...")
        except Exception as e:
            print("access_token 获取失败:", e)