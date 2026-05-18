with open(r"C:\Users\OPENPC\.openclaw\workspace\_body_result.txt","rb") as f:
    raw = f.read()
print(f"字节[1297:1320]: {raw[1297:1320]}")
print(f"可打印: {[chr(b) if 32<=b<127 else f'\\\\x{b:02x}' for b in raw[1297:1320]]}")
# 尝试字节级匹配
import re
matches = re.findall(b"B0[A-Z0-9]{9,10}", raw)
print(f"\n字节级B0[A-Z0-9]匹配: {len(matches)}")
# 放宽到英文+数字
matches2 = re.findall(b"B0[A-Z0-9a-z]{9,10}", raw)
print(f"放宽(小写): {len(matches2)}")
if matches2:
    for m in matches2[:10]:
        print(f"  {m}")
