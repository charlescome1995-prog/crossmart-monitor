"""解析查竞品表格数据，分类挑ASIN"""
import re, json

with open(r"C:\Users\OPENPC\.openclaw\workspace\_table_data.txt", "r", encoding="utf-8") as f:
    text = f.read()

with open(r"C:\Users\OPENPC\.openclaw\workspace\_body_result.txt", "r", encoding="utf-8") as f:
    body = f.read()

# 提取所有ASIN（唯一）
asins_all = re.findall(r"B0[A-Z0-9]{9,10}", body)
unique = list(dict.fromkeys(asins_all))
print(f"全部ASIN ({len(unique)}):")
for a in unique:
    print(f"  {a}")

# 按查竞品表格（_table_data.txt）顺序看排名
lines = text.strip().split("\n")
print(f"\n表格行数: {len(lines)}")
# 从每行提取排名和ASIN
for i, line in enumerate(lines):
    if i == 0: continue  # 表头
    # 找ASIN
    asins_in_line = re.findall(r"B0[A-Z0-9]{9,10}", line)
    if asins_in_line:
        main_asin = asins_in_line[0]
        # 找品牌名（ASIN后面的品牌）
        brand = ""
        m = re.search(r"品牌: (\w+)", line)
        if m:
            brand = m.group(1)
        # 找销量数字
        # 大类BSR可以从单独的统计数据里找
        print(f"  #{i}: {main_asin} {brand}")
