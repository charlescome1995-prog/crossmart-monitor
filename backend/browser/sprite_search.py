import sys,os,time,json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from cdp_bridge import CDPBrowser

b=CDPBrowser()
b.connect_tab()

# 你要在Edge上看到以下操作
print("="*60)
print("【你将在Edge上看到】")
print("1. 打开出单词反查页面")
print("2. 输入ASIN → 点查询")
print("3. 数据出来后导出")
print("4. 跳转到查竞品")
print("="*60)

# ─── Step 1: 出单词反查 ───
b.navigate("https://www.sellersprite.com/v2/aba/reverse/search", wait_min=3, wait_max=5)
time.sleep(3)

# 填ASIN到正确输入框 (input[25])
b.eval("""
(()=>{
    var inp=document.querySelectorAll('input')[25];
    if(!inp)return;
    inp.focus();
    inp.scrollIntoView({behavior:'smooth',block:'center'});
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(inp,'B0DCX7628T');
    inp.dispatchEvent(new Event('input',{bubbles:true}));
    inp.dispatchEvent(new Event('change',{bubbles:true}));
})()
""")
time.sleep(1)

# 点立即查询
b.eval("""
(()=>{
    var btns=document.querySelectorAll('button');
    for(var b of btns){
        if((b.textContent||'').trim().includes('立即查询')){b.click();break;}
    }
})()
""")
print("✅ Step 1 完成：出单词反查已提交查询")
print("   请你在Edge上看结果表格是否显示")
print("   如果显示了，请告诉我关键词的第一个是什么")
print("   我在等待你的回复...")
