#!/usr/bin/env python3
import re, sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend\browser\asin_monitor.py', encoding='utf-8') as f:
    content = f.read()
print('file len:', len(content))
for m in re.finditer(r'TYPE_WORDS', content):
    print(f'TYPE_WORDS at char {m.start()}, line ~{content[:m.start()].count(chr(10))}')
for m in re.finditer(r'seller\s*=\s*re\.search', content):
    print(f'seller search at char {m.start()}, line ~{content[:m.start()].count(chr(10))}')
for m in re.finditer(r'sc\s*=\s*re\.search', content):
    print(f'sc search at char {m.start()}, line ~{content[:m.start()].count(chr(10))}')
for m in re.finditer(r'brand\s*=\s*re\.search', content):
    print(f'brand search at char {m.start()}, line ~{content[:m.start()].count(chr(10))}')