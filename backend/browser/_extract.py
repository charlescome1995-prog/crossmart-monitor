"""直接从_raw文件提取"""
import re
with open(r"C:\Users\OPENPC\.openclaw\workspace\_body_result.txt","r",encoding="utf-8") as f:
    raw = f.read()

# 直接提取所有B0开头的
asins = re.findall(r"B0[A-Z0-9]{9,10}", raw)
print(f"总数: {len(asins)}")
unique = list(dict.fromkeys(asins))
print(f"唯一 ({len(unique)}):")
for a in unique:
    pos = raw.find(a)
    context = raw[max(0,pos-30):pos+50].replace("\n"," ")[:80]
    print(f"  {a} ...{context}")

# 也看看_table_data.txt的ASIN
with open(r"C:\Users\OPENPC\.openclaw\workspace\_table_data.txt","r",encoding="utf-8") as f:
    tbl = f.read()
asins2 = re.findall(r"B0[A-Z0-9]{9,10}", tbl)
print(f"\n表格ASIN ({len(asins2)}):")
for a in asins2:
    print(f"  {a}")
