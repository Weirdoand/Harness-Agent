import re, pathlib
for p in ["workspace/notesapi/auth.py"]:
    txt = pathlib.Path(p).read_text(encoding="utf-8")
    print("=====", p, len(txt.splitlines()), "lines")
    for m in re.finditer(r"^(DEFAULT_\w+|_?\w+_ALGO\w*|TOKEN\w*)\s*=.*$", txt, re.M):
        print("CONST:", m.group(0))
    for m in re.finditer(r"^def .*?(?=:\s*\n)", txt, re.M | re.S):
        pass
    # print def signatures (possibly multi-line)
    for m in re.finditer(r"^def ([\s\S]*?)\)\s*(->\s*[^:]+)?:", txt, re.M):
        sig = " ".join(m.group(1).split())
        print("DEF:", sig, (m.group(2) or "").strip())
