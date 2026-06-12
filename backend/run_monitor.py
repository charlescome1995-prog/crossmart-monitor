#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_monitor.py - 跨境电商 ASIN 监控系统入口
支持随机化、时间窗口、概率运行、人类行为模拟。
恢复旧逻辑：从 GitHub user_config.json 读取 asins + keywords 配置。
"""
import os, sys, json, time, random, subprocess, urllib.request, glob
from datetime import datetime

# 积加 API 客户端
try:
    from jike_client import get_jike_data_for_asins
    JIKE_AVAILABLE = True
except Exception:
    JIKE_AVAILABLE = False
    print("[WARNING] 积加 API 模块加载失败，监控将跳过积加数据抓取")
sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data")
TRIGGER_FILE = os.path.join(DATA_DIR, "trigger.json")
CONFIG_FILE = os.path.join(DATA_DIR, "user_config.json")
REPO = "charlescome1995-prog/crossmart-monitor"

DEFAULT_SCHEDULE = {
    "morning":   {"anchor": "06:20", "window_start": "06:20", "window_end": "07:20", "jitter_max_minutes": 1, "run_probability": 1.0},
    "midday":     {"anchor": "06:30", "window_start": "06:30", "window_end": "07:30", "jitter_max_minutes": 1, "run_probability": 1.0},
    "evening":    {"anchor": "06:40", "window_start": "06:40", "window_end": "07:40", "jitter_max_minutes": 1, "run_probability": 1.0},
}

KEYWORD_LIST_FILE = os.path.join(DATA_DIR, "keyword_list.json")
KW_RELATED_FILE   = os.path.join(DATA_DIR, "keyword_related_asins.json")


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


def gh_update_json_file(path, new_content):
    """通过 GitHub API 更新仓库中的 JSON 文件（不依赖 git push）"""
    import base64
    api_url = "https://api.github.com/repos/" + REPO + "/contents/" + path
    try:
        req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            current = json.loads(r.read())
        sha = current["sha"]
        encoded = base64.b64encode(new_content.encode("utf-8")).decode("ascii")
        payload = json.dumps({
            "message": "auto: update " + path,
            "content": encoded,
            "sha": sha
        }).encode("utf-8")
        put_req = urllib.request.Request(api_url, data=payload,
            headers={"Accept": "application/vnd.github.v3+json",
                     "Content-Type": "application/json"},
            method="PUT")
        with urllib.request.urlopen(put_req, timeout=15) as r2:
            return json.loads(r2.read())
    except Exception as e:
        print("  gh_update " + path + " error: " + str(e))
        return None


def load_trigger():
    return gh_fetch_json("backend/data/trigger.json")


def load_config():
    """从 GitHub user_config.json 加载配置（恢复旧逻辑）"""
    data = gh_fetch_json("backend/data/user_config.json")
    if data is None:
        return {"asins": [], "keywords": [], "schedule": DEFAULT_SCHEDULE}
    return data


def load_keyword_list():
    """加载本地关键词列表（作为补充）"""
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
    """同步数据并推送 GitHub"""
    sync_script = os.path.join(PROJECT_ROOT, "backend", "sync_monitor_data.py")
    if not os.path.exists(sync_script):
        print("  sync_monitor_data.py not found, skip sync")
        return True
    ok = run_command([sys.executable, sync_script], timeout=120)
    if not ok:
        print("  sync failed")
        return False
    repo_dir = PROJECT_ROOT
    subprocess.run(["git", "config", "--global", "user.name", "CrossMart Bot"],
        shell=False, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run(["git", "config", "--global", "user.email", "bot@crossmart.ai"],
        shell=False, cwd=repo_dir, encoding="utf-8", errors="replace")
    result = subprocess.run(["git", "status", "--porcelain"],
        shell=False, cwd=repo_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    run_command(["git", "commit", "-m", "auto: sync " + ts],
        cwd=repo_dir, timeout=30)
    push_ok = run_command(["git", "push"], cwd=repo_dir, timeout=60)
    if not push_ok:
        print("  push rejected, force-push...")
        run_command(["git", "push", "-f"], cwd=repo_dir, timeout=60)
    print("  数据已推送")
    return True


def push_trigger_done(trigger):
    """更新 trigger.json 状态并推送"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TRIGGER_FILE, "w", encoding="utf-8") as f:
        json.dump(trigger, f, ensure_ascii=False, indent=2)
    repo_dir = PROJECT_ROOT
    subprocess.run(["git", "config", "--global", "user.name", "CrossMart Bot"],
        shell=False, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run(["git", "config", "--global", "user.email", "bot@crossmart.ai"],
        shell=False, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run(["git", "add", TRIGGER_FILE],
        shell=False, cwd=repo_dir, encoding="utf-8", errors="replace")
    subprocess.run(["git", "commit", "-m", "auto: trigger done"],
        shell=False, cwd=repo_dir, encoding="utf-8", errors="replace")
    pr = subprocess.run(["git", "push"],
        shell=False, cwd=repo_dir, timeout=60, encoding="utf-8", errors="replace")
    if pr.returncode != 0:
        print("  force-pushing trigger...")
        subprocess.run(["git", "push", "-f"],
            shell=False, cwd=repo_dir, timeout=60, encoding="utf-8", errors="replace")
    print("  trigger.json 已推送")


def browse_unrelated_pages():
    print("  [Phase 0] 人类行为模拟：先逛几个无关页面...")
    urls = ["https://www.amazon.com", "https://www.amazon.com/gp/bestsellers/"]
    random.shuffle(urls)
    for url in urls[:2]:
        print(f"  浏览: {url}")
        time.sleep(random.randint(3, 8))


def run_monitor(config_override=None):
    """主监控逻辑"""
    sep = "=" * 60
    print("\n" + sep)
    print("CrossMart Monitor - 本地触发执行")
    print("时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(sep)

    # config_override: 直接传入配置（API 触发时用），否则从 GitHub 读
    if config_override is not None:
        config = config_override
        asins = config.get("asins", [])
        keywords = config.get("keywords", [])
        schedule = config.get("schedule", DEFAULT_SCHEDULE)
        trigger = {}  # API 模式：trigger 由 api_server.py 管理本地文件无需写入
        print("[CONFIG] 使用 API 传入配置: " + str(len(asins)) + " 个ASIN, " + str(len(keywords)) + " 个关键词")
    else:
        trigger = load_trigger()
        if trigger is None:
            print("trigger.json 读取失败，请检查网络和仓库配置")
            return
        if trigger.get("status") != "pending":
            print("触发器状态: " + str(trigger.get("status")) + "，无需执行")
            return
        print("检测到 pending 触发器，上次触发: " + str(trigger.get("triggered_at")))
        config = load_config()
        asins = config.get("asins", [])
        keywords = config.get("keywords", [])
        schedule = config.get("schedule", DEFAULT_SCHEDULE)

    print("配置: " + str(len(asins)) + " 个ASIN, " + str(len(keywords)) + " 个关键词")

    # ── 已抓取ASIN去重集合 ──
    seen_asins = set()

    # ── 时间窗口判断 ──
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

    # ── Phase A: 关键词监控 ──
    random.shuffle(keywords)
    for kw_entry in keywords:
        kw = kw_entry.get("main", "").strip()
        if not kw:
            continue
        print("\n--- 关键词监控: " + kw + " ---")
        ok = run_command(
            [sys.executable, "-m", "browser.keyword_monitor", kw],
            cwd=os.path.join(PROJECT_ROOT, "backend"), timeout=300)
        if not ok:
            print("  关键词 " + kw + " 执行失败，继续")
        time.sleep(random.randint(15, 40))

        # ── Phase A2: 抓取关键词 Top5 ASIN 的完整详情 ──
        kw_safe = kw.replace(" ", "_").replace("/", "_")
        kw_latest = os.path.join(DATA_DIR, "processed", f"kw_{kw_safe}", "latest.json")
        if os.path.exists(kw_latest):
            with open(kw_latest, "r", encoding="utf-8") as f:
                kw_data = json.load(f)
            top5 = kw_data.get("top_asins", [])
            for a in top5:
                aasin = a.get("asin", "").strip()
                if not aasin:
                    continue
                if aasin in seen_asins:
                    print(f"  [跳过] ASIN {aasin} 已抓过（来源：关键词{kw}），继续")
                    continue
                seen_asins.add(aasin)
                print(f"\n--- 关键词ASIN详情: {aasin} (来源: {kw}) ---")
                ok = run_command(
                    [sys.executable, "-m", "browser.asin_monitor", aasin, "--amazon"],
                    cwd=os.path.join(PROJECT_ROOT, "backend"), timeout=300)
                if not ok:
                    print(f"  关键词ASIN {aasin} 执行失败，继续")
                time.sleep(random.randint(20, 50))

    # ── Phase B: ASIN 监控（主ASIN + 关联ASIN）──
    random.shuffle(asins)
    for asin_entry in asins:
        main_asin = asin_entry.get("main", "").strip()
        if not main_asin:
            continue
        if main_asin in seen_asins:
            print(f"  [跳过] 主ASIN {main_asin} 已抓过，继续")
            continue
        seen_asins.add(main_asin)

        print("\n--- 主ASIN监控: " + main_asin + " ---")
        ok = run_command(
            [sys.executable, "-m", "browser.asin_monitor", main_asin, "--amazon"],
            cwd=os.path.join(PROJECT_ROOT, "backend"), timeout=300)
        if not ok:
            print("  ASIN " + main_asin + " 执行失败，继续")
        else:
            # 主ASIN抓取成功后，调用积加API
            if JIKE_AVAILABLE:
                try:
                    print("  调用积加 API... ")
                    jike_data = get_jike_data_for_asins([main_asin])
                    # 保存积加数据到 processed 目录
                    asin_dir = os.path.join(PROJECT_ROOT, "backend", "data", "processed", f"asin_{main_asin}")
                    os.makedirs(asin_dir, exist_ok=True)
                    jike_path = os.path.join(asin_dir, "jike_latest.json")
                    with open(jike_path, "w", encoding="utf-8") as f:
                        json.dump(jike_data, f)
                    print(f"  积加数据已保存: {jike_path}")
                except Exception as e:
                    print(f"  积加API调用失败: {e}")
        time.sleep(5)  # 积加 API 限流：每 5 秒最多 1 次请求
        time.sleep(random.randint(20, 50))

        # 抓取用户配置的关联 ASIN
        related_list = asin_entry.get("related", [])
        for rel_asin in related_list:
            rel_asin = rel_asin.strip()
            if not rel_asin:
                continue
            if rel_asin in seen_asins:
                print(f"  [跳过] 关联ASIN {rel_asin} 已抓过，继续")
                continue
            seen_asins.add(rel_asin)
            print("\n--- 关联竞品: " + rel_asin + " ---")
            ok = run_command(
                [sys.executable, "-m", "browser.asin_monitor", rel_asin, "--amazon"],
                cwd=os.path.join(PROJECT_ROOT, "backend"), timeout=300)
            if not ok:
                print("  关联ASIN " + rel_asin + " 执行失败，继续")
            time.sleep(random.randint(20, 50))

        # ── 写入 _meta.json（记录关联ASIN，供 sync_monitor_data.py 判断 logic_type）─────────
        try:
            from browser.snapshot_storage import save_asin_meta
            meta_related = [{"asin": ra.strip(), "source": "user_related"}
                           for ra in related_list if ra.strip()]
            if meta_related:
                save_asin_meta(main_asin, meta_related)
                print(f"  [_meta] 已写入 {len(meta_related)} 个关联ASIN")
        except Exception as e:
            print(f"  [_meta] 写入失败: {e}")

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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, help='JSON config string (bypass GitHub read)')
    args = parser.parse_args()
    _cfg = None
    if args.config and args.config.strip():
        _cfg = json.loads(args.config)
    run_monitor(config_override=_cfg)