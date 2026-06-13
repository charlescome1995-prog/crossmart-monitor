# Dump js_content lines 1-50
content = open(r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend\browser\asin_monitor.py', 'r', encoding='utf-8').read()
start = content.find('js_bundle = r') + 16
end = content.find('return JSON.stringify(result);', start) + len('return JSON.stringify(result);')
js = content[start:end]
lines = js.split('\n')
with open(r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\js_dump.js', 'w', encoding='utf-8') as f:
    f.write(js)
print('Dumped', len(js), 'chars,', len(lines), 'lines')