"""直接从二进制中提取"""
import re
with open(r"C:\Users\OPENPC\.openclaw\workspace\_body_result.txt","rb") as f:
    raw = f.read()

# 转成字符串，但保留所有字符
text = raw.decode("utf-8", errors="replace")
# 用更宽松的方式找
asins = re.findall(r"B0[A-Z0-9]{9,10}", text)
print(f"直接findall: {len(asins)}")
# 按字节级找
import re as re2
byte_asins = re2.findall(b"B0[A-Z0-9]{9,10}", raw)
print(f"字节级findall: {len(byte_asins)}")
if byte_asins:
    unique = list(dict.fromkeys([b.decode() for b in byte_asins]))
    print(f"唯一 ({len(unique)}):")
    for a in unique:
        print(f"  {a}")
