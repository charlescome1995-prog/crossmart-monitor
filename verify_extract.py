content = open(r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend\browser\asin_monitor.py', 'r', encoding='utf-8').read()
pos = content.find('js_bundle = r')
after_r = content.find('r"""', pos)
start = after_r + 4
end_marker = 'return JSON.stringify(result);'
end = content.find(end_marker, start)
js_content = content[start:end + len(end_marker) + 30]
print('Length:', len(js_content))
print('Last 50 chars:', repr(js_content[-50:]))
# Find where })() is in the content
iife_pos = js_content.find('})()')
print('})() found at pos:', iife_pos)
if iife_pos == -1:
    print('IIFE closing NOT found!')
else:
    print('After })():', repr(js_content[iife_pos+4:iife_pos+10]))