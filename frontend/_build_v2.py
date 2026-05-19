#!/usr/bin/env python3
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(BASE, 'monitor.html')
DATA = os.path.join(BASE, 'data', 'monitor-data.json')

CSS = open(os.path.join(BASE, '_css.txt'), encoding='utf-8').read()
HTML_PART1 = open(os.path.join(BASE, '_html1.txt'), encoding='utf-8').read()
HTML_PART2 = open(os.path.join(BASE, '_html2.txt'), encoding='utf-8').read()
JS = open(os.path.join(BASE, '_js.txt'), encoding='utf-8').read()

with open(DATA, 'r', encoding='utf-8') as f:
    raw_data = f.read()
safe_data = raw_data.replace('</script>', '<\\/script>')
html = HTML_PART1 + CSS + HTML_PART2.replace('__DATA__', safe_data) + '\n<script>\n' + JS + '\n</script>'
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print('Written:', OUT)
