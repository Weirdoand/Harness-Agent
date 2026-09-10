# -*- coding: utf-8 -*-
import io, os, re

roots = [r'H:\AI Files\Harness-Agent', r'H:\AI Files\learn-claude-code']
md_pat = re.compile(r'^( *)-\s')
rows = []
for root in roots:
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in ('.git', '__pycache__', '.pytest_cache',
                  '.compression_archive', '.memory', 'skills')]
        for fn in fns:
            if not (fn.endswith('.md') or fn.endswith('.markdown')):
                continue
            p = os.path.join(dp, fn)
            cnt = {}
            try:
                ls = io.open(p, encoding='utf-8', errors='replace').read().splitlines()
            except Exception:
                continue
            for ln in ls:
                m = md_pat.match(ln)
                if m:
                    n = len(m.group(1))
                    cnt[n] = cnt.get(n, 0) + 1
            if cnt:
                rows.append((p, cnt))
for p, cnt in sorted(rows, key=lambda r: r[0]):
    c3 = cnt.get(3, 0); c4 = cnt.get(4, 0)
    mark = '  <<< 3格与4格都有' if (c3 and c4) else ''
    print('%s %s%s' % (p, dict(sorted(cnt.items())), mark))
