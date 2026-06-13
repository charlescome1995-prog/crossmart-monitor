path = r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend\browser\asin_monitor.py"
with open(path, 'rb') as f:
    data = f.read()
idx = data.find(b'raw = re.sub(r')
chunk = data[idx:idx+120]
print(repr(chunk))