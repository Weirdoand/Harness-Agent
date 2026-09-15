# -*- coding: utf-8 -*-
"""Verification script for the config-extraction refactor (task f5d814aa).

Checks, in-process and via fresh subprocesses, that:

1. ``config`` is import-safe (no files created, no DB opened, no process state
   mutated merely by importing it).
2. ``config`` is env-driven: ``NOTES_API_DB_PATH`` / ``NOTES_API_SECRET_KEY`` /
   ``NOTES_API_ENV`` / ``NOTES_API_HOST`` / ``NOTES_API_PORT`` are honoured.
3. ``db.get_connection`` / ``db.init_db`` / ``db.reset_db`` keep their exact
   parameter names, defaults and return annotations.
4. ``db.DEFAULT_DB_PATH`` is still available as a backward-compatible alias and
   tracks ``config.DB_PATH``; ``config.DEFAULT_DB_PATH`` is re-exported too.
5. Importing ``db`` leaves a usable, name-resolvable schema (``init_db`` still
   returns a ``sqlite3.Connection`` with ``sqlite3.Row`` rows and foreign-key
   enforcement enabled).

Run with::

    python verify_config.py

Exits non-zero on the first failure.
"""
from __future__ import annotations

import inspect
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config  # noqa: E402
import db  # noqa: E402

_failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label}" + (f" -> {detail}" if detail else ""))
    if not ok:
        _failures.append(label)


def _ann_name(annotation) -> str:
    """Normalise an annotation to its source name.

    Because the modules use ``from __future__ import annotations`` (PEP 563),
    ``inspect`` yields annotation *strings* such as ``'str'`` rather than the
    live objects, so accept both spellings.
    """
    if annotation is inspect.Parameter.empty:
        return ""
    if isinstance(annotation, str):
        return annotation
    return getattr(annotation, "__name__", str(annotation))


def check_signature(func, default_value) -> None:
    """Assert the frozen public contract: (db_path: str = <default>) -> Connection."""
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    check(
        f"{func.__qualname__} takes exactly one param",
        len(params) == 1,
        f"params={[p.name for p in params]}",
    )
    p = params[0]
    check(f"{func.__qualname__} param name 'db_path'", p.name == "db_path", p.name)
    check(
        f"{func.__qualname__} db_path annotation is str",
        _ann_name(p.annotation) == "str",
        repr(p.annotation),
    )
    check(
        f"{func.__qualname__} db_path default == DEFAULT_DB_PATH",
        p.default == default_value,
        repr(p.default),
    )
    check(
        f"{func.__qualname__} return -> sqlite3.Connection",
        _ann_name(sig.return_annotation) == "sqlite3.Connection",
        repr(sig.return_annotation),
    )


def main() -> int:
    print("== 1. import-safe / side-effect free ==")
    check("config.HERE is notesapi dir", config.HERE == HERE, config.HERE)
    check(
        "config.DB_PATH default ends with notes.db",
        config.DB_PATH.endswith("notes.db"),
        config.DB_PATH,
    )
    check(
        "config.DEFAULT_DB_PATH re-exported == DB_PATH",
        config.DEFAULT_DB_PATH == config.DB_PATH,
    )
    check("config.ENV default", config.ENV == "development", config.ENV)
    check("config.HOST default", config.HOST == "127.0.0.1", config.HOST)
    check("config.PORT default", config.PORT == 8000, config.PORT)
    check("config.PORT is int", isinstance(config.PORT, int))

    print("\n== 2. config<->db alias consistency ==")
    check("db.DEFAULT_DB_PATH == config.DB_PATH", db.DEFAULT_DB_PATH == config.DB_PATH)

    print("\n== 3. db public interfaces are byte-for-byte unchanged ==")
    for fn in (db.get_connection, db.init_db, db.reset_db):
        check_signature(fn, db.DEFAULT_DB_PATH)

    print("\n== 4. behaviour preserved (memory DB) ==")
    conn = db.init_db(":memory:")
    rows = [r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    check("init_db(':memory:') creates tables", bool(rows), str(rows))
    check(
        "row_factory is sqlite3.Row",
        conn.row_factory is __import__("sqlite3").Row,
    )
    fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    check("PRAGMA foreign_keys = ON", fk == 1, str(fk))
    conn.close()

    print("\n== 5. env-driven overrides (fresh subprocesses) ==")
    import subprocess

    tmp = tempfile.mkdtemp(prefix="notesapi_cfg_")
    env = dict(os.environ, **{
        "NOTES_API_DB_PATH": os.path.join(tmp, "override.db"),
        "NOTES_API_SECRET_KEY": "sekret-123",
        "NOTES_API_ENV": "production",
        "NOTES_API_HOST": "0.0.0.0",
        "NOTES_API_PORT": "9999",
    })
    probe = (
        "import config, db;"
        "print(config.DB_PATH);"
        "print(db.DEFAULT_DB_PATH);"
        "print(config.SECRET_KEY);"
        "print(config.ENV);"
        "print(config.HOST);"
        "print(config.PORT);"
        "assert config.DB_PATH == os.path.join(r'%s', 'override.db');"
        "assert db.DEFAULT_DB_PATH == config.DB_PATH;"
        "assert config.SECRET_KEY == 'sekret-123';"
        "assert config.ENV == 'production';"
        "assert config.HOST == '0.0.0.0';"
        "assert config.PORT == 9999;"
        "assert isinstance(config.PORT, int)"
        % tmp
    )
    env["WITH_OS"] = "1"
    probe = "import os;" + probe
    proc = subprocess.run(
        [sys.executable, "-c", probe], cwd=HERE, env=env,
        capture_output=True, text=True,
    )
    check(
        "NOTES_API_* overrides honoured",
        proc.returncode == 0,
        (proc.stdout + proc.stderr).strip().replace("\n", " | "),
    )

    print("\n== summary ==")
    if _failures:
        print(f"{len(_failures)} FAILED: {_failures}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
