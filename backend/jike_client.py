"""
积加 ERP API 客户端
API 文档: https://open.gerpgo.com/api/open
"""

import json
import time
import requests
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "data" / "jike_config.json"
TOKEN_CACHE_PATH = Path(__file__).parent / "data" / "jike_token_cache.json"

BASE_URL = "https://open.gerpgo.com/api/open"


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
        # 提前5分钟过期，留 buffer
        if time.time() < data.get("expires_at", 0) - 300:
            return data.get("token")
    except Exception:
        pass
    return None


def get_access_token(app_id: str, app_key: str) -> str:
    """
    获取 access_token，先查缓存，无效则重新请求
    """
    # 先试缓存
    cached = load_token_cache()
    if cached:
        return cached

    # 请求新 token
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

    # 积加返回格式: { code: 0, data: { access_token: "...", expires_in: 3600 } }
    if result.get("code") != 0:
        raise Exception(f"获取 access_token 失败: {result}")

    data = result.get("data", {})
    token = data.get("access_token")
    expires_in = data.get("expires_in", 3600)

    # 缓存
    save_token_cache(token, time.time() + expires_in)
    return token


def get_listing_analyze(asin_list: list, app_id: str, app_key: str,
                        market_list: list = None,
                        begin_date: str = None,
                        end_date: str = None):
    """
    调用商品表现接口（ASIN维度）

    Args:
        asin_list: ASIN 列表（建议一次≤20个）
        app_id: APP ID
        app_key: APP KEY
        market_list: 站点列表，默认 [1]
        begin_date: 开始日期 "YYYY-MM-DD"，默认 7 天前
        end_date: 结束日期 "YYYY-MM-DD"，默认今天

    Returns:
        dict: { code, data: { rows: [...] } }
    """
    import datetime

    today = datetime.date.today()
    if not end_date:
        end_date = today.strftime("%Y-%m-%d")
    if not begin_date:
        begin_date = (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")

    if market_list is None:
        market_list = [1]

    token = get_access_token(app_id, app_key)

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
    return resp.json()


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

    result = get_listing_analyze(asin_list, app_id, app_key)
    code = result.get("code")
    if code != 0:
        raise Exception(f"积加 API 返回错误: code={code}, 请检查凭证是否有效")

    rows = result.get("data", {}).get("rows", [])

    # 转换为 { asin: {...fields} } 字典
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
            # 原始完整数据也保留，方便调试
            "_raw": row
        }

    return out


if __name__ == "__main__":
    # 简单测试
    config = load_config()
    if not config:
        print("未配置 jike_config.json，请先配置 APP_ID 和 APP_KEY")
    else:
        print("已配置 appId:", config.get("appId"))
        # 测试 token 获取
        try:
            token = get_access_token(config["appId"], config["appKey"])
            print("access_token 获取成功:", token[:20] + "...")
        except Exception as e:
            print("access_token 获取失败:", e)