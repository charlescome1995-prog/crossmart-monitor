import json
content = open(r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend\browser\asin_monitor.py', 'r', encoding='utf-8').read()
start = content.find('js_bundle = r') + 16
end = content.find('return JSON.stringify(result);', start) + len('return JSON.stringify(result);')
js = content[start:end]
wrapped = '(function(){{ try {{ return JSON.stringify(eval({j})); }} catch(e) {{ return JSON.stringify({{error: e.message}}); }} }})()'.format(j=json.dumps(js))
pos_in_wrapped = wrapped.find(json.dumps(js))
print('json.dumps(js) starts at char', pos_in_wrapped)
print('error col 10573 -> js pos approx', 10573 - pos_in_wrapped)
print('wrapped total len:', len(wrapped))
# raw position in js_content
raw_pos = 10573 - pos_in_wrapped
print('js around raw_pos', raw_pos, ':', repr(js[raw_pos-10:raw_pos+10]))
# Count quotes that were escaped
num_quotes = js[:raw_pos].count("'")
print('quotes before raw_pos:', num_quotes)
# The escape sequences in JSON: each ' becomes \'
# So actual position in js_content is earlier
adjusted = raw_pos - num_quotes
print('adjusted js pos:', adjusted)
print('js[adjusted-10:adjusted+10]:', repr(js[adjusted-10:adjusted+10]))
# Find the problematic line
lines_above = js[:adjusted].count('\n')
print('problem is around line', lines_above + 1)
line_start = js.rfind('\n', 0, adjusted) + 1
line_end = js.find('\n', adjusted)
print('problematic line:', js[line_start:line_end])