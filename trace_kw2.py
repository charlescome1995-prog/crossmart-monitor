s = 'amazon亚马逊14.50%'
b = s.encode('utf-8')
for i in range(len(s)):
    byte_start = len(s[:i].encode('utf-8'))
    print(f'char {i:2d} byte {byte_start:2d}: {repr(s[i]):6s} = 0x{b[byte_start]:02X}')

print()
pct_pos = s.find('14.50%')
pct_byte = len(s[:pct_pos].encode('utf-8'))
print(f"'14.50%' at char {pct_pos}, byte {pct_byte}")
print(f"Bytes before %: {b[pct_byte-5:pct_byte].hex()}")
print(f"Chars before %: {repr(s[pct_pos-5:pct_pos])}")

# Trace the scan
j = pct_byte - 1
print(f"\nScanning backward from byte {j}:")
steps = 0
while j >= 0 and steps < 15:
    bv = b[j]
    c = chr(bv) if bv < 0x80 else '?'
    print(f"  j={j} byte=0x{bv:02X} '{c}'", end='')
    if (0x61 <= bv <= 0x7A) or (0x41 <= bv <= 0x5A):
        print(" ← ASCII LETTER")
        break
    if (0x80 <= bv <= 0xBF):
        print(" ← CJK cont, backing up...")
        k = j - 1
        while k >= 0 and (0x80 <= b[k] <= 0xBF):
            k -= 1
        if k >= 0:
            lead = b[k]
            print(f"    lead=0x{lead:02X}", end='')
            if (0xE4 <= lead <= 0xEF):
                k -= 3
                print(f" (3-byte), skip to {k}")
            elif (0xC0 <= lead <= 0xDF):
                k -= 2
                print(f" (2-byte), skip to {k}")
            else:
                print(f" (other), skip to {k}")
        j = k
        steps += 1
        continue
    print(" ← other, skip")
    j -= 1
    steps += 1