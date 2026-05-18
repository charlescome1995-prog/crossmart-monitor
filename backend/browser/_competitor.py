"""查竞品完整版"""
import json,urllib.request,websocket,time,re
tabs=json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json",timeout=3).read())
tab=[t for t in tabs if "google" in t.get("url","") or "about:blank" in t.get("url","")]
if not tab: tab=tabs[:1]
tab=tab[0]
ws_url=tab["webSocketDebuggerUrl"]
ws=websocket.create_connection(ws_url,timeout=10)
mid=0
def cmd(m,p=None):
    global mid;mid+=1
    ws.send(json.dumps({"id":mid,"method":m,"params":p or {}}))
    while True:
        r=json.loads(ws.recv())
        if r.get("id")==mid: return r.get("result",{})

# 开新标签页 (不`Page.navigate`)
r=cmd("Target.createTarget",{"url":"https://www.sellersprite.com/v3/competitor-lookup"})
time.sleep(5)
tabs=json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json",timeout=3).read())
tab=[t for t in tabs if "competitor-lookup" in t.get("url","")]
if tab:
    ws.close()
    ws=websocket.create_connection(tab[0]["webSocketDebuggerUrl"],timeout=10)
    time.sleep(5)
    
    # 输入
    cmd("Input.insertText",{"text":"batana oil"})
    time.sleep(1)
    cmd("Runtime.evaluate",{"expression":"""
    (()=>{
        var inp=document.activeElement;
        if(inp&&inp.tagName=='INPUT'){
            inp.dispatchEvent(new Event('input',{bubbles:true}));
            inp.dispatchEvent(new Event('change',{bubbles:true}));
        }
    })()
    ""","returnByValue":True})
    time.sleep(1)
    
    # 点按钮
    cmd("Runtime.evaluate",{"expression":"""
    (()=>{
        for(var b of document.querySelectorAll('button')){
            var t=(b.textContent||'').trim();
            if(t.includes('查询')){b.click();return 'clicked '+t;}
        }
        return Array.from(document.querySelectorAll('button')).slice(0,5).map(b=>(b.textContent||'').trim()).filter(Boolean).join('|');
    })()
    ""","returnByValue":True})
    time.sleep(10)
    
    # 拿文本——用innerHTML存为文件（避免编码问题）
    r2=cmd("Runtime.evaluate",{"expression":"document.body.innerHTML.substring(0,50000)","returnByValue":True})
    html=r2.get("result",{}).get("value","")
    if html:
        print(f"HTML size: {len(html)}")
        # 保存文件避免编码
        with open("_out.html","w",encoding="utf-8") as f:
            f.write(html)
        asins=list(set(re.findall(r'B0[A-Z0-9]{9}',html)))
        print(f"\nASINs: {asins}")

ws.close()
