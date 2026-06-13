"""Fix split newlines in asin_monitor.py"""
path = r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend\browser\asin_monitor.py"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

nl = chr(10)  # newline character
content = content.replace(f"raw.split('{nl}')", f"raw.split('\\n')")
content = content.replace(f"click_raw.split('{nl}')", f"click_raw.split('\\n')")
content = content.replace(f"organic_raw.split('{nl}')", f"organic_raw.split('\\n')")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed split newlines")