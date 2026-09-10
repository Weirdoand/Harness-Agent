# -*- coding: utf-8 -*-
import io

def show(path, a, b, tag):
    ls = io.open(path, encoding='utf-8', errors='replace').read().splitlines()
    out = ['#### %s %s 行%d~%d' % (tag, path, a + 1, b + 1)]
    for i in range(a - 1, min(b, len(ls))):
        ln = ls[i]
        lead = ln[:len(ln) - len(ln.lstrip(' '))]
        out.append('%4d | len(前导)=%d %s | %s' % (i + 1, len(lead), repr(lead), ln))
    return out

res = []
res += show(r'H:\AI Files\learn-claude-code\web\src\app\globals.css', 44, 50, 'globals.css')
res += show(r'H:\AI Files\learn-claude-code\web\src\app\globals.css', 487, 494, 'globals.css')
res += show(r'H:\AI Files\LLMUnity\LICENSE.md', 4, 9, 'LLMUnity LICENSE')
res += show(r'H:\AI Files\Harness-Agent\skills\code-review\SKILL.md', 68, 80, 'SKILL.md')
io.open(r'H:\AI Files\Harness-Agent\workspace\raw2.txt', 'w', encoding='utf-8').write('\n'.join(res))
print('ok')
