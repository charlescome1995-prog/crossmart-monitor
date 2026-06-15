"""最终：直接写监控配置 + 输出全量ASIN供参考"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")

PROJECT = r"C:\Users\OPENPC\.openclaw\workspace\projects\amazon_ai_kit"
MONITOR_LIST = os.path.join(PROJECT, "data", "monitor_list.json")

# 从查竞品已知结果：
# 我的产品 (Lebanta Batana Oil) 父体: B0FSMQZ3S5
# 同类第一名 (Handcraft Blends Rosemary + Batana) 销量488: B0GJ7536MY
# 同类中游 (#19位置): B0DFMDFL8J
# 类目随机: B0DPBHVMS4 (Yacemira)
# 新品第一名 (Batana Oil套装) 父体: B0F3BB1B6Z
# 新品中游: B0FRSGJVM6 (MAREE)

config = [
    {"asin": "B0DCX7628T", "keywords": "batana oil", "nickname": "我的产品(Lebanta)", "group": "own"},
    {"asin": "B0GJ7536MY", "keywords": "batana oil", "nickname": "同类第一名(Handcraft)", "group": "top_same"},
    {"asin": "B0DFMDFL8J", "keywords": "batana oil", "nickname": "同类中游(MISICH)", "group": "mid_same"},
    {"asin": "B0DPBHVMS4", "keywords": "batana oil", "nickname": "类目随机(Yacemira)", "group": "random"},
    {"asin": "B0F3BB1B6Z", "keywords": "batana oil", "nickname": "新品第一名(Artnaturals)", "group": "new_top"},
    {"asin": "B0FRSGJVM6", "keywords": "batana oil", "nickname": "新品中游(MAREE)", "group": "new_mid"},
]

os.makedirs(os.path.dirname(MONITOR_LIST), exist_ok=True)
with open(MONITOR_LIST, "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print("监控配置已写入:")
for c in config:
    print(f"  {c['nickname'][:25]:25} → {c['asin']}")
