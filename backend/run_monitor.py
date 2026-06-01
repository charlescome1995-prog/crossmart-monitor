#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_monitor.py - 跨境电商 ASIN 监控系统入口
支持随机化、时间窗口、概率运行、人类行为模拟。
"""
import os, sys, json, time, random, subprocess, urllib.request
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data")
TRIGGER_FILE = os.path.join(DATA_DIR, "trigger.json")
CONFIG_FILE = os.path.join(DATA_DIR, "user_config.json")
REPO = "charlescome1995-prog/crossmart-monitor"

DEFAULT_SCHEDULE = {
    "morning":   {"anchor": "06:20", "window_start": "06:20", "window_end": "07:20", "jitter_max_minutes": 30, "run_probability": 1.0},
    "midday":     {"anchor": "06:30", "window_start": "06:30", "window_end": "07:30", "jitter_max_minutes": 30, "run_probability": 1.0},
    "evening":    {"anchor": "06:40", "window_start": "06:40", "window_end": "07:40", "jitter_max_minutes": 30, "run_probability": 1.0},
}

# ── 文件路径常量 ──
MAIN_ASINS_FILE    = os.path.join(DATA_DIR, "main_asins.json")
ASIN_RELATED_FILE = os.path.join(DATA_DIR, "asin_related_asins.json")
KEYWORD_LIST_FILE  = os.path.join(DATA_DIR, "keyword_list.json")
KW_RELATED_FILE   = os.path.join(DATA_DIR, "keyword_related_asins.json")  # 旧文件，逐步废弃


def gh_fetch_json(path):
    api_url = "https://api.github.com/repos/" + REPO + "/contents/" + path
    req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            import base64
            data = json.loads(r.read())
            content = base64.b64decode(data["content"]).decode("utf-8")
            return json.loads(content)
    except Exception as e:
        print("  fetch " + path + " error: " + str(e))
        return None


def load_trigger():
    return gh_fetch_json("backend/data/trigger.json")


def load_config():
    data = gh_fetch_json("backend/data/user_config.json")
    if data is None:
        return {"asins": [], "keywords": [], "schedule": DEFAULT_SCHEDULE}
    return data


def load_main_asins():
    """加载主 ASIN 列表（新增结构）"""
    if os.path.exists(MAIN_ASINS_FILE):
        try:
            with open(MAIN_ASINS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("  load main_asins.json error: " + str(e))
    return []


def load_asin_related():
    """加载 ASIN → 关联 ASIN 映射（新增结构）"""
    if os.path.exists(ASIN_RELATED_FILE):
        try:
            with open(ASIN_RELATED_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("  load asin_related_asins.json error: " + str(e))
    return {}


def save_asin_related(data):
    """保存 ASIN → 关联 ASIN 映射"""
    with open(ASIN_RELATED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_keyword_list():
    """加载关键词列表"""
    if os.path.exists(KEYWORD_LIST_FILE):
        try:
            with open(KEYWORD_LIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []


def _safe_print(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('gbk', errors='replace').decode('gbk'))


def now_in_window(window_start, window_end):
    now = datetime.now()
    current_min = now.hour * 60 + now.minute
    start_min = int(window_start.split(":")[0]) * 60 + int(window_start.split(":")[1])
    end_min   = int(window_end.split(":")[0])   * 60 + int(window_end.split(":")[1])
    return start_min <= current_min <= end_min


def wait_random(max_minutes, label=""):
    wait = random.randint(0, max_minutes)
    if wait > 0:
        print(f"  [{label}] 随机等待 {wait} 分钟...")
        time.sleep(wait * 60)


def should_run(slot_config):
    prob = slot_config.get("run_probability", 1.0)
    roll = random.random()
    execute = roll < prob
    print(f"  抽奖结果: {roll:.3f} {'>= ' if not execute else '< '}{prob:.1f} → {'执行' if execute else '跳过'}")
    return execute


def run_command(cmd_list, cwd=None, timeout=600):
    print("  Running: " + ' '.join(cmd_list))
    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['CDP_PORT'] = '9225'
        python_dir = os.path.dirname(sys.executable)
        env['PATH'] = python_dir + os.pathsep + env.get('PATH', '')
        if 'SYSTEMROOT' not in env:
            env['SYSTEMROOT'] = os.environ.get('SYSTEMROOT', r'C:\WINDOWS')
        result = subprocess.run(
            cmd_list, shell=False, cwd=cwd or PROJECT_ROOT,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout, env=env
        )
        if result.stdout:
            _safe_print(result.stdout[-2000:])
        if result.returncode != 0 and result.stderr:
            _safe_print("  STDERR: " + result.stderr[-500:])
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("  TIMEOUT after " + str(timeout) + "s")
        return False
    except Exception as e:
        print("  Exception: " + str(e))
        return False


def sync_and_push():
    sync_script = os.path.join(PROJECT_ROOT, "backend", "sync_monitor_data.py")
    if not os.path.exists(sync_script):
        print("  sync_monitor_data.py not found, skip sync")
        return True
    ok = run_command([sys.executable, sync_script], timeout=120)
    if not ok:
        print("  sync failed")
        return False
    repo_dir = PROJECT_ROOT
    subprocess.run("git config --global user.name \"CrossMart Bot\"",  shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run("git config --global user.email \"bot@crossmart.ai\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    result = subprocess.run("git status --porcelain", shell=True, cwd=repo_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.stdout.strip():
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        run_command(["git", "add",
            "frontend/data/rawData.json",
            "backend/data/asin_related_asins.json",
            "backend/data/main_asins.json"],
            cwd=repo_dir, timeout=15)
        run_command(["git", "commit", "-m", "auto: sync " + ts], cwd=repo_dir, timeout=30)
        push_ok = run_command(["git", "push"], cwd=repo_dir, timeout=60)
        if not push_ok:
            print("  push rejected, force-push...")
            run_command(["git", "push", "-f"], cwd=repo_dir, timeout=60)
        print("  数据已推送")
    else:
        print("  无数据变化")
    return True


def push_trigger_done(trigger):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TRIGGER_FILE, "w", encoding="utf-8") as f:
        json.dump(trigger, f, ensure_ascii=False, indent=2)
    repo_dir = PROJECT_ROOT
    subprocess.run("git config --global user.name \"CrossMart Bot\"",  shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run("git config --global user.email \"bot@crossmart.ai\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run("git add " + TRIGGER_FILE, shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run("git commit -m \"auto: trigger done\"", shell=True, cwd=repo_dir, encoding="utf-8", errors="replace")
    pr = subprocess.run("git push", shell=True, cwd=repo_dir, timeout=60, encoding="utf-8", errors="replace")
    if pr.returncode != 0:
        print("  force-pushing trigger...")
        subprocess.run("git push -f", shell=True, cwd=repo_dir, timeout=60, encoding="utf-8", errors="replace")
    print("  trigger.json 已推送")


def browse_unrelated_pages():
    print("  [Phase 0] 人类行为模拟：先逛几个无关页面...")
    urls = ["https://www.amazon.com", "https://www.amazon.com/gp/bestsellers/"]
    random.shuffle(urls)
    for url in urls[:2]:
        print(f"  浏览: {url}")
        time.sleep(random.randint(3, 8))


def discover_related_asins_via_sprite(main_asin):
    """通过卖家精灵竞品查询，自动发现主 ASIN 的关联 ASIN 列表"""
    script_path = os.path.join(PROJECT_ROOT, "backend", "discover_related.py")
    if not os.path.exists(script_path):
        print(f"  [关联发现] discover_related.py 不存在，跳过")
        return []
    result = subprocess.run(
        [sys.executable, script_path, main_asin],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=os.path.join(PROJECT_ROOT, "backend"), timeout=120
    )
    if result.returncode == 0 and result.stdout:
        try:
            # 脚本输出 JSON 数组
            related = json.loads(result.stdout.strip().split("\n")[-1])
            print(f"  [关联发现] 主ASIN {main_asin} → {len(related)} 个关联ASIN")
            return related
        except:
            pass
    print(f"  [关联发现] 主ASIN {main_asin} 发现失败或无结果")
    return []


def run_monitor():
    sep = "=" * 60
    print("\n" + sep)
    print("CrossMart Monitor - 本地触发执行")
    print("时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(sep)

    trigger = load_trigger()
    if trigger is None:
        print("trigger.json 读取失败，请检查网络和仓库配置")
        return
    if trigger.get("status") != "pending":
        print("触发器状态: " + str(trigger.get("status")) + "，无需执行")
        return
    print("检测到 pending 触发器，上次触发: " + str(trigger.get("triggered_at")))

    # ── 加载新结构数据 ──
    main_asins       = load_main_asins()
    asin_related_map = load_asin_related()
    keyword_list    = load_keyword_list()

    print("主ASIN: %d 个 | 关联映射: %d 个 | 关键词: %d 个"
          % (len(main_asins), len(asin_related_map), len(keyword_list)))

    # ── 时间窗口判断 ──
    schedule = DEFAULT_SCHEDULE
    now = datetime.now()
    current_slot = None
    for slot_name, slot_cfg in schedule.items():
        if now_in_window(slot_cfg["window_start"], slot_cfg["window_end"]):
            current_slot = slot_name
            break
    if current_slot is None:
        print("[BYPASS] 强制执行模式")
        current_slot = "morning"
    slot_config = schedule[current_slot]
    print(f"\n当前窗口: {current_slot} ({slot_config['window_start']}-{slot_config['window_end']})")

    if not should_run(slot_config):
        print("本次不执行（随机跳过）")
        return

    jitter_max = slot_config.get("jitter_max_minutes", 30)
    wait_random(jitter_max, label=current_slot)

    # ── Phase 0: 人类行为模拟 ──
    browse_unrelated_pages()

    # ── Phase A: 关键词监控（保留，不变）──
    kw_list = [k.get("keyword", "").strip() for k in keyword_list if k.get("keyword")]
    random.shuffle(kw_list)
    for kw in kw_list:
        if not kw:
            continue
        print("\n--- 关键词监控: " + kw + " ---")
        ok = run_command(
            [sys.executable, "-m", "browser.keyword_monitor", kw],
            cwd=os.path.join(PROJECT_ROOT, "backend"), timeout=300)
        if not ok:
            print("  关键词 " + kw + " 执行失败，继续")
        time.sleep(random.randint(15, 40))

    # ── Phase B: 主 ASIN 监控 + 自动发现关联 ASIN ──
    for asin_entry in main_asins:
        main_asin = asin_entry.get("asin", "").strip()
        if not main_asin:
            continue

        print("\n--- 主ASIN监控: " + main_asin + " ---")
        ok = run_command(
            [sys.executable, "-m", "browser.asin_monitor", main_asin],
            cwd=os.path.join(PROJECT_ROOT, "backend"), timeout=300)
        if not ok:
            print("  ASIN " + main_asin + " 执行失败，继续")
        time.sleep(random.randint(20, 50))

        # 通过卖家精灵竞品查询自动发现关联 ASIN
        print(f"\n  [关联发现] 通过卖家精灵查询主ASIN {main_asin} 的竞品...")
        new_related = discover_related_asins_via_sprite(main_asin)

        # 更新 asin_related_asins.json（增量合并，不覆盖已有）
        updated = False
        old_list = asin_related_map.get(main_asin, [])
        old_asins = set(a.get("asin", "") for a in old_list)
        for a in new_related:
            if a.get("asin") and a.get("asin") not in old_asins:
                old_list.append(a)
                old_asins.add(a.get("asin"))
                updated = True
        if updated:
            asin_related_map[main_asin] = old_list
            save_asin_related(asin_related_map)
            print(f"  [关联发现] 已更新 asin_related_asins.json（主ASIN {main_asin} 共 {len(old_list)} 个关联）")
        else:
            print(f"  [关联发现] 无新增关联ASIN（现有 {len(old_list)} 个）")

    # ── Phase C: 关联 ASIN 监控（从 asin_related_asins.json 读取）──
    all_related = []
    for asin_entry in main_asins:
        main_asin = asin_entry.get("asin", "").strip()
        if not main_asin:
            continue
        related_list = asin_related_map.get(main_asin, [])
        for rel in related_list:
            rel_asin = rel.get("asin", "").strip()
            if rel_asin and rel_asin not in [a.get("asin") for a in all_related]:
                all_related.append(rel)

    if all_related:
        print(f"\n--- 关联ASIN批量监控: {len(all_related)} 个 ---")
        for rel in all_related:
            rel_asin = rel.get("asin", "")
            print("\n--- 关联ASIN: " + rel_asin + " ---")
            ok = run_command(
                [sys.executable, "-m", "browser.asin_monitor", rel_asin],
                cwd=os.path.join(PROJECT_ROOT, "backend"), timeout=300)
            if not ok:
                print("  关联ASIN " + rel_asin + " 执行失败，继续")
            time.sleep(random.randint(20, 50))
    else:
        print("\n--- 关联ASIN: 暂无（首次运行需等 Phase B 发现）---")

    # ── Phase D: 同步推送 ──
    print("\n--- 同步数据 ---")
    sync_and_push()

    trigger["status"] = "done"
    trigger["completed_at"] = datetime.now().isoformat()
    push_trigger_done(trigger)
    print("\n" + sep)
    print("监控完成！")
    print(sep)


if __name__ == "__main__":
    run_monitor()