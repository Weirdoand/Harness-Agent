# -*- coding: utf-8 -*-
"""全盘(本机H:\AI Files)扫描:哪些文本文件的真实缩进是3格/4格/tab, 记录证据到 out_indent_scan.txt"""
import os

OUT = r"H:\AI Files\Harness-Agent\workspace\out_indent_scan.txt"
ROOT = r"H:\AI Files"
SKIP = {'.git','node_modules','__pycache__','.pytest_cache','.compression_archive',
        '.memory','.venv','venv','site-packages','.idea','dist','build'}
EXTS = ('.py','.ts','.tsx','.js','.jsx','.md','.json','.sh','.css','.html','.txt',
        '.c','.h','.go','.java','.yml','.yaml')

def probe(path):
    try:
        raw = open(path, 'rb').read()
    except Exception:
        return None
    text = None
    for enc in ('utf-8','gbk'):
        try:
            text = raw.decode(enc); break
        except Exception:
            continue
    if text is None:
        text = raw.decode('utf-8', 'replace')
    n3 = n4 = ntab = 0
    ex3, ex4, extab = [], [], []
    for i, ln in enumerate(text.splitlines(), 1):
        if not ln.strip():
            continue
        s = ln.lstrip(' \t')
        lead = ln[:len(ln) - len(s)]
        if not lead:
            continue
        if '\t' in lead:
            ntab += 1
            if len(extab) < 4:
                extab.append((i, repr(lead), ln[:60]))
        else:
            L = len(lead)
            if L == 3:
                n3 += 1
                if len(ex3) < 8: ex3.append((i, ln[:80]))
            elif L == 4:
                n4 += 1
                if len(ex4) < 3: ex4.append((i, ln[:80]))
    if n3 == 0 and ntab == 0:
        return None
    return (n3, n4, ntab, ex3, extab)

buf = []
count3 = counttab = 0
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for fn in files:
        if not fn.endswith(EXTS):
            continue
        p = os.path.join(root, fn)
        r = probe(p)
        if r:
            count3 += (1 if r[0] else 0)
            counttab += (1 if r[2] else 0)
            buf.append('FILE: ' + p)
            buf.append('   缩进3格的行数=%d, 4格行数=%d, 含tab缩进的行数=%d' % (r[0], r[1], r[2]))
            for e in r[3]:
                buf.append('     例3格@行%d: %s' % (e[0], e[1]))
            for e in r[4]:
                buf.append('     例tab@行%d: %s %s' % (e[0], e[1], e[2]))

buf.insert(0, '=== 扫描完成: 出现3格或tab的文件共 %d 个 (其中含3格 %d 个, 含tab %d 个) ===' % (len(buf) and count3+counttab or 0, count3, counttab))
with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(buf))
print('written', len(buf))
