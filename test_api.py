import urllib.request, json

# 测试直接发请求
body = json.dumps({"asins": ["B09V7Z4TJG"]}).encode("utf-8")
r = urllib.request.urlopen(
    "http://127.0.0.1:8765/api/scrape",
    data=body,
    timeout=5
)
print("Status:", r.status)
print("Response:", r.read().decode()[:200])

# 等几秒检查状态
import time
time.sleep(3)
r2 = urllib.request.urlopen("http://127.0.0.1:8765/api/status", timeout=5)
print("Status after:", json.loads(r2.read()))
