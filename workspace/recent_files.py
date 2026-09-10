import os, time

roots = [r'H:\AI Files\AI', r'H:\AI Files\CoreAI', r'H:\AI Files\Harness-Agent', r'H:\AI Files\learn-claude-code', r'H:\AI Files\LLMUnity']
skip_dirs = {'.git', '__pycache__', '.pytest_cache', '.venv', 'venv', 'node_modules', 'dist', 'build', '.mypy_cache', '.ruff_cache', '.tox', '.compression_archive', '.memory'}
exts = ('.py', '.md', '.txt', '.json', '.yaml', '.yml', '.js', '.ts', '.html', '.css')
recent = []
now = time.time()
for root in roots:
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        for fn in files:
            if not fn.endswith(exts):
                continue
            p = os.path.join(dirpath, fn)
            try:
                st = os.stat(p)
            except Exception:
                continue
            if now - st.st_mtime < 60 * 60 * 24 * 20:   # within 20 days
                recent.append((st.st_mtime, p))
recent.sort(reverse=True)
print('近20天修改过的文本/代码文件（按时间倒序）:')
for m, p in recent[:60]:
    print(' ', time.strftime('%Y-%m-%d %H:%M', time.localtime(m)), p)
