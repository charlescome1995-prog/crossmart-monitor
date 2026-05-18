import sys, os, json, time, threading
sys.path.insert(0, r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend')
os.environ["CDP_PORT"] = "9225"

asins = ["B09V7Z4TJG"]
print("Testing scrape with %s" % asins)

# 设置Edge
import urllib.request
try:
    r = urllib.request.urlopen("http://127.0.0.1:9225/json", timeout=3)
    tabs = json.loads(r.read())
    print("Edge OK: %d tabs" % len(tabs))
except Exception as e:
    print("Edge not ready: %s" % e)
    import subprocess
    exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    subprocess.Popen([exe, "--remote-debugging-port=9225", "--remote-allow-origins=*", "--no-first-run", "--no-default-browser-check", "--new-window", "about:blank"])
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            r = urllib.request.urlopen("http://127.0.0.1:9225/json", timeout=3)
            json.loads(r.read())
            print("Edge started manually")
            break
        except:
            time.sleep(2)
    else:
        print("Edge start failed")

# 跑抓取
from browser.asin_monitor import check_asin

for asin in asins:
    asin = asin.strip()
    if not asin:
        continue
    print("\n=== Scraping %s ===" % asin)
    try:
        result = check_asin(asin)
        print("Result: asin=%s has_changes=%s" % (result.get("asin","?"), result.get("has_changes","?")))
    except Exception as e:
        import traceback
        print("FAILED: %s" % e)
        traceback.print_exc()

# 同步到前端
print("\n=== Syncing to frontend ===")
import subprocess
r = subprocess.run([sys.executable, r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend\sync_to_frontend.py'], 
                   cwd=r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend',
                   capture_output=True, text=True, timeout=60)
print("stdout:", r.stdout)
print("stderr:", r.stderr)

print("\nDone!")
