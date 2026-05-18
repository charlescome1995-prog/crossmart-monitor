import re
with open(r"C:\Users\OPENPC\.openclaw\workspace\_body_result.txt","r",encoding="utf-8") as f:
    text = f.read()
# raw match
asins = re.findall(r"B0[A-Z0-9]{9,10}", text)
print(f"直接match: {len(asins)}")
if asins:
    print(asins[:15])
# 试试更宽松的
asins2 = re.findall(r"B[A-Z0-9]{9,10}", text)
print(f"宽松match: {len(asins2)}")
if asins2:
    print(asins2[:15])
# 看文件内容包含B0吗
if "B0" in text:
    print("文件包含B0")
    print(text[text.index("B0"):text.index("B0")+15])
else:
    print("文件不包含B0")
    print("前100字符:", repr(text[:100]))
