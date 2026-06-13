path = r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend\browser\asin_monitor.py"
with open(path, 'rb') as f:
    data = f.read()

# Pattern found: raw = re.sub(r'<[^>]*>', '', td)\r\n            lines = [l.strip() for l in raw.split('\\n') if l.strip()]
# We need to insert Vue template stripping between these two lines
old = b"raw = re.sub(r'<[^>]*>', '', td)\r\n            lines = [l.strip() for l in raw.split('\\n') if l.strip()]"
new = b"raw = re.sub(r'<[^>]*>', '', td)\r\n            raw = re.sub(r'\\{\\{[^}]+\\}\\}', '', raw)\r\n            lines = [l.strip() for l in raw.split('\\n') if l.strip()]"

if old in data:
    data = data.replace(old, new)
    print("Vue template stripping added")
else:
    print("Pattern not found")
    idx = data.find(b"raw = re.sub(r'<[^>]*>', '', td)")
    print(f"Context: {repr(data[idx:idx+100])}")

with open(path, 'wb') as f:
    f.write(data)
print("Done")