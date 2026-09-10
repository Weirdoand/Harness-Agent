import os, collections

root = r'H:\AI Files\Harness-Agent'
skip_dirs = {'.git', '__pycache__', '.pytest_cache', '.compression_archive', '.memory', 'skills', 'node_modules', 'workspace'}

print("=" * 100)
for dirpath, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for fn in sorted(files):
        if fn.endswith(('.py', '.txt', '.md', '.json', '.yaml', '.yml', '.ini', '.cfg')):
            p = os.path.join(dirpath, fn)
            try:
                with open(p, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
            except Exception as e:
                print(p, 'ERR', e)
                continue
            widths = collections.Counter()
            tab_lines = 0
            for ln in lines:
                s = ln.rstrip('\n')
                if not s.strip() or s.strip().startswith('#'):
                    continue
                lead = s[:len(s) - len(s.lstrip(' \t'))]
                if '\t' in lead:
                    tab_lines += 1
                else:
                    w = len(lead)
                    if w > 0:
                        widths[w] += 1
            if widths or tab_lines:
                total_indented = sum(widths.values()) + tab_lines
                info = ", ".join(f"{w}格x{c}" for w, c in sorted(widths.items()))
                flag = "  <== 含非4倍缩进" if any(w % 4 != 0 for w in widths) else ""
                print(f"{p}   [tab行={tab_lines}] 缩进行={total_indented} 缩进分布: {info}{flag}")
