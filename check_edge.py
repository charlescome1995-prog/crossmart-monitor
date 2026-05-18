import urllib.request, json
try:
    req = urllib.request.urlopen('http://127.0.0.1:9222/json', timeout=3)
    tabs = json.loads(req.read())
    print('Edge已在运行, %d个标签页' % len(tabs))
    for t in tabs[:3]:
        print('  %s | %s' % (t.get('title','?')[:60], t.get('url','?')[:80]))
except Exception as e:
    print('Edge未运行: %s' % e)
