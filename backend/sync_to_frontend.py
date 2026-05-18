#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_to_frontend.py - 将浏览器抓取的快照数据同步到前端monitor-data.json
同时计算逐次变化，生成前端需要的完整数据格式
"""
import sys, os, json, re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT, "backend", "data", "processed")
FRONTEND_DATA = os.path.join(PROJECT, "frontend", "data", "monitor-data.json")

def load_all_snapshots():
    """扫描data/processed下的所有ASIN快照"""
    asins = {}
    if not os.path.exists(DATA_DIR):
        print("  数据目录不存在: %s" % DATA_DIR)
        return asins
    
    for entry in os.listdir(DATA_DIR):
        if not entry.startswith("asin_"):
            continue
        asin = entry.replace("asin_", "", 1)
        snap_dir = os.path.join(DATA_DIR, entry)
        
        snaps = []
        for f in sorted(os.listdir(snap_dir)):
            if f.startswith("snapshot_") and f.endswith(".json"):
                path = os.path.join(snap_dir, f)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        snap = json.load(fh)
                    snaps.append(snap)
                except Exception as e:
                    print("  跳过 %s: %s" % (f, e))
        
        if snaps:
            asins[asin] = snaps
    
    return asins

def parse_price(text):
    """从文本中提取价格数字"""
    if not text:
        return None
    m = re.search(r'[\d.]+', text.replace(",", ""))
    return float(m.group()) if m else None

def parse_rating(text):
    """提取评分"""
    if not text:
        return None
    m = re.search(r'([\d.]+)', text)
    return float(m.group()) if m else None

def parse_review_count(text):
    """提取评论数"""
    if not text:
        return None
    m = re.search(r'([\d,]+)', str(text))
    return int(m.group(1).replace(",","")) if m else None

def parse_bsr_number(text):
    """提取BSR数字"""
    if not text:
        return None
    m = re.search(r'#([\d,]+)', text)
    return int(m.group(1).replace(",","")) if m else int(re.search(r'([\d,]+)', text).group(1).replace(",","")) if re.search(r'([\d,]+)', text) else None

def compute_snapshot_changes(snapshots):
    """计算相邻snapshot之间的变化"""
    changes = []
    for i in range(1, len(snapshots)):
        prev = snapshots[i-1]["data"]
        curr = snapshots[i]["data"]
        ts = snapshots[i]["timestamp"]
        
        change_items = []
        
        # 价格变化
        old_p = parse_price(prev.get("price",""))
        new_p = parse_price(curr.get("price",""))
        if old_p and new_p and old_p != new_p:
            diff = new_p - old_p
            pct = (diff / old_p) * 100
            direction = "up" if diff > 0 else "down"
            change_items.append({
                "field": "price",
                "from": prev.get("price",""),
                "to": curr.get("price",""),
                "direction": direction,
                "diff": "$%.2f" % abs(diff),
                "pct": "%.1f%%" % abs(pct)
            })
        
        # 评分变化
        old_r = parse_rating(prev.get("rating",""))
        new_r = parse_rating(curr.get("rating",""))
        if old_r and new_r and abs(old_r - new_r) > 0.05:
            direction = "up" if new_r > old_r else "down"
            change_items.append({
                "field": "rating",
                "from": str(old_r),
                "to": str(new_r),
                "direction": direction,
                "diff": "%.1f" % abs(new_r - old_r)
            })
        
        # 评论数变化
        old_c = parse_review_count(prev.get("review_count",""))
        new_c = parse_review_count(curr.get("review_count",""))
        if old_c and new_c and old_c != new_c:
            direction = "up" if new_c > old_c else "down"
            change_items.append({
                "field": "review_count",
                "from": str(old_c),
                "to": str(new_c),
                "direction": direction,
                "diff": abs(new_c - old_c)
            })
        
        # BSR变化
        old_b = parse_bsr_number(prev.get("bsr",""))
        new_b = parse_bsr_number(curr.get("bsr",""))
        if old_b and new_b and old_b != new_b:
            # BSR数字越小越好
            direction = "up" if new_b < old_b else "down"
            change_items.append({
                "field": "bsr",
                "from": "#%s" % format(old_b, ","),
                "to": "#%s" % format(new_b, ","),
                "direction": direction,
                "diff": abs(new_b - old_b)
            })
        
        if change_items:
            changes.append({
                "timestamp": ts,
                "items": change_items
            })
    
    return changes

def build_frontend_data(asins_data):
    """构建前端需要的monitor-data.json格式"""
    items = []
    
    for asin, snapshots in sorted(asins_data.items()):
        snaps_sorted = sorted(snapshots, key=lambda s: s.get("timestamp", ""))
        
        if not snaps_sorted:
            continue
        
        latest = snaps_sorted[-1]
        data = latest.get("data", {})
        
        # 提取字段
        title = data.get("title", "")[:100]
        brand = data.get("brand", "").replace("Visit the ", "").replace(" Store", "")
        price = data.get("price", "")
        list_price = data.get("list_price", "")
        
        # 评分
        rating_raw = data.get("rating", "")
        rating_m = re.search(r'([\d.]+)', rating_raw)
        rating = rating_m.group(1) if rating_m else rating_raw[:5]
        
        # 评论数 - 去除括号逗号
        review_raw = data.get("review_count", "")
        review_raw_clean = str(review_raw).replace("(", "").replace(")", "").replace(",", "")
        review_m = re.search(r'(\d+)', review_raw_clean)
        review_count = review_m.group(1) if review_m else "0"
        
        # BSR - 提取更完整的描述
        bsr_raw = data.get("bsr", "")
        # 提取完整格式: #N in Category
        bsr_m = re.search(r'(#[\d,]+)\s+in\s+([^\n\r#]+?)(?=\s*(?:#|$))', bsr_raw)
        if bsr_m:
            bsr = "%s in %s" % (bsr_m.group(1), bsr_m.group(2).strip()[:40])
        else:
            bsr_m2 = re.search(r'#[\d,]+', bsr_raw)
            bsr = bsr_m2.group(0) if bsr_m2 else ""
            if bsr:
                # 尝试从行内取剩余的文案
                rest = bsr_raw.replace(bsr_m2.group(0), "").strip()[:40]
                if rest and "Best" not in rest:
                    bsr += " " + rest
        
        # 小类BSR
        bsr_sub_rank = data.get("bsr_sub_rank", "")
        bsr_sub_category = data.get("bsr_sub_category", "")[:50]
        
        # 卖家
        seller = data.get("sold_by", "")
        
        # 主图
        main_image = data.get("main_image", "")
        
        # 变化计算
        snapshot_changes = compute_snapshot_changes(snaps_sorted)
        
        # 所有snapshot的时间轴
        snap_times = [s.get("timestamp", "")[:16] for s in snaps_sorted]
        
        # 构建基础change描述
        change_desc = ""
        if snapshot_changes:
            parts = []
            for sc in snapshot_changes:
                for item in sc["items"]:
                    if item["field"] == "price":
                        parts.append("价格 %s %s (%s)" % (
                            "↑" if item["direction"] == "up" else "↓",
                            item["diff"],
                            item["pct"]
                        ))
                    elif item["field"] == "bsr":
                        parts.append("BSR %s #%s→#%s" % (
                            "↑" if item["direction"] == "up" else "↓",
                            item["from"].replace("#",""),
                            item["to"].replace("#","")
                        ))
                    elif item["field"] == "rating":
                        parts.append("评分 %s %s" % (
                            "↑" if item["direction"] == "up" else "↓",
                            item["diff"]
                        ))
                    elif item["field"] == "review_count":
                        parts.append("评论 %s %s条" % (
                            "↑" if item["direction"] == "up" else "↓",
                            item["diff"]
                        ))
            change_desc = " | ".join(parts)
        
        item = {
            "asin": asin,
            "title": title,
            "brand": brand,
            "price": price,
            "list_price": list_price,
            "rating": rating,
            "review_count": review_count,
            "bsr": bsr,
            "bsr_sub_rank": "#" + bsr_sub_rank if bsr_sub_rank else "",
            "bsr_sub_category": bsr_sub_category,
            "seller": seller,
            "main_image": main_image,
            "last_check": latest.get("timestamp", ""),
            "snapshots": snap_times,
            "snapshot_count": len(snaps_sorted),
            "has_changes": len(snapshot_changes) > 0,
            "change_count": len(snapshot_changes),
            "change_desc": change_desc,
            "changes": snapshot_changes
        }
        items.append(item)
    
    return {"asins": items, "updated": datetime.now().isoformat()}

def main():
    print("同步抓取数据到前端...")
    print("  数据目录: %s" % DATA_DIR)
    print("  目标文件: %s" % FRONTEND_DATA)
    
    asins = load_all_snapshots()
    print("  发现 %d 个ASIN" % len(asins))
    for asin, snaps in asins.items():
        print("    %s: %d个快照" % (asin, len(snaps)))
    
    if not asins:
        print("  ⚠️ 没有数据，生成空模板")
        frontend = {"asins": [], "updated": datetime.now().isoformat()}
    else:
        frontend = build_frontend_data(asins)
    
    os.makedirs(os.path.dirname(FRONTEND_DATA), exist_ok=True)
    with open(FRONTEND_DATA, "w", encoding="utf-8") as f:
        json.dump(frontend, f, ensure_ascii=False, indent=2)
    
    print("  ✅ 已更新 %d 个ASIN到前端" % len(frontend["asins"]))
    for item in frontend["asins"][:5]:
        changes = "有变化" if item["has_changes"] else "无变化"
        print("    %s | %s | %s | %s" % (item["asin"], item["price"], item["title"][:30], changes))

if __name__ == "__main__":
    main()
