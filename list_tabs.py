import urllib.request, json
req = urllib.request.urlopen('http://127.0.0.1:9225/json', timeout=5)
tabs = json.loads(req.read())
print('Total:', len(tabs), 'tabs')
for i, t in enumerate(tabs):
    title = t.get("title","")[:50]
    url = t.get("url","")[:70]
    print(f'[{i}] {title} | {url}')