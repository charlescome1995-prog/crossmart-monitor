content = open(r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend\browser\asin_monitor.py', 'r', encoding='utf-8').read()
pos = content.find('js_bundle = r')
after_r = content.find('r"""', pos)
start = after_r + 4
end_marker = 'return JSON.stringify(result);'
end = content.find(end_marker, start)
print('start:', start, 'end:', end)
print('content[end:end+20]:', repr(content[end:end+20]))
print('end_marker repr:', repr(end_marker))
print('end_marker len:', len(end_marker))
# Try different offsets
for offset in [3, 4, 5, 6]:
    js = content[start:end + len(end_marker) + offset]
    print('offset +{}: len={} last15={}'.format(offset, len(js), repr(js[-15:])))