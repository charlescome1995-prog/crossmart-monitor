import re
with open("_out.html","r",encoding="utf-8") as f:
    h=f.read()
asins=re.findall(r"B0[A-Z0-9]{9}",h)
print(f"ASINs: {asins[:10]}")
btns=re.findall(r"<button[^>]*>([^<]+)",h)
print(f"Buttons: {[b.strip() for b in btns if b.strip()][:10]}")
inps=re.findall(r"input[^>]*placeholder=\"([^\"]+)",h)
print(f"Inputs: {inps[:5]}")
print(f"Has loading: {'loading' in h.lower()}")
print(f"Has batana: {'batana' in h.lower()}")
# 表格
print(f"Body size: {len(h)}")
print(h[1000:2000])
