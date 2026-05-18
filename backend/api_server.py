#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api_server.py - CrossMart Monitor 本地API服务
启动后: http://127.0.0.1:8765
前端点击"立即抓取"时，请求 /api/scrape 触发后台抓取
"""
import sys, os, json, subprocess, threading, time
sys.stdout.reconfigure(encoding='utf-8')
os.environ["CDP_PORT"] = "9225"  # 强制使用用户的默认Edge
from http.server import HTTPServer, BaseHTTPRequestHandler

PROJECT = os.path.dirname(os.path.abspath(__file__))
# 允许跨域
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}

SCRAPE_STATUS = {"running": False, "last_result": None}

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
                "last_result": SCRAPE_STATUS["last_result"]
            })
        else:
            self._send_json({"error": "not found"}, 404)
    
    def do_POST(self):
        if self.path == "/api/scrape":
            self._handle_scrape()
        else:
            self._send_json({"error": "not found"}, 404)
    
    def _handle_scrape(self):
        global SCRAPE_STATUS
        
        if SCRAPE_STATUS["running"]:
            self._send_json({"status": "busy", "message": "正在采集中，请稍候"})
            return
        
        # 读取前端配置的ASIN列表（从localStorage传过来）
        content_len = int(self.headers.get("Content-Length", 0))
        body = b""
        if content_len > 0:
            body = self.rfile.read(content_len)
        
        asins = []
        if body:
            try:
                data = json.loads(body)
                asins = data.get("asins", [])
            except:
                pass
        
        if not asins:
            # 没有传ASIN，用默认
            asins = ["B09V7Z4TJG"]
        
        self._send_json({"status": "ok", "message": "开始采集 %d 个ASIN" % len(asins)})
        
        # 后台执行
        SCRAPE_STATUS["running"] = True
        SCRAPE_STATUS["last_result"] = None
        
        def run_scrape():
            global SCRAPE_STATUS
            try:
                print("[Scrape] 开始采集 %d 个ASIN: %s" % (len(asins), asins[:3]))
                
                # 确保当前目录正确
                os.chdir(PROJECT)
                sys.path.insert(0, PROJECT)
                print("[Scrape] CWD: %s" % os.getcwd())
                
                # 先确认Edge在9225端口
                import urllib.request
                try:
                    r = urllib.request.urlopen("http://127.0.0.1:9225/json", timeout=3)
                    tabs = json.loads(r.read())
                    print("[Scrape] Edge已连接 (%d个标签页)" % len(tabs))
                except:
                    print("[Scrape] Edge不在9225端口，请先启动Edge...")
                    # 尝试自动启动
                    exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
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
                            print("[Scrape] Edge手动启动成功")
                            break
                        except:
                            time.sleep(2)
                    else:
                        print("[Scrape] Edge启动失败")
                        SCRAPE_STATUS["running"] = False
                        SCRAPE_STATUS["last_result"] = {"status": "error", "error": "Edge启动失败"}
                        return
                
                # 逐个抓取
                results = []
                for asin in asins:
                    asin = asin.strip()
                    if not asin:
                        continue
                    print("[Scrape] 抓取 %s..." % asin)
                    try:
                        # 导入asin_monitor
                        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                        from browser.asin_monitor import check_asin
                        result = check_asin(asin)
                        results.append(result)
                    except Exception as e:
                        print("[Scrape] %s 失败: %s" % (asin, e))
                
                # 同步到前端
                print("[Scrape] 同步到前端...")
                try:
                    subprocess.run([
                        sys.executable,
                        os.path.join(PROJECT, "sync_to_frontend.py")
                    ], cwd=PROJECT, capture_output=True, text=True, timeout=60)
                except Exception as e:
                    print("[Scrape] 同步失败: %s" % e)
                
                SCRAPE_STATUS["last_result"] = {
                    "status": "ok",
                    "count": len(results),
                    "asins": [r.get("asin", "?") for r in results],
                }
                print("[Scrape] 采集完成: %d个ASIN" % len(results))
            except Exception as e:
                print("[Scrape] 采集异常: %s" % e)
                SCRAPE_STATUS["last_result"] = {"status": "error", "error": str(e)}
            finally:
                SCRAPE_STATUS["running"] = False
        
        t = threading.Thread(target=run_scrape, daemon=True)
        t.start()

def main():
    port = 8765
    server = HTTPServer(("127.0.0.1", port), ScrapeHandler)
    print("=" * 50)
    print("CrossMart Monitor API Server")
    print("  URL: http://127.0.0.1:%d" % port)
    print("  POST /api/scrape  - 触发抓取")
    print("  GET  /api/status  - 查询状态")
    print("=" * 50)
    print("(需要Edge在9225端口运行)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()
