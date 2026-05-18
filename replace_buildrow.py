import re

with open(r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\frontend\monitor.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find the exact buildRow function
start = html.find('function buildRow(item){')
end = html.find('load();', start)
if start > 0 and end > 0:
    end = html.rfind('}', start, end) + 1
    print("Found buildRow from %d to %d" % (start, end))
    
    new_func = '''function buildRow(item){
  var div=document.createElement('div');div.className='asin-row';
  var changed=item.has_changes, chgCount=item.change_count||0;
  var price=item.price||'---', brand=item.brand||'---', rt=item.rating||'---';
  var rc=item.review_count||'---', seller=item.seller||'---';
  var bsr=item.bsr||'', bsrSub=item.bsr_sub_rank||'', bsrCat=item.bsr_sub_category||'';

  // BSR display
  var bsrTop=bsr||'---';
  var bsrSubDisp=bsrSub&&bsrCat ? bsrSub+' '+bsrCat : (bsrSub||'---');
  var pvHtml=price;
  if(item.list_price&&item.price&&item.list_price!==item.price){
    pvHtml+=' <span style="color:#999;text-decoration:line-through">'+item.list_price+'</span>';
  }

  // Image
  var imgURL=item.main_image||'';
  var imgHTML=imgURL ? ('<img src="'+imgURL+'" onerror="this.style.display=\\'none\\'">') : '<div class="plh">\\ud83d\\udcf7</div>';

  // Status column with change timeline
  var stHTML='';
  if(changed){
    stHTML='<div class="bg-c">\\u26a0\\ufe0f \\u53d8\\u5316 '+chgCount+'\\u6b21</div>';
    var clist=item.changes||[];
    var maxShow=3;
    var slice=clist.slice(-maxShow);
    slice.forEach(function(chg, idx){
      var actualIdx=clist.length - (slice.length-idx);
      stHTML+='<div style="margin:4px 0;background:#fff7ed;border-radius:4px;padding:3px 5px;font-size:10px;line-height:1.4;border:1px solid #fed7aa">';
      stHTML+='<div style="color:#9a3412;font-weight:600;font-size:9px">\\u7b2c'+actualIdx+'\\u6b21 '+fmtTime(chg.timestamp)+'</div>';
      chg.items.forEach(function(c){
        var cl=c.direction==='up'?'up':'dn';
        stHTML+='<span class="chg-i '+cl+'">';
        if(c.field==='price') stHTML+='\\ud83d\\udcb0 \\u4ef7\\u683c '+c.from+'\\u2192'+c.to;
        else if(c.field==='rating') stHTML+='\\u2b50 \\u8bc4\\u5206 '+c.from+'\\u2192'+c.to;
        else if(c.field==='review_count') stHTML+='\\ud83d\\udcdd \\u8bc4\\u8bba '+c.from+'\\u2192'+c.to;
        else if(c.field==='bsr') stHTML+='\\ud83d\\udcca BSR '+c.from+'\\u2192'+c.to;
        stHTML+='</span><br>';
      });
      stHTML+='</div>';
    });
    if(clist.length>maxShow){
      stHTML+='<div style="font-size:9px;color:#999;margin-top:2px">\\u8fd8\\u6709 '+(clist.length-maxShow)+' \\u6b21\\u66f4\\u65e9\\u53d8\\u5316</div>';
    }
  }else{
    stHTML='<div class="bg-s">\\u2705 \\u7a33\\u5b9a</div>';
  }
  if(item.last_check){
    stHTML+='<div style="font-size:9px;color:#999;margin-top:4px">\\ud83d\\udd52 '+fmtTime(item.last_check).replace(' ','')+'</div>';
  }
  var times=(item.snapshots||[]).map(function(t){return fmtTime(t)}).join('<br>');
  if(times) stHTML+='<div style="font-size:9px;color:#ccc;margin-top:2px">'+times+'</div>';

  // Metrics grid
  var mg=
    '<span class="ml">\\u54c1\\u724c</span><span class="mv">'+brand+'</span>'+
    '<span class="ml">\\u552e\\u4ef7</span><span class="mv pc">'+pvHtml+'</span>'+
    '<span class="ml">\\u8bc4\\u5206</span><span class="mv rt">'+rt+'</span>'+
    '<span class="ml">\\u8bc4\\u8bba</span><span class="mv">'+rc+'</span><span></span>'+
    '<span class="ml">\\u5927\\u7c7b</span><span class="mv">'+bsrTop+'</span>'+
    '<span class="ml">\\u5c0f\\u7c7b</span><span class="mv">'+bsrSubDisp+'</span>'+
    '<span class="ml">\\u5356\\u5bb6</span><span class="mv">'+seller+'</span>';

  div.innerHTML=
    '<div class="asin-img">'+imgHTML+'</div>'+
    '<div class="asin-body">'+
      '<div class="asin-title"><span class="name"><a href="https://www.amazon.com/dp/'+item.asin+'" target="_blank">'+g(item.title).substring(0,120)+'</a></span><span class="badge">'+item.asin+'</span></div>'+
      '<div class="mt">'+mg+'</div>'+
    '</div>'+
    '<div class="asin-stat">'+stHTML+'</div>';

  return div;
}

function fmtTime(ts){
  if(!ts) return '';
  var d=new Date(ts);
  if(isNaN(d.getTime())) return ts.substring(5,16);
  return ('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2)+' '+('0'+d.getHours()).slice(-2)+':'+('0'+d.getMinutes()).slice(-2);
}'''
    
    html = html[:start] + new_func + html[end:]
    
    with open(r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\frontend\monitor.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Done! Replaced buildRow function.")
else:
    print("Could not find buildRow function. Start=%d, End=%d" % (start, end))
