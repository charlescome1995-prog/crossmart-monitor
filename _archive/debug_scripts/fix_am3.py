#!/usr/bin/env python3
"""Fix extract_sprite_plugin_data: remove the button click step that's specific
   to search page sidebar (not detail page). Use innerText for newlines.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import py_compile

path = r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend\browser\asin_monitor.py'
with open(path, 'rb') as f:
    d = f.read()
original = len(d)

# Find the click_js block: from "    click_js = r\"\"\"" to "    \"\"\"\n    click_result"
click_start = d.find(b"    click_js = r\"\"\"")
click_end_marker = b'    """\n    click_result = browser.eval(click_js)'
click_end = d.find(click_end_marker, click_start)
if click_end < 0:
    print('ERROR: click_end not found')
    import sys; sys.exit(1)
click_end = click_end + len(b'    """\n')

# The block to remove: from click_start to click_end
removed_block = d[click_start:click_end]
print('Block to remove:')
print(removed_block.decode('utf-8', errors='replace')[:500])
print('---')

# Replacement: just a print + wait statement
replacement = b'''    # \xe5\x95\x86\xe5\x93\x81\xe9\xa1\xb5 seller-sprite \xe5\xb7\xb2\xe8\x87\xaa\xe5\x8a\xa8\xe6\xb3\xa8\xe5\x85\xa5, \xe6\x97\xa0\xe9\x9c\x80\xe7\x82\xb9\xe5\x87\xbb\xe6\x8c\x89\xe9\x92\xae
    print("  [\xe6\x8f\x92\xe4\xbb\xb6] \xe5\x95\x86\xe5\x93\x81\xe9\xa1\xb5 seller-sprite \xe5\xb7\xb2\xe5\x8a\xa0\xe8\xbd\xbd, \xe7\xad\x89\xe5\xbe\x853s...")
    time.sleep(3)  # \xe7\xad\x89\xe5\xbe\x85 overlay \xe5\xae\x8c\xe5\x85\xa8\xe6\xb8\xb2\xe6\x9f\x93
'''

d = d[:click_start] + replacement + d[click_end:]

# Also fix: textContent -> innerText for newlines preservation
old = b"data[ids[i]] = (el.textContent||'').trim();"
new = b"data[ids[i]] = (el.innerText||'').trim();"
if old in d:
    d = d.replace(old, new, 1)
    print('Changed textContent -> innerText')

# Verify the new structure
with open(path, 'wb') as f:
    f.write(d)

print(f'Size: {original} -> {len(d)}')
try:
    py_compile.compile(path, doraise=True)
    print('Syntax OK')
except py_compile.PyCompileError as e:
    print('Syntax error:', e)
    import subprocess
    subprocess.run(['git', '-C', r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor', 'checkout', 'HEAD', '--', 'backend/browser/asin_monitor.py'],
                   capture_output=True, text=True)
    print('Restored from git')