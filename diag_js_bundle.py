#!/usr/bin/env python3
import sys, os
_backend = r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend"
sys.path.insert(0, _backend)

with open(os.path.join(_backend, "browser", "asin_monitor.py"), "r", encoding="utf-8") as f:
    content = f.read()

start = content.find('js_bundle = r"""')
end = content.find('return JSON.stringify(result);', start) + len('return JSON.stringify(result);')
snippet = content[start:end]
print("js_bundle length:", len(snippet))
print("First 500 chars:")
print(snippet[:500])
print("...")
print("Last 200 chars:")
print(snippet[-200:])