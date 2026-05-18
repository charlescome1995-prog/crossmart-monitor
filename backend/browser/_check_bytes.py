"""检查文件编码"""
with open(r"C:\Users\OPENPC\.openclaw\workspace\_body_result.txt","rb") as f:
    raw = f.read()
# 找B0的位置（字节级）
pos = raw.find(b"B0")
print(f"B0位置: {pos}")
if pos >= 0:
    print(f"B0附近字节: {raw[max(0,pos-5):pos+20]}")
else:
    # 找B
    pos2 = raw.find(b"B")
    print(f"B位置: {pos2}")
    if pos2 >= 0:
        print(f"B附近: {raw[max(0,pos2-5):pos2+20]}")
        # 看看附近有什么
        print(f"B->索引:(B在前面的ASCII)")
        for i in range(max(0,pos2-3), min(len(raw), pos2+20)):
            print(f"  [{i}] {raw[i]:3d} {chr(raw[i]) if 32<=raw[i]<127 else '?'}")
    
print(f"\n文件前200字节:")
print(raw[:200])
