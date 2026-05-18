import re
with open(r"C:\Users\OPENPC\.openclaw\workspace\_body_result.txt","rb") as f:
    raw = f.read()
# B0 + 8-10位
matches = re.findall(b"B0[A-Z0-9]{8,10}", raw)
print(f"B0[A-Z0-9]{{8,10}} 匹配: {len(matches)}")
unique = list(dict.fromkeys([m.decode() for m in matches]))
print(f"唯一 ({len(unique)}):")
for a in unique:
    print(f"  {a}")
