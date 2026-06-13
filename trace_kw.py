#!/usr/bin/env python3
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

traffic_text = "主要流量词\n收起\n\t流量词\t流量占比\t流量词类型\t自然排名\t广告排名\n\t\n\t\namazon\n亚马逊\n\t\n\t\n14.50%\n主要流量词\n\n\t\n自然搜索词\n\t\n\t\n37\n第1页,37/48\n昨日16:47排名\n\t\n\t\n前3页无排名\n\n\n\t\ncotton rounds\n棉轮\n\t\n\t\n9.71%\n主要流量词\n转化优质词\n\n\t\n自然搜索词\nSP广告词\nAC推荐词\n\n\t\n4\n第1页,4/61\n昨日21:24排名\n\t\n\t\n1\n第1页,1/64\n06月05日排名\n\n\n\t\nqtips\n技巧\n\t\n\t\n9.52%\n\n\t\n自然搜索词\n\n\t\n\t\n22\n第1页,22/60\n2天前03:25排名\n\t\n\t\n前3页无排名\n\n\n\t\nmakeup\n化妆\n\t\n\t\n8.78%\n\n\t\n自然搜索词\n\n\t\n\t\n59\n第1页,59/67\n昨日15:41排名\n\t\n\t\n前3页无排名\n点击查看全部流量词"

def _extract_kw(text, utf8_bytes, pct_char_pos):
    pct_byte = len(text[:pct_char_pos].encode('utf-8'))

    # Strategy: find the newline that is closest to % while still being
    # at the start of a line containing an ASCII word.
    # Pattern near %: ...CJC\n\t\n\t\n14.50%
    # So scan backward from % for:  \n (followed by non-ASCII at first byte) = blank line
    # Or: \n followed by ASCII = keyword line
    # We want the \n followed by ASCII that appears AFTER the last \n followed by non-ASCII

    best_newline_byte = None

    # Scan backward from % for the first newline followed by an ASCII letter.
    # This is the keyword line closest to the % (the immediate preceding line).
    j = pct_byte - 1  # start from byte before '%'
    last_valid_newline = None

    while j >= 0:
        b = utf8_bytes[j]
        if b == 0x0A:  # newline
            # Is the byte after this newline an ASCII letter?
            if j + 1 < pct_byte:
                nb = utf8_bytes[j + 1]
                if (0x61 <= nb <= 0x7A) or (0x41 <= nb <= 0x5A):
                    last_valid_newline = j
                    break  # Found the first (closest to %) valid newline - STOP
        j -= 1

    if last_valid_newline is None:
        return ''

    # Now collect the ASCII word(s) starting from last_valid_newline+1
    kw_chars = []
    k = last_valid_newline + 1
    while k < pct_byte:
        kb = utf8_bytes[k]
        if (0x61 <= kb <= 0x7A) or (0x41 <= kb <= 0x5A) or kb == 0x20:
            kw_chars.append(kb)
            k += 1
        else:
            break

    kw_bytes = bytes(kw_chars).rstrip()
    return kw_bytes.decode('utf-8', errors='replace')

utf8_traffic = traffic_text.encode('utf-8')
pct_positions = [(m.start(), m.group()) for m in re.finditer(r'\d+\.\d+%', traffic_text)]
print(f"Found {len(pct_positions)} pct positions\n")

for i, (pct_pos, pct) in enumerate(pct_positions):
    kw = _extract_kw(traffic_text, utf8_traffic, pct_pos)
    print(f"[{i}] pct at char {pct_pos}: kw={repr(kw)}")