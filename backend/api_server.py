#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api_server.py - CrossMart Monitor 本地API服务
启动后: http://127.0.0.1:8765

工作流程：
1. 接收前端传来的主ASIN列表
2. 对每个主ASIN，从卖家精灵查找最多4个关联ASIN
3. 组合成 主ASIN + 关联ASIN = 5个一组
4. 逐个抓取亚马逊数据（asin_monitor）
5. 同步到前端

新架构（2026-06-02）：纯本地轮询
- 前端写入 trigger.json 到 GitHub
- api_server.py 轮询 GitHub trigger.json，检测到 pending 则执行 run_monitor.py
- 不再依赖 127.0.0.1:8765（远程访问不可达的问题）
"""
import sys, os, json, subprocess, threading, time, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
os.environ["CDP_PORT"] = "9225"
from http.server import HTTPServer, BaseHTTPRequestHandler

PROJECT = os.path.dirname(os.path.abspath(__file__))
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}

REPO = "charlescome1995-prog/crossmart-monitor"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main"
API_BASE = f"https://api.github.com/repos/{REPO}"

SCRAPE_STATUS = {"running": False, "last_result": None, "progress": "", "trigger_mode": False}
MONITOR_PROCESS = None
USER_CONFIG_PATH = os.path.join(PROJECT, 'data', 'user_config.json')
GH_TOKEN_PATH = os.path.join(PROJECT, 'data', 'gh_token.txt')
GH_TOKEN = os.environ.get("GH_TOKEN", "")

# 从本地文件读取 token（由前端写入）
def load_gh_token():
    global GH_TOKEN
    if GH_TOKEN:
        return GH_TOKEN
    if os.path.exists(GH_TOKEN_PATH):
        with open(GH_TOKEN_PATH, 'r', encoding='utf-8') as f:
            GH_TOKEN = f.read().strip()
    return GH_TOKEN

def save_gh_token(token):
    global GH_TOKEN
    GH_TOKEN = token
    os.makedirs(os.path.dirname(GH_TOKEN_PATH), exist_ok=True)
    with open(GH_TOKEN_PATH, 'w', encoding='utf-8') as f:
        f.write(token)
    print(f"[Token] 已保存到本地 ({len(token)} chars)")

def load_config_from_github():
    """从GitHub加载用户配置（云端加载）"""
    token = load_gh_token()
    if not token:
        print("[配置] GH_TOKEN 未设置，尝试本地文件")
        if os.path.exists(USER_CONFIG_PATH):
            with open(USER_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    try:
        url = f"{RAW_BASE}/backend/data/user_config.json"
        req = urllib.request.Request(url, headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3.raw",
            "User-Agent": "crossmart-monitor/1.0"
        })
        with urllib.request.urlopen(req, timeout=30) as r:
            content = r.read().decode("utf-8")
            print(f"[配置] 从GitHub加载: {content[:100]}")
            return json.loads(content)
    except Exception as e:
        print(f"[配置] GitHub加载失败: {e}，回退到本地文件")
        if os.path.exists(USER_CONFIG_PATH):
            with open(USER_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

def fetch_github_json(url):
    """从GitHub获取JSON（带token认证）"""
    token = load_gh_token()
    if not token:
        return None
    try:
        req = urllib.request.Request(url, headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "crossmart-monitor/1.0"
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"[GitHub] 请求失败 {url}: {e}")
        return None

def update_trigger_on_github(status, progress=""):
    """更新GitHub上的trigger.json状态"""
    token = load_gh_token()
    if not token:
        return
    import base64
    try:
        url = f"{API_BASE}/contents/backend/data/trigger.json"
        req = urllib.request.Request(url, headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "crossmart-monitor/1.0"
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            current = json.loads(r.read().decode("utf-8"))
            sha = current.get("sha", "")

        content = json.dumps({
            "status": status,
            "triggered_at": current.get("triggered_at", ""),
            "progress": progress,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        }, ensure_ascii=False)
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")

        put_req = urllib.request.Request(url, method="PUT", headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "User-Agent": "crossmart-monitor/1.0"
        })
        body = json.dumps({
            "message": "update trigger status",
            "content": encoded,
            "sha": sha
        }).encode("utf-8")
        put_req.data = body
        with urllib.request.urlopen(put_req, timeout=10) as r:
            print(f"[Trigger] GitHub trigger.json 更新为 {status}")
    except Exception as e:
        print(f"[Trigger] 更新失败: {e}")

def ensure_edge():
    """确保Edge在9225端口运行"""
    try:
        r = urllib.request.urlopen("http://127.0.0.1:9225/json", timeout=3)
        tabs = json.loads(r.read())
        print("[Edge] 已连接 (%d个标签页)" % len(tabs))
        return True
    except:
        pass
    # 自动启动Edge
    exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(exe):
        exe = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    print("[Edge] 启动中...")
    subprocess.Popen([
        exe,
        "--remote-debugging-port=9225",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
        "--new-window",
        "about:blank",
    ])
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            r = urllib.request.urlopen("http://127.0.0.1:9225/json", timeout=3)
            json.loads(r.read())
            print("[Edge] 启动成功")
            return True
        except:
            time.sleep(2)
    print("[Edge] 启动失败")
    return False

def find_related_asins(main_asin, max_count=4):
    """
    用卖家精灵查找一个ASIN的关联ASIN。
    返回最多 max_count 个关联ASIN。
    """
    print("[关联] 查找 %s 的关联ASIN..." % main_asin)
    try:
        from browser.cdp_bridge import CDPBrowser
        from browser.sprite_bridge import SpriteBrowser

        browser = CDPBrowser()
        browser.connect_tab(tab_url_filter="about:blank")
        if not browser.tab:
            browser.cmd("Target.createTarget", {"url": "about:blank"})
            time.sleep(0.5)
            browser.connect_tab(tab_url_filter="about:blank")

        sprite = SpriteBrowser(browser)
        related = sprite.find_related_asins(main_asin, max_results=max_count)
        browser.close()
        return related
    except Exception as e:
        print("[关联] 查找失败: %s" % e)
        return []

def run_full_scrape(main_asins):
    """完整抓取流程"""
    global SCRAPE_STATUS
    all_asins = []      # 最终要抓的所有ASIN
    related_map = {}    # 主ASIN -> 关联ASIN列表

    # Step 1: 对每个主ASIN查找关联
    for idx, main_asin in enumerate(main_asins):
        main_asin = main_asin.strip()
        if not main_asin:
            continue
        print("\n[步骤 %d/%d] 处理主ASIN: %s" % (idx+1, len(main_asins), main_asin))
        SCRAPE_STATUS["progress"] = "处理主ASIN %s... 正在查找竞品" % main_asin

        related = find_related_asins(main_asin)
        if related:
            related_map[main_asin] = related
            # 主ASIN + 最多4个关联
            group = [main_asin] + related[:4]
            all_asins.extend(group)
            print("[步骤] 组合: %s + %d个关联 = %d个" % (main_asin, len(related), len(group)))
        else:
            # 没找到关联，只抓主ASIN本身
            all_asins.append(main_asin)
            print("[步骤] %s 无关联ASIN，只抓主ASIN" % main_asin)

    if not all_asins:
        # fallback
        all_asins = ["B09V7Z4TJG"]

    # Step 2: 逐个抓取
    print("\n[抓取] 共 %d 个ASIN: %s" % (len(all_asins), all_asins))
    results = []

    for idx, asin in enumerate(all_asins):
        print("\n[抓取 %d/%d] %s..." % (idx+1, len(all_asins), asin))
        SCRAPE_STATUS["progress"] = "抓取 %d/%d: %s" % (idx+1, len(all_asins), asin)

        try:
            from browser.asin_monitor import check_asin
            # 抓取时只查亚马逊前台，不查卖家精灵（关联ASIN已在前面查过）
            result = check_asin(asin, use_sprite=False)
            results.append(result)
        except Exception as e:
            import traceback
            print("[抓取] %s 失败: %s" % (asin, e))
            traceback.print_exc()

    # Step 3: 同步到前端
    print("\n[同步] 同步到前端...")
    SCRAPE_STATUS["progress"] = "同步数据到前端..."
    try:
        subprocess.run([
            sys.executable,
            os.path.join(PROJECT, "sync_to_frontend.py")
        ], cwd=PROJECT, capture_output=True, text=True, timeout=60);
        subprocess.run([
            sys.executable,
            os.path.join(PROJECT, "sync_monitor_data.py")
        ], cwd=PROJECT, capture_output=True, text=True, timeout=60)
    except Exception as e:
        print("[同步] 失败: %s" % e)

    SCRAPE_STATUS["last_result"] = {
        "status": "ok",
        "count": len(results),
        "asins": [r.get("asin", "?") for r in results],
        "related_map": {k: v for k, v in related_map.items()}
    }
    print("\n[完成] 采集 %d 个ASIN" % len(results))

# =============================================================================
# 轮询线程：从 GitHub 读取 trigger.json，检测到 pending 则执行抓取
# =============================================================================
POLL_INTERVAL = 10  # 每 10 秒检查一次

def polling_worker():
    """后台轮询线程：检查 GitHub trigger.json，发现 pending 则执行"""
    global SCRAPE_STATUS, MONITOR_PROCESS
    print(f"[轮询] 启动，每 {POLL_INTERVAL} 秒检查 GitHub trigger.json")
    
    while True:
        time.sleep(POLL_INTERVAL)
        
        if SCRAPE_STATUS["running"]:
            continue
        
        token = load_gh_token()
        if not token:
            continue
        
        try:
            url = f"{RAW_BASE}/backend/data/trigger.json?t={time.time()}"
            req = urllib.request.Request(url, headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3.raw",
                "User-Agent": "crossmart-monitor/1.0"
            })
            with urllib.request.urlopen(req, timeout=15) as r:
                trigger_data = json.loads(r.read().decode("utf-8"))
            
            if trigger_data.get("status") == "pending":
                print("\n[轮询] 检测到 trigger.json pending，开始执行抓取...")
                SCRAPE_STATUS["running"] = True
                SCRAPE_STATUS["progress"] = "正在从 GitHub 加载配置..."
                
                # 加载配置
                config = load_config_from_github()
                if not config:
                    print("[轮询] 无法加载配置，停止")
                    update_trigger_on_github("error", "配置加载失败")
                    SCRAPE_STATUS["running"] = False
                    continue
                
                asins = config.get("asins", [])
                keywords = config.get("keywords", [])
                
                # 保存到本地
                os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
                with open(USER_CONFIG_PATH, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                try:
                    os.chdir(PROJECT)
                    os.environ["CDP_PORT"] = "9225"
                    
                    if not ensure_edge():
                        update_trigger_on_github("error", "Edge 启动失败")
                        SCRAPE_STATUS["running"] = False
                        continue
                    
                    update_trigger_on_github("running", "开始抓取...")
                    SCRAPE_STATUS["progress"] = "运行 run_monitor.py..."
                    
                    # 执行 run_monitor.py
                    monitor_script = os.path.join(PROJECT, "run_monitor.py")
                    env = os.environ.copy()
                    env['CDP_PORT'] = '9225'
                    env['GH_TOKEN'] = token
                    
                    proc = subprocess.Popen(
                        [sys.executable, monitor_script, '--config', json.dumps(config, ensure_ascii=False)],
                        cwd=PROJECT,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding='utf-8',
                        errors='replace'
                    )
                    for line in proc.stdout:
                        print(f"[run] {line}", end='')
                    proc.wait()
                    returncode = proc.returncode
                    
                    if returncode == 0:
                        update_trigger_on_github("done", "抓取完成")
                        print("[轮询] run_monitor.py 执行完成")
                    else:
                        update_trigger_on_github("error", f"执行失败: {returncode}")
                        print(f"[轮询] run_monitor.py 失败 (exit {returncode})")
                    
                except subprocess.TimeoutExpired:
                    update_trigger_on_github("error", "执行超时（600秒）")
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    update_trigger_on_github("error", str(e))
                finally:
                    SCRAPE_STATUS["running"] = False
                    SCRAPE_STATUS["progress"] = ""
        
        except Exception as e:
            # 网络错误不打印，避免刷屏
            pass

class ScrapeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print("[API] %s - %s" % (self.client_address[0], format % args))

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/status":
            self._send_json({
                "scrape_running": SCRAPE_STATUS["running"],
                "progress": SCRAPE_STATUS["progress"],
                "last_result": SCRAPE_STATUS["last_result"]
            })
        elif self.path == "/api/config":
            cfg = load_config_from_github()
            self._send_json(cfg or {})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/api/scrape":
            self._handle_scrape()
        elif self.path == "/api/save-config":
            self._handle_save_config()
        elif self.path == "/api/trigger":
            self._handle_trigger()
        elif self.path == "/api/token":
            self._handle_token()
        else:
            self._send_json({"error": "not found"}, 404)

    def _handle_token(self):
        """前端写入 GitHub Token（保存到本地文件，供轮询线程使用）"""
        content_len = int(self.headers.get("Content-Length", 0))
        body = b""
        if content_len > 0:
            body = self.rfile.read(content_len)
        if not body:
            self._send_json({"status": "error"}, 400)
            return
        try:
            data = json.loads(body)
            token = data.get("token", "")
            if token:
                save_gh_token(token)
                self._send_json({"status": "ok"})
            else:
                self._send_json({"status": "error"}, 400)
        except:
            self._send_json({"status": "error"}, 400)

    def push_user_config_to_github(config_obj):
        """将 user_config.json 同步推送到 GitHub 仓库"""
        token = load_gh_token()
        if not token:
            print("[GitHub推送] 未配置 token，跳过")
            return False
        import base64
        content = json.dumps(config_obj, ensure_ascii=False, indent=2)
        encoded = base64.b64encode(content.encode('utf-8')).decode('ascii')
        path = 'backend/data/user_config.json'
        api_url = f"{API_BASE}/contents/{path}"
        # 先获取当前 SHA
        req = urllib.request.Request(api_url, headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'})
        sha = None
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                sha = json.loads(r.read()).get('sha')
        except Exception:
            pass  # 文件不存在则 sha 为 None
        payload = json.dumps({
            'message': 'chore: sync user_config.json from local',
            'content': encoded,
            'sha': sha
        }).encode('utf-8')
        req = urllib.request.Request(api_url, data=payload, headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}, method='PUT')
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                print("[GitHub推送] 成功")
                return True
        except Exception as e:
            print(f"[GitHub推送] 失败: {e}")
            return False

    def _handle_save_config(self):
        """保存用户输入的ASIN和关键词到本地文件"""
        content_len = int(self.headers.get("Content-Length", 0))
        body = b""
        if content_len > 0:
            body = self.rfile.read(content_len)

        if not body:
            self._send_json({"status": "error", "message": "empty body"}, 400)
            return

        try:
            data = json.loads(body)
            asins = data.get("asins", [])
            keywords = data.get("keywords", [])

            config = {
                "asins": asins,
                "keywords": keywords,
                "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S")
            }

            os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
            with open(USER_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            print("[保存] ASINs=%d, KWs=%d -> %s" % (len(asins), len(keywords), USER_CONFIG_PATH))
            # 同步推送到 GitHub
            push_user_config_to_github(config)
            self._send_json({
                "status": "ok",
                "message": "配置已保存到本地",
                "path": USER_CONFIG_PATH,
                "count": {"asins": len(asins), "keywords": len(keywords)}
            })
        except Exception as e:
            print("[保存] 失败: %s" % e)
            self._send_json({"status": "error", "message": str(e)}, 500)

    def _handle_scrape(self):
        global SCRAPE_STATUS

        if SCRAPE_STATUS["running"]:
            self._send_json({"status": "busy", "message": "正在采集中，请稍候"})
            return

        main_asins = []
        gh_config = load_config_from_github()
        if gh_config:
            main_asins = [a.strip() for a in gh_config.get("asins", []) if a.strip()]
            print(f"[配置] 使用GitHub配置，共 {len(main_asins)} 个ASIN: {main_asins}")

        if not main_asins:
            content_len = int(self.headers.get("Content-Length", 0))
            body = b""
            if content_len > 0:
                body = self.rfile.read(content_len)
            if body:
                try:
                    data = json.loads(body)
                    main_asins = [a.strip() for a in data.get("asins", []) if a.strip()]
                except:
                    pass

        if not main_asins:
            main_asins = ["B09V7Z4TJG"]

        self._send_json({"status": "ok", "message": "开始处理 %d 个主ASIN" % len(main_asins)})

        SCRAPE_STATUS["running"] = True
        SCRAPE_STATUS["last_result"] = None
        SCRAPE_STATUS["progress"] = "准备中..."

        def run():
            global SCRAPE_STATUS
            try:
                os.chdir(PROJECT)
                sys.path.insert(0, PROJECT)

                if not ensure_edge():
                    SCRAPE_STATUS["running"] = False
                    SCRAPE_STATUS["last_result"] = {"status": "error", "error": "Edge启动失败"}
                    return

                run_full_scrape(main_asins)
            except Exception as e:
                import traceback
                print("[异常] %s" % e)
                traceback.print_exc()
                SCRAPE_STATUS["last_result"] = {"status": "error", "error": str(e)}
            finally:
                SCRAPE_STATUS["running"] = False
                SCRAPE_STATUS["progress"] = ""

        t = threading.Thread(target=run, daemon=True)
        t.start()

    def _handle_trigger(self):
        """触发完整监控流程（Phase A→B→B2→C→D），启动 run_monitor.py"""
        global SCRAPE_STATUS, MONITOR_PROCESS

        if SCRAPE_STATUS["running"] and SCRAPE_STATUS.get("trigger_mode"):
            self._send_json({"status": "busy", "message": "正在采集中，请稍候"})
            return

        content_len = int(self.headers.get("Content-Length", 0))
        body = b""
        if content_len > 0:
            body = self.rfile.read(content_len)

        asins, keywords = [], []
        if body:
            try:
                data = json.loads(body)
                asins = data.get("asins", [])
                keywords = data.get("keywords", [])
            except:
                pass

        if not asins and not keywords:
            gh = load_config_from_github()
            if gh:
                asins = gh.get("asins", [])
                keywords = gh.get("keywords", [])

        config = {"asins": asins, "keywords": keywords}
        os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
        with open(USER_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        self._send_json({"status": "ok", "message": "触发成功，采集线程已启动", "asins": len(asins), "keywords": len(keywords)})

        SCRAPE_STATUS["running"] = True
        SCRAPE_STATUS["trigger_mode"] = True
        SCRAPE_STATUS["progress"] = "准备启动 Edge..."
        SCRAPE_STATUS["last_result"] = None

        def run():
            global SCRAPE_STATUS, MONITOR_PROCESS
            try:
                os.chdir(PROJECT)
                os.environ["CDP_PORT"] = "9225"

                if not ensure_edge():
                    SCRAPE_STATUS["last_result"] = {"status": "error", "error": "Edge启动失败"}
                    SCRAPE_STATUS["running"] = False
                    return

                SCRAPE_STATUS["progress"] = "运行 run_monitor.py..."

                cfg_json = json.dumps(config, ensure_ascii=False)
                monitor_script = os.path.join(PROJECT, "run_monitor.py")
                env = os.environ.copy()
                env['CDP_PORT'] = '9225'
                token = load_gh_token()
                if token:
                    env['GH_TOKEN'] = token
                MONITOR_PROCESS = subprocess.run(
                    [sys.executable, monitor_script, '--config', cfg_json],
                    cwd=PROJECT,
                    env=env,
                    timeout=600
                )
                SCRAPE_STATUS["last_result"] = {"status": "ok", "message": "采集完成"}
            except subprocess.TimeoutExpired:
                SCRAPE_STATUS["last_result"] = {"status": "error", "error": "超时（600s）"}
            except Exception as e:
                import traceback
                traceback.print_exc()
                SCRAPE_STATUS["last_result"] = {"status": "error", "error": str(e)}
            finally:
                SCRAPE_STATUS["running"] = False
                SCRAPE_STATUS["trigger_mode"] = False
                SCRAPE_STATUS["progress"] = ""
                MONITOR_PROCESS = None

        t = threading.Thread(target=run, daemon=True)
        t.start()

def main():
    # 启动轮询线程
    poll_thread = threading.Thread(target=polling_worker, daemon=True)
    poll_thread.start()
    
    port = 8765
    server = HTTPServer(("127.0.0.1", port), ScrapeHandler)
    print("=" * 60)
    print("CrossMart Monitor API Server")
    print("  URL: http://127.0.0.1:%d" % port)
    print("  架构: GitHub trigger.json 轮询触发")
    print("  Token: 在前端输入 GitHub Token（自动保存到本地）")
    print("  轮询间隔: %d 秒" % POLL_INTERVAL)
    print("=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()