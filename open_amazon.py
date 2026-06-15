import urllib.request, json, websocket, time, sys
sys.stdout.reconfigure(encoding='utf-8')

# Get first tab as bridge
req = urllib.request.urlopen('http://127.0.0.1:9225/json', timeout=5)
tabs = json.loads(req.read())
first_ws = tabs[0]['webSocketDebuggerUrl']

ws = websocket.create_connection(first_ws, timeout=10)
# Create Amazon tab
ws.send(json.dumps({'id':1,'method':'Target.createTarget','params':{'url':'https://www.amazon.com/dp/B09542G9ZN'}}))
time.sleep(3)
ws.close()
print('Amazon tab created')