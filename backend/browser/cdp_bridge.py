#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDP连接基类 - 控制闫旭的默认Edge浏览器
只有一个浏览器实例（默认Edge，有缓存/收藏/搜索记录）
所有操作都在同一个Edge里，开不同标签页完成
"""
import sys, os, json, time, base64, random, subprocess
sys.stdout.reconfigure(encoding='utf-8')
import websocket, urllib.request
from datetime import datetime

# ─── 项目路径 ───
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "output", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# ─── Edge配置 ───
# 就用闫旭的系统默认Edge，不新建任何profile
EDGE_PROFILE_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
# 优先从环境变量读取CDP端口（便于外层控制），否则默认9224
EDGE_PORT = int(os.environ.get("CDP_PORT", "9225"))

# OpenClaw管理的Edge CDP端口
OPENCLAW_CDP_PORT = 18800
OPENCLAW_CDP_URL = "http://127.0.0.1:18800"


def find_edge_exe():
    """查找Edge可执行文件"""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return "msedge"


def ensure_edge_running(port=None):
    """
    确保Edge在运行+CDP端口已开
    优先尝试OpenClaw管理的Edge（已有亚马逊登录态），失败则自动启动新实例。
    """
    if port is None:
        port = EDGE_PORT

    # 1. 优先尝试OpenClaw的CDP端口
    try:
        req = urllib.request.urlopen(f"{OPENCLAW_CDP_URL}/json", timeout=3)
        tabs = json.loads(req.read())
        if tabs and len(tabs) > 0:
            # 找到非devtools、非about:blank的标签页优先
            real_tabs = [t for t in tabs if t.get('url','') not in ('','about:blank') and 'devtools://' not in t.get('url','')]
            if real_tabs:
                print(f"  ✅ 连接OpenClaw管理的Edge (port=18800, {len(tabs)}个标签页)")
                return True
    except:
        pass

    # 2. 尝试指定端口
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3)
        tabs = json.loads(req.read())
        if tabs:
            print(f"  ✅ Edge已在运行 (port={port})")
            return True
    except:
        pass

    # 3. 启动新实例
    exe = find_edge_exe()
    print(f"  Edge未运行，启动中... (port={port})")

    # 使用OpenClaw已有profile目录（确保登录态）
    OPENCLAW_USER_DIR = os.path.expandvars(r"%USERPROFILE%\.openclaw\browser\openclaw\user-data")
    if os.path.exists(OPENCLAW_USER_DIR):
        profile_dir = OPENCLAW_USER_DIR
    else:
        profile_dir = EDGE_PROFILE_DIR

    print(f"  📂 Profile: {profile_dir}")
    args = [
        exe,
        f"--user-data-dir={profile_dir}",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
        "--new-window",
        "about:blank",
    ]
    subprocess.Popen(args)

    # 等待CDP端口可用
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3)
            tabs = json.loads(req.read())
            if tabs:
                print(f"  ✅ Edge启动成功 (port={port})")
                return True
        except:
            pass
        time.sleep(1)

    print(f"  ❌ Edge启动失败")
    return False


class CDPBrowser:
    """控制闫旭的默认Edge浏览器"""

    def __init__(self, auto_start=True):
        # 自动检测可用CDP端口
        self.port = self._detect_port()

        if not ensure_edge_running(self.port):
            raise RuntimeError("Edge无法启动")

        self._refresh_tabs()
        self._msg_id = 0
        self.ws = None
        self.tab = None
        print(f"  ✅ CDP已连接 — {len(self.tabs)}个标签页")

    def _detect_port(self):
        """检测哪个CDP端口可用：优先OpenClaw，其次默认端口"""
        ports_to_try = [OPENCLAW_CDP_PORT, EDGE_PORT]
        for p in ports_to_try:
            try:
                req = urllib.request.urlopen(f"http://127.0.0.1:{p}/json", timeout=3)
                tabs = json.loads(req.read())
                if tabs:
                    print(f"  📡 使用CDP端口: {p}")
                    return p
            except:
                pass
        return EDGE_PORT  # fallback，让ensure_edge_running去启动

    def _refresh_tabs(self):
        req = urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json", timeout=5)
        self._raw_tabs = json.loads(req.read())
        self.tabs = self._raw_tabs

    def connect_tab(self, tab_index=0, tab_url_filter=None):
        """连接到某个标签页"""
        self._refresh_tabs()
        tabs = self._raw_tabs

        if tab_url_filter:
            filtered = [t for t in tabs if tab_url_filter.lower() in (t.get("url","")+t.get("title","")).lower()]
            if filtered:
                self.tab = filtered[0]
            else:
                # 未找到，打开新标签页
                target = self.cmd("Target.createTarget", {"url": "about:blank"})
                target_id = target.get("targetId")
                time.sleep(1)
                self._refresh_tabs()
                # 找新开的标签页
                filtered_new = [t for t in self._raw_tabs if t.get("id") == target_id]
                self.tab = filtered_new[0] if filtered_new else self._raw_tabs[0]
        else:
            self.tab = tabs[tab_index] if tabs else None

        if not self.tab:
            raise RuntimeError("没有可用的标签页")

        ws_url = self.tab.get("webSocketDebuggerUrl")
        if not ws_url:
            raise RuntimeError(f"无法获取 WebSocket URL (tab: {self.tab.get('id','?')})")

        try:
            if self.ws:
                self.ws.close()
        except:
            pass

        self.ws = websocket.create_connection(ws_url, timeout=15)
        title = self.tab.get("title","")[:40]
        url = self.tab.get("url","")[:60]
        print(f"  📌 Tab: {title} | {url}")
        return self

    def _recv_until_id(self, target_id, timeout=15):
        """持续接收消息直到找到匹配id的响应"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                self.ws.settimeout(max(0.1, deadline - time.time()))
                raw = self.ws.recv()
                msg = json.loads(raw)
                if msg.get("id") == target_id:
                    return msg.get("result", {})
                # 忽略事件消息（没有id的）
            except websocket.WebSocketTimeoutException:
                continue
            except (ConnectionError, OSError):
                break
            except Exception:
                continue
        return {}

    def cmd(self, method, params=None):
        """发送CDP命令"""
        self._msg_id += 1
        self.ws.send(json.dumps({"method": method, "id": self._msg_id, "params": params or {}}))
        return self._recv_until_id(self._msg_id, timeout=15)

    def eval(self, js):
        """执行JS并返回值"""
        r = self.cmd("Runtime.evaluate", {"expression": js, "returnByValue": True, "awaitPromise": True})
        result = r.get("result", {})
        if result.get("type") == "string" and result.get("value") is None:
            return None
        return result.get("value")

    def navigate(self, url, wait_min=3, wait_max=6):
        """导航到URL，导航后重建WebSocket连接"""
        # 先保存当前tab id
        old_id = self.tab.get("id", "") if self.tab else ""
        try:
            self.cmd("Page.navigate", {"url": url})
        except:
            pass
        wait = random.uniform(wait_min, wait_max)
        time.sleep(max(wait, 3))
        # 导航后重建WebSocket ——用同一个tab id重新连
        try:
            self.ws.close()
        except:
            pass
        self._refresh_tabs()
        # 用旧的tab id找这个标签页
        new_tab = None
        for t in self._raw_tabs:
            if t.get("id") == old_id:
                new_tab = t
                break
        if not new_tab and self._raw_tabs:
            new_tab = self._raw_tabs[0]
        if new_tab:
            ws_url = new_tab.get("webSocketDebuggerUrl")
            if ws_url:
                self.ws = websocket.create_connection(ws_url, timeout=10)
                self.tab = new_tab
        title = self.eval("document.title") or ""
        print(f"  → {url}")
        print(f"     {title[:60]}")
        return title

    def screenshot(self, name=None):
        """截取当前页面截图"""
        if name is None:
            name = datetime.now().strftime("ss_%Y%m%d_%H%M%S")
        r = self.cmd("Page.captureScreenshot", {"format": "png", "fromSurface": True})
        data = r.get("data", "")
        if data:
            path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
            with open(path, "wb") as f:
                f.write(base64.b64decode(data))
            return path
        return None

    def scroll_down(self, times=1, min_pause=1, max_pause=3):
        for i in range(times):
            d = random.randint(200, 600)
            self.eval(f"window.scrollBy(0, {d})")
            time.sleep(random.uniform(min_pause, max_pause))

    def scroll_up(self, times=1, min_pause=1, max_pause=3):
        for i in range(times):
            d = random.randint(100, 400)
            self.eval(f"window.scrollBy(0, -{d})")
            time.sleep(random.uniform(min_pause, max_pause))

    def random_pause(self, min_sec=2, max_sec=8):
        time.sleep(random.uniform(min_sec, max_sec))

    def click_element(self, selector):
        js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return false;
            el.scrollIntoView({{behavior:'smooth', block:'center'}});
            setTimeout(() => el.click(), 100);
            return true;
        }})()
        """
        return self.eval(js)

    def get_text(self, selector):
        return self.eval(f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                return el ? el.textContent.trim() : null;
            }})()
        """)

    def open_new_tab(self, url="about:blank"):
        """打开新标签页并切换到它"""
        result = self.cmd("Target.createTarget", {"url": url})
        target_id = result.get("targetId")
        time.sleep(1)
        self._refresh_tabs()
        for t in self._raw_tabs:
            if t.get("id") == target_id:
                ws_url = t.get("webSocketDebuggerUrl")
                try: self.ws.close()
                except: pass
                self.ws = websocket.create_connection(ws_url, timeout=10)
                self.tab = t
                return True
        return False

    def close_all_new_tabs(self, keep_url_filter=None):
        """
        关掉我打开的新标签页，保留原来的
        keep_url_filter: 保留包含此关键字的标签页
        """
        self._refresh_tabs()
        # 简单做法：只关掉 about:blank 和 sellersprite
        for t in self._raw_tabs:
            url = t.get("url","")
            if "about:blank" in url or "sellersprite" in url:
                tid = t.get("id")
                if tid and tid != self.tab.get("id"):
                    self.cmd("Target.closeTarget", {"targetId": tid})
        print("  🧹 清理了临时标签页")

    def close(self):
        try:
            self.ws.close()
        except:
            pass


def start_default_edge():
    """启动闫旭的默认Edge（带缓存/收藏/卖家精灵插件）"""
    return ensure_edge_running()
