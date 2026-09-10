# -*- coding: utf-8 -*-
"""检查核心文件的具体上下文 + Harness-Agent 内 .py 缩进分布"""
import io, os, collections

def dump(path, lines, tag):
    out = []
    out.append('#### ' + tag + ' : ' + path)
    for ln in lines:
        out.append(repr(ln))
    return out

res = []

# 1) code-review SKILL.md 上下文 (行60~82)
p = r'H:\AI Files\Harness-Agent\skills\code-review\SKILL.md'
ls = io.open(p, encoding='utf-8').read().splitlines()
res += dump(p, [ls[i] for i in range(59, min(82, len(ls)))], 'code-review SKILL.md 行60~82')

# 2) Memory需求文档.md 行30~45
p = r'H:\AI Files\Harness-Agent\需求文档\Memory需求文档.md'
ls = io.open(p, encoding='utf-8').read().splitlines()
res += dump(p, [ls[i] for i in range(29, min(46, len(ls)))], 'Memory需求文档.md 行30~45')

# 3) Harness-Agent 内所有 .py 的缩进宽度统计
def stat_py(path):
    try:
        ls = io.open(path, encoding='utf-8').read().splitlines()
    except Exception:
        ls = io.open(path, encoding='gbk').read().splitlines()
    c = collections.Counter()
    tabs = 0
    for ln in ls:
        s = ln.strip()
        if not s or s.startswith('#'):
            continue
        lead = ln[:len(ln)-len(ln.lstrip(' \t'))]
        if '\t' in lead:
            tabs += 1
        else:
            c[len(lead)] += 1
    return dict(c), tabs

res.append('#### Harness-Agent 目录下 .py 文件的缩进分布')
for root, dirs, files in os.walk(r'H:\AI Files\Harness-Agent'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__','.pytest_cache','.compression_archive','.memory','skills','node_modules','-p')]
    for fn in files:
        if fn.endswith('.py'):
            pp = os.path.join(root, fn)
            c, tabs = stat_py(pp)
            res.append('%s -> 缩进宽度分布%s, tab行数=%d' % (pp, c, tabs))

io.open('detail.txt', 'w', encoding='utf-8').write('\n'.join(res))
print('ok')
