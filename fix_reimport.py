"""Fix extract_sprite_plugin_data: remove local 'import re' and add Vue template stripping"""
path = r"C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend\browser\asin_monitor.py"
with open(path, 'rb') as f:
    data = f.read()

# Fix 1: Remove local 'import re' inside the try block (it shadows the module-level re)
# Pattern: b'\r\n    try:\r\n        import re\r\n'
# This is at the start of the traffic keywords section
broken_try_import = b'\r\n    try:\r\n        import re\r\n'
if broken_try_import in data:
    data = data.replace(broken_try_import, b'\r\n    try:\r\n')
    print("Removed local 'import re'")
else:
    print("Local import re pattern not found, searching...")
    idx = data.find(b'import re')
    print(f"Context: {repr(data[idx-30:idx+50])}")

# Fix 2: Add Vue template stripping before the cell_texts processing
# We need to add: raw = re.sub(r'\{\{[^}]+\}\}', '', raw) in the right place
# The pattern for the cell processing loop is:
#   raw = re.sub(r'<[^>]*>', '', td)
#   lines = [l.strip() for l in raw.split('\n') if l.strip()]
# We add Vue stripping between these two lines
vue_fix = b"raw = re.sub(r'<[^>]*>', '', td)\n            raw = re.sub(r'\\{\\{[^}]+\\}\\}', '', raw)\n            lines = [l.strip() for l in raw.split('\\n') if l.strip()]"
if vue_fix in data:
    print("Vue template fix already applied")
else:
    # Try without escaped braces
    vue_fix2 = b"raw = re.sub(r'<[^>]*>', '', td)\n            lines = [l.strip() for l in raw.split('\\n') if l.strip()]"
    vue_fix2_replace = b"raw = re.sub(r'<[^>]*>', '', td)\n            raw = re.sub(r'\\{\\{[^}]+\\}\\}', '', raw)\n            lines = [l.strip() for l in raw.split('\\n') if l.strip()]"
    if vue_fix2 in data:
        data = data.replace(vue_fix2, vue_fix2_replace)
        print("Vue template stripping added")
    else:
        print("Cell processing pattern not found, trying hex search...")
        idx = data.find(b"raw = re.sub(r'<[^>]*>', '', td)")
        print(f"Found at byte {idx}")
        print(f"Context: {repr(data[idx:idx+80])}")

with open(path, 'wb') as f:
    f.write(data)
print("Done")