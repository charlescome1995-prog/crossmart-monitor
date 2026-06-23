#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scheduled_run.py - 定时任务入口（替代已删除的 reset_and_run.py）
1. 确保 Edge 在 9225 端口运行（系统默认 profile，带卖家精灵插件）
2. 调用 backend/run_monitor.py 执行完整监控流程

定时任务的 .bat 调用本脚本。
"""
import os
import sys
import io

# 强制 UTF-8 输出，彻底避免 GBK UnicodeEncodeError（reset_and_run.py 的旧 bug）
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)


def _port_alive(port=9225):
    """检测 CDP 调试端口是否可用。"""
    import urllib.request, json as _json
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3)
        tabs = _json.loads(req.read())
        return bool(tabs is not None)
    except Exception:
        return False


def _kill_all_edge():
    """杀掉所有 msedge 进程（定时任务专用：保证 9225 一定能干净启动）。
    代价：会关掉用户当前正在用的所有 Edge 窗口/标签。"""
    import subprocess, time as _time
    try:
        subprocess.run(["taskkill", "/F", "/IM", "msedge.exe", "/T"],
                       capture_output=True, text=True)
        print("[scheduled_run] 已 taskkill 所有 msedge 进程")
    except Exception as e:
        print(f"[scheduled_run] taskkill 失败: {e}")
    _time.sleep(3)  # 等进程完全退出，释放 user-data-dir 锁


def ensure_edge():
    """确保 Edge 在 9225 端口运行（定时任务版）。

    关键修复：若 9225 端口未开（即便有 Edge 进程在跑，那些进程没开调试端口，
    新启动只会附加到现有实例而忽略 --remote-debugging-port），
    则先杀掉所有 Edge，再用 9225 干净重启。这样定时抓取一定能拿到调试端口。
    """
    try:
        from browser.cdp_bridge import ensure_edge_running, get_tab_count

        # 1. 端口已通 → 直接用
        if _port_alive(9225):
            cnt = get_tab_count(9225)
            print(f"[scheduled_run] Edge 9225 已就绪（无需重启），标签页={cnt}")
            return True

        # 2. 端口不通 → 先杀掉所有 Edge（含没开调试端口的日常窗口），再干净重启
        print("[scheduled_run] 9225 端口未开，先杀掉所有 Edge 再重启...")
        _kill_all_edge()

        ok = ensure_edge_running(port=9225)
        cnt = get_tab_count(9225) if ok else 0
        print(f"[scheduled_run] Edge 9225 就绪={ok}, 当前标签页={cnt}")

        # 3. 二次确认端口
        if not ok or not _port_alive(9225):
            print("[scheduled_run] 首次启动后端口仍不通，再杀一次并重试...")
            _kill_all_edge()
            ok = ensure_edge_running(port=9225)
            cnt = get_tab_count(9225) if ok else 0
            print(f"[scheduled_run] 重试结果 就绪={ok}, 标签页={cnt}")
        return ok and _port_alive(9225)
    except Exception as e:
        print(f"[scheduled_run] 启动 Edge 失败: {e}")
        return False


def main():
    print("=" * 60)
    print("[scheduled_run] 定时任务启动")
    print("=" * 60)

    ensure_edge()

    # 调用真正的监控入口 backend/run_monitor.py
    import subprocess
    run_monitor = os.path.join(BACKEND_DIR, "run_monitor.py")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["CDP_PORT"] = "9225"
    rc = subprocess.run(
        [sys.executable, run_monitor, "--scheduled"],
        cwd=BACKEND_DIR, env=env
    ).returncode
    print(f"[scheduled_run] run_monitor.py 退出码={rc}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
