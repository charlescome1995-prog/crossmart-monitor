#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浜虹被琛屼负妯℃嫙鍣?鎺у埗鑺傚銆侀殢鏈哄寲銆佷吉瑁咃紝闄嶄綆琚簹椹€婇鎺ц瘑鍒殑姒傜巼
"""
import random, time, json
from datetime import datetime, timedelta

# 鈹€鈹€鈹€ 浠婃棩绉嶅瓙锛堝熀浜庢棩鏈燂紝纭繚姣忓ぉ涓嶅浐瀹氫絾涓€澶╁唴涓€鑷达級 鈹€鈹€鈹€
_TODAY_SEED = int(datetime.now().strftime("%Y%m%d"))
_RNG = random.Random(_TODAY_SEED)


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲
# 鏃堕棿绠＄悊
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲

def is_within_window(last_check_str):
    """
    妫€鏌ユ槸鍚﹀凡瓒呰繃鏈€灏忛棿闅旓紙4-7灏忔椂闅忔満锛?    杩斿洖 True = 鍙互妫€鏌? False = 杩樺お鏃?    """
    if not last_check_str:
        return True

    from datetime import datetime
    last = datetime.fromisoformat(last_check_str)
    now = datetime.now()
    diff_hours = (now - last).total_seconds() / 3600

    # 鏈€灏忛棿闅斿湪 3.5 ~ 6.5 灏忔椂涔嬮棿闅忔満锛屾瘡澶╀竴鍙?    min_gap = 3.5 + _RNG.uniform(0, 3)
    return diff_hours >= min_gap


def get_daily_plan(min_checks=2, max_checks=4):
    """
    鐢熸垚浠婂ぉ鐨勬鏌ヨ鍒掞紙闅忔満鏃堕棿鐐癸級
    杩斿洖涓€涓椂闂村垪琛紝濡?["09:15", "14:30", "20:45"]
    """
    # 鍙敤鏃堕棿娈碉細鏃?7-11鐐? 鍗?13-17鐐? 鏅?18-23鐐?    windows = [
        (7, 11),
        (13, 17),
        (18, 23),
    ]

    # 浠婂ぉ鍋氬灏戞锛?-4娆￠殢鏈猴級
    count = _RNG.randint(min_checks, max_checks)
    random.shuffle(windows, _RNG.random)

    plan = []
    for i in range(min(count, len(windows))):
        start_h, end_h = windows[i]
        h = start_h + _RNG.random() * (end_h - start_h)
        plan.append(f"{int(h):02d}:{int((h % 1) * 60):02d}")

    plan.sort()
    return plan


def time_to_next_check(plan):
    """璁＄畻璺濈涓嬫妫€鏌ヨ繕鏈夊涔咃紙绉掞級"""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    for t in plan:
        check_time = datetime.strptime(f"{today} {t}", "%Y-%m-%d %H:%M")
        if check_time > now:
            return (check_time - now).total_seconds()

    # 鎵€鏈夋椂闂村凡杩囷紝鏄庡ぉ
    return None


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲
# 闅忔満鍋滅暀
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲

def human_pause(min_sec=1, max_sec=5):
    """浜虹被鑷劧鍋滈】锛堥潪鍧囧寑鍒嗗竷锛?""
    # 鍋忓悜鐭仠椤匡紙鍍忕湡浜虹殑闃呰鑺傚锛?    bias = random.triangular(min_sec, max_sec, min_sec * 1.2)
    time.sleep(max(0.5, bias))


def read_pause():
    """鍋囪鍦ㄩ槄璇诲唴瀹癸紙3-15绉掞級"""
    time.sleep(random.uniform(1, 5))


def think_pause():
    """鍋囪鍦ㄧ姽璞?鎬濊€冿紙2-8绉掞級"""
    time.sleep(random.uniform(1, 3))


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲
# 琛屼负搴忓垪
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲

# 甯歌浜氶┈閫婃悳绱㈣瘝姹狅紙閫氱敤鍝佺被锛?_COMMON_SEARCHES = [
    "beauty products",
    "gift for women",
    "gift for men",
    "home decor",
    "kitchen gadgets",
    "phone accessories",
    "office supplies",
    "pet supplies",
    "travel accessories",
    "fitness equipment",
    "makeup organizer",
    "storage solutions",
    "bathroom accessories",
    "outdoor gear",
    "winter warmers",
]


def random_amazon_search():
    """闅忔満閫変竴涓湅浼艰嚜鐒剁殑鎼滅储璇?""
    return random.choice(_COMMON_SEARCHES)


def random_category():
    """闅忔満閫変竴涓被鐩悕锛堟ā鎷熼€涚被鐩級"""
    cats = [
        "Beauty & Personal Care",
        "Home & Kitchen",
        "Electronics",
        "Clothing",
        "Sports & Outdoors",
        "Pet Supplies",
        "Health & Household",
        "Office Products",
    ]
    return random.choice(cats)
