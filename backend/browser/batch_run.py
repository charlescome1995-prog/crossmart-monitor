"""补充扫描 - 完整监控流程（含人类行为模拟）"""
import sys, os, time, json
sys.stdout.reconfigure(encoding="utf-8")
PROJECT = r"C:\Users\OPENPC\.openclaw\workspace\projects\amazon_ai_kit"
sys.path.insert(0, os.path.join(PROJECT, "browser"))

from asin_monitor import check_asin

with open(os.path.join(PROJECT, "data", "monitor_list.json"), "r", encoding="utf-8") as f:
    config = json.load(f)

# 补充B0GJ7536MY（只有2条）和B0DPBHVMS4（BSR缺失）
targets = ["B0GJ7536MY", "B0DPBHVMS4"]
for asin in targets:
    print(f"\n补充扫描: {asin}")
    check_asin(asin, search_keyword="batana oil", use_sprite=False)
    time.sleep(2)

print("\n✅ 补充完成")
