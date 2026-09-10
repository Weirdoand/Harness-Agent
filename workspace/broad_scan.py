import os, collections

roots = [r'H:\AI Files\AI', r'H:\AI Files\CoreAI', r'H:\AI Files\learn-claude-code', r'H:\AI Files\LLMUnity']
skip_dirs = {'.git', '__pycache__', '.pytest_cache', '.venv', 'venv', 'node_modules', 'dist', 'build', '.mypy_cache', '.ruff_cache', '.tox', '.compression_archive', '.memory'}

stats = collections.Counter()   # indent width -> count of files using it predominantly
file_report = []
for root in roots:
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fn in files:
            if not fn.endswith('.py'):
                continue
            p = os.path.join(dirpath, fn)
            try:
                size = os.path.getsize(p)
                if size > 2_000_000:
                    continue
                with open(p, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
            except Exception:
                continue
            widths = collections.Counter()
            for ln in lines:
                s = ln.rstrip('\n')
                if not s.strip():
                    continue
                lead = s[:len(s) - len(s.lstrip(' \t'))]
                if '\t' in lead:
                    widths['TAB'] += 1
                elif lead:
                    widths[len(lead)] += 1
            # dominant indent unit
            if not widths:
                continue
            # the smallest positive width often = unit
            pos = sorted(w for w in widths if isinstance(w, int) and w > 0)
            if not pos:
                unit = 'TAB'
            else:
                unit = pos[0]
            stats[unit] += 1
            if unit != 4:
                file_report.append((p, unit, dict(widths)))

print('按“最小缩进单位”统计的 .py 文件数:')
for u, c in sorted(stats.items(), key=lambda x: str(x[0])):
    print(f'  单位={u}格 -> {c} 个文件')

print()
print('== 缩进单位 != 4 的文件明细 ==')
for p, unit, widths in sorted(file_report):
    info = ", ".join(f"{w}格x{c}" for w, c in sorted(widths.items(), key=lambda x: str(x[0])))
    print(f'{p}\n    单位={unit}  分布: {info}')
