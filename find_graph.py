data = open(r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend\browser\asin_monitor.py', 'rb').read()
start_pos = data.find(b'r"""', data.find(b'js_bundle = r')) + 4
end_pos = data.find(b'return JSON.stringify(result);', start_pos)
js_bytes = data[start_pos:end_pos]
js_str = js_bytes.decode('utf-8')
lines = js_str.split('\n')
print('Total lines:', len(lines))
for i, line in enumerate(lines, 1):
    if '@graph' in line or '@type' in line:
        print('Line {}: {}'.format(i, repr(line[:150])))