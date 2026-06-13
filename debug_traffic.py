#!/usr/bin/env python3
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

traffic_text = "主要流量词\n收起\n\t流量词\t流量占比\t流量词类型\t自然排名\t广告排名\n\t\n\t\namazon\n亚马逊\n\t\n\t\n14.50%\n主要流量词\n\n\t\n自然搜索词\n\t\n\t\n37\n第1页,37/48\n昨日16:47排名\n\t\n\t\n前3页无排名\n\n\n\t\ncotton rounds\n棉轮\n\t\n\t\n9.71%\n主要流量词\n转化优质词\n\n\t\n自然搜索词\nSP广告词\nAC推荐词\n\n\t\n4\n第1页,4/61\n昨日21:24排名\n\t\n\t\n1\n第1页,1/64\n06月05日排名\n\n\n\t\nqtips\n技巧\n\t\n\t\n9.52%\n\n\t\n自然搜索词\n\n\t\n\t\n22\n第1页,22/60\n2天前03:25排名\n\t\n\t\n前3页无排名\n\n\n\t\nmakeup\n化妆\n\t\n\t\n8.78%\n\n\t\n自然搜索词\n\n\t\n\t\n59\n第1页,59/67\n昨日15:41排名\n\t\n\t\n前3页无排名\n点击查看全部流量词"

def _extract_kw(text, utf8_bytes, pct_char_pos):
    pct_byte = len(text[:pct_char_pos].encode('utf-8'))
    j = pct_byte - 1
    while j >= 0:
        b = utf8_bytes[j]
        is_ascii = (0x61 <= b <= 0x7A) or (0x41 <= b <= 0x5A)
        is_utf8_cont = (0x80 <= b <= 0xBF)
        is_utf8_lead = (0xE4 <= b <= 0xEF) or (0xC0 <= b <= 0xDF)
        if is_ascii:
            break
        if is_utf8_lead:
            if (0xE4 <= b <= 0xEF):
                j -= 4  # skip past this 3-byte char + find prev char start
            else:
                j -= 3  # skip past this 2-byte char + find prev char start
            continue
        if is_utf8_cont:
            j -= 1
            continue
        # Delimiter bytes (newline, tab, space, etc.): skip and continue
        j -= 1
        continue
    if j < 0:
        return ''
    b = utf8_bytes[j]
    is_ascii = (0x61 <= b <= 0x7A) or (0x41 <= b <= 0x5A)
    if not is_ascii:
        return ''
    kw_start = j
    while j >= 0:
        b2 = utf8_bytes[j]
        if (0x61 <= b2 <= 0x7A) or (0x41 <= b2 <= 0x5A):
            kw_start = j
            j -= 1
            continue
        elif b2 == 0x20:
            break  # space ends the word
        else:
            break
    kw = utf8_bytes[kw_start:pct_byte].decode('utf-8', errors='replace').strip()
    return kw

utf8_traffic = traffic_text.encode('utf-8')
pct_positions = [(m.start(), m.group()) for m in re.finditer(r'\d+\.\d+%', traffic_text)]
print(f"Found {len(pct_positions)} pct positions")
for i, (pct_pos, pct) in enumerate(pct_positions):
    result = _extract_kw(traffic_text, utf8_traffic, pct_pos)
    pct_byte = len(traffic_text[:pct_pos].encode('utf-8'))
    print(f"  [{i}] pct at char {pct_pos} (byte {pct_byte}): kw={repr(result)}")
    # Show surrounding bytes
    seg = utf8_traffic[max(0,pct_byte-25):pct_byte]
    print(f"      bytes {max(0,pct_byte-25)}:{pct_byte} = {seg.hex()}")
    print(f"      = {repr(seg.decode('utf-8', errors='replace'))}")