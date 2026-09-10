# -*- coding: utf-8 -*-
import io

def show(path, a, b, tag):
    ls = io.open(path, encoding='utf-8').read().splitlines()
    out = ['#### %s (%s) 行%d~%d' % (tag, path, a + 1, b + 1)]
    for i in range(a - 1, min(b, len(ls))):
        ln = ls[i]
        lead = ln[:len(ln) - len(ln.lstrip(' '))]
        out.append('%4d | %-3s | %s' % (i + 1, repr(lead), ln))
    return out

res = []
res += show(r'H:\AI Files\learn-claude-code\docs\zh\s12-worktree-task-isolation.md', 55, 80, 's12 zh')
res += show(r'H:\AI Files\learn-claude-code\docs\zh\s06-context-compact.md', 18, 40, 's06 zh')
res += show(r'H:\AI Files\learn-claude-code\web\src\app\globals.css', 40, 50, 'globals.css 注释横幅')
res += show(r'H:\AI Files\LLMUnity\LICENSE.md', 3, 10, 'LLMUnity LICENSE(第三方,对照)')
io.open(r'H:\AI Files\Harness-Agent\workspace\raw.txt', 'w', encoding='utf-8').write('\n'.join(res))
print('ok')
