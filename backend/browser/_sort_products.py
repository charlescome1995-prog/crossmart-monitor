"""整理竞品列表"""
import json,re
with open("_competitor_data.json","r",encoding="utf-8") as f:
    d = json.load(f)

products = []
seen_parents = set()
for row in d["data"]:
    if len(row) < 5: continue
    rank = row[1].strip() if len(row)>1 else ""
    title = row[2][:100] if len(row)>2 else ""
    full_title = row[3][:100] if len(row)>3 else ""
    sales_text = row[4][:30] if len(row)>4 else ""
    
    # 提取ASIN,Brand
    asin = ""
    brand = ""
    parent_asin = ""
    m = re.search(r"ASIN:\s*(B0[A-Z0-9]{8,10})", row[3])
    if m: asin = m.group(1)
    m2 = re.search(r"品牌:\s*(\w+)", row[3])
    if m2: brand = m2.group(1)
    m3 = re.search(r"畅销父ASIN\s*:\s*(B0[A-Z0-9]{8,10})", row[3])
    if m3: parent_asin = m3.group(1)
    m4 = re.search(r"父ASIN\s*:\s*(B0[A-Z0-9]{8,10})", row[3])
    if m4 and not parent_asin: parent_asin = m4.group(1)
    
    # 销量数字（第一个数字）
    nums = re.findall(r"[\d,]+", sales_text)
    sales = nums[0] if nums else "?"
    
    # 去重：按父ASIN或品牌
    dedup_key = parent_asin or asin or brand
    if dedup_key and dedup_key not in seen_parents:
        seen_parents.add(dedup_key)
        products.append({
            "rank": rank, "asin": asin, "parent_asin": parent_asin,
            "brand": brand, "title": title[:50], "sales": sales, "sales_raw": sales_text
        })

print(f"去重后 {len(products)} 个产品:")
for p in products:
    print(f"  #{p['rank']:>2} {p['asin']:>12} {p['brand']:>15} sales={p['sales']:>6} | {p['title']}")
