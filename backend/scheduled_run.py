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


def ensure_edge():
    """确保 Edge 在 9225 端口运行。"""
    try:
        from browser.cdp_bridge import ensure_edge_running, get_tab_count
        ok = ensure_edge_running(port=9225)
        cnt = get_tab_count(9225)
        print(f"[scheduled_run] Edge 9225 就绪={ok}, 当前标签页={cnt}")
        return ok
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
        [sys.executable, run_monitor],
        cwd=BACKEND_DIR, env=env
    ).returncode
    print(f"[scheduled_run] run_monitor.py 退出码={rc}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
