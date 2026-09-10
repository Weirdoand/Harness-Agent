# -*- coding: utf-8 -*-
import os, collections, io

p = r'H:\AI Files\Harness-Agent\需求文档\Memory需求文档.md'

# detect encoding via BOM / try several
for enc in ['utf-8-sig', 'utf-8', 'utf-16', 'gbk', 'utf-8-sig']:
    try:
        with io.open(p, encoding=enc, errors='strict') as f:
            first = f.readline()
        print('encoding ok:', enc, repr(first[:60]))
        break
    except Exception as e:
        print('enc fail:', enc, e)

with io.open(p, encoding='utf-8-sig', errors='replace') as f:
    for i, ln in enumerate(f, 1):
        s = ln.rstrip('\n')
        if not s.strip():
            continue
        lead = s[:len(s) - len(s.lstrip(' \t'))]
        if lead:
            print(i, len(lead), repr(s[:60]))
