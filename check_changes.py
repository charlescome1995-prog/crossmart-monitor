import json
d=json.load(open(r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\frontend\data\monitor-data.json',encoding='utf-8'))
a=d['asins'][0]
ss=a['snapshots']
print('ASIN:', a['asin'])
for i in range(1,len(ss)):
    p=ss[i-1]['data']; c=ss[i]['data']; t=ss[i]['timestamp']
    items=[]
    if p.get('price')!=c.get('price'): items.append('价格: '+str(p.get('price',''))+' -> '+str(c.get('price','')))
    if p.get('rating')!=c.get('rating'): items.append('评分: '+str(p.get('rating',''))+' -> '+str(c.get('rating','')))
    if p.get('review_count')!=c.get('review_count'): items.append('评论: '+str(p.get('review_count',0))+' -> '+str(c.get('review_count',0)))
    if p.get('bsr')!=c.get('bsr'): 
        b1=p.get('bsr','').split(' in')[0]; b2=c.get('bsr','').split(' in')[0]
        items.append('BSR: '+b1+' -> '+b2)
    if items: print(t[:16]+' | '+', '.join(items))
