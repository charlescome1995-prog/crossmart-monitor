#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASIN监控 - 独立入口
连接已有的CDP Edge实例（端口9225）
"""
import sys, os, time, urllib.request, json

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), 'w', encoding='utf-8', buffering=1)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Edge已经手动启动在9225端口（默认profile，有收藏夹）
os.environ["CDP_PORT"] = "9225"

# 先确认连接
try:
    r = urllib.request.urlopen("http://127.0.0.1:9225/json", timeout=5)
    tabs = json.loads(r.read())
    print("Edge已连接 (9225, %d个标签页)" % len(tabs))
except Exception as e:
    print("Edge未运行: %s" % e)
    print("请先启动Edge: msedge --remote-debugging-port=9225 --remote-allow-origins=*")
    sys.exit(1)

from browser.asin_monitor import check_asin

asins = sys.argv[1:] if len(sys.argv) > 1 else ["B09V7Z4TJG"]

for asin in asins:
    check_asin(asin)
