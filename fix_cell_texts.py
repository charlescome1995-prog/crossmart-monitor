"""Fix the cell_texts.append split issue in asin_monitor.py using binary write"""
path = r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend\browser\asin_monitor.py"
with open(path, 'rb') as f:
    data = f.read()

# The broken pattern: cell_texts.append('  <CRLF>  '.join(lines))
# Replaced with: cell_texts.append('\r\n'.join(lines))
# We want: cell_texts.append('\\n'.join(lines))
broken = b"cell_texts.append('\r\n'.join(lines))"
fixed = b"cell_texts.append('\\n'.join(lines))"

if broken in data:
    data = data.replace(broken, fixed)
    with open(path, 'wb') as f:
        f.write(data)
    print("Fixed!")
else:
    print("Pattern not found")
    # Search nearby
    idx = data.find(b"cell_texts.append")
    print(f"Context: {repr(data[idx-5:idx+60])}")