#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scheduler.py - 监控调度器
读取 monitor_list.json 和 keyword_list.json，逐个执行 ASIN + 关键词 监控
"""
import sys, os, json, time
sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data")
os.makedirs(DATA_DIR, exist_ok=True)

MONITOR_LIST_PATH = os.path.join(DATA_DIR, "monitor_list.json")
KEYWORD_LIST_PATH = os.path.join(DATA_DIR, "keyword_list.json")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# ─── 日志 ───
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

# ─── 加载配置 ───
def load_monitor_list():
    if not os.path.exists(MONITOR_LIST_PATH):
        log(f"⚠️ {MONITOR_LIST_PATH} 不存在，跳过 ASIN 监控")
        return []
    with open(MONITOR_LIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_keyword_list():
    if not os.path.exists(KEYWORD_LIST_PATH):
        log(f"⚠️ {KEYWORD_LIST_PATH} 不存在，跳过关键词监控")
        return []
    with open(KEYWORD_LIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ─── 运行单个 ASIN ───
def run_asin(asin_data):
    asin = asin_data.get("asin", "")
    if not asin:
        return
    log(f"📦 检查ASIN: {asin}")
    try:
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))
        from browser.asin_monitor import check_asin
        result = check_asin(asin)
        log(f"✅ ASIN {asin} 完成")
    except Exception as e:
        log(f"❌ ASIN {asin} 失败: {e}")

# ─── 运行关键词 ───
def run_keyword(kw_data):
    kw = kw_data.get("keyword", "") or kw_data.get("kw", "")
    if not kw:
        return
    log(f"🔍 检查关键词: {kw}")
    try:
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))
        from browser.keyword_monitor import check_keyword
        result = check_keyword(kw)
        log(f"✅ 关键词 {kw} 完成")
    except Exception as e:
        log(f"❌ 关键词 {kw} 失败: {e}")

# ─── 主流程 ───
def main():
    mode = "force"
    if "--asin-only" in sys.argv:
        mode = "asin"
    elif "--keyword-only" in sys.argv:
        mode = "keyword"

    log("=" * 60)
    log("🔄 调度器启动")
    log(f"   时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"   模式: {mode}")
    log("=" * 60)

    if mode in ("force", "asin"):
        asins = load_monitor_list()
        log(f"\n📦 Phase A: ASIN监控检查 ({len(asins)}个)")
        for i, a in enumerate(asins, 1):
            log(f"\n  [{i}/{len(asins)}]")
            run_asin(a)
            if i < len(asins):
                wait = 15 + int(time.time() % 20)
                log(f"  ⏳ 等待{wait}s后继续...")
                time.sleep(wait)

    if mode in ("force", "keyword"):
        kws = load_keyword_list()
        log(f"\n🔍 Phase B: 关键词监控检查 ({len(kws)}个)")
        for i, k in enumerate(kws, 1):
            log(f"\n  [{i}/{len(kws)}]")
            run_keyword(k)
            if i < len(kws):
                wait = 10 + int(time.time() % 15)
                log(f"  ⏳ 等待{wait}s后继续...")
                time.sleep(wait)

    log("\n✅ 调度器完成")

if __name__ == "__main__":
    main()