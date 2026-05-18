"""用insertText填入ASIN"""
import json,urllib.request,websocket,time
tabs=json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json",timeout=3).read())
tab=[t for t in tabs if "reverse" in t.get("url","")][0]
ws_url=tab["webSocketDebuggerUrl"]
ws=websocket.create_connection(ws_url,timeout=10)
mid=0
def cmd(m,p=None):
    global mid;mid+=1
    ws.send(json.dumps({"id":mid,"method":m,"params":p or {}}))
    while True:
        r=json.loads(ws.recv())
        if r.get("id")==mid: return r.get("result",{})

# 先清空+聚焦
cmd("Runtime.evaluate",{"expression":"""
(()=>{
    var inp=document.querySelectorAll('input')[25];
    if(!inp)return;
    inp.focus();
    inp.value='';
    inp.dispatchEvent(new Event('input',{bubbles:true}));
})()
""","returnByValue":True})
time.sleep(0.5)

# 用Input.insertText
cmd("Input.insertText",{"text":"B0DCX7628T"})
time.sleep(1)

# 检查
r=cmd("Runtime.evaluate",{"expression":"document.querySelectorAll('input')[25].value","returnByValue":True})
val=r.get("result",{}).get("value","")
print(f"输入框值: {val}")

# 手动也dispatch一个input事件（保险）
cmd("Runtime.evaluate",{"expression":"""
(()=>{
    var inp=document.querySelectorAll('input')[25];
    if(inp){
        inp.dispatchEvent(new Event('input',{bubbles:true}));
        inp.dispatchEvent(new Event('change',{bubbles:true}));
    }
})()
""","returnByValue":True})

# 点立即查询
cmd("Runtime.evaluate",{"expression":"""
(()=>{
    var btns=document.querySelectorAll('button');
    for(var b of btns){
        if((b.textContent||'').trim().includes('立即查询')){
            b.click();break;
        }
    }
})()
""","returnByValue":True})
print("已点击查询")
time.sleep(10)

# 检查页面
r2=cmd("Runtime.evaluate",{"expression":"'tables:'+document.querySelectorAll('table').length+' body:'+document.body.innerText.length","returnByValue":True})
print(r2.get("result",{}).get("value",""))

# 提取关键词
r3=cmd("Runtime.evaluate",{"expression":"""
(()=>{
    var text=document.body.innerText;
    var lines=text.split(String.fromCharCode(10));
    var words=[];
    for(var i=0;i<lines.length;i++){
        var l=lines[i].trim();
        if(/^[a-z][a-z\\s]{2,25}[a-z]$/i.test(l) && l.length>3){
            words.push(l);
        }
    }
    return words.slice(0,15).join('|');
})()
""","returnByValue":True})
print("找到的关键词:",r3.get("result",{}).get("value",""))

ws.close()
