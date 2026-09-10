# -*- coding: utf-8 -*-
import io
t = io.open('out_indent_scan.txt', encoding='utf-8').read()
targets = ['code-review\\SKILL.md', 'Memory需求文档.md', 's06-context-compact.md',
           's12-worktree-task-isolation.md', 'cron_scheduler', 'globals.css']
lines = t.splitlines()
res = []
for i, l in enumerate(lines):
    if l.startswith('FILE:') and any(x in l for x in targets):
        j = i
        while j < len(lines) and j < i + 40:
            res.append(lines[j]); j += 1
        res.append('-' * 30)
io.open('sel.txt', 'w', encoding='utf-8').write('\n'.join(res))
print('ok lines=%d' % len(res))
