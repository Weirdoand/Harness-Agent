# -*- coding: utf-8 -*-
"""Backend test suite for the refactored Notes API.

Covers the three deliverables of the refactor:

* ``config`` - environment contract (``NOTES_API_*``) and import safety;
* ``db``     - the public interface (``get_connection`` / ``init_db`` /
  ``reset_db``) is preserved, including defaults, signatures and behaviour;
* ``auth``   - password hashing (PBKDF2-HMAC-SHA256 + random salt + constant
  time compare) and HMAC-SHA256 token issue/verify with tamper & expiry cases.

Only the standard library plus ``pytest`` is required.
"""
from __future__ import annotations

import json
import os
import pathlib
import sqlite3
import subprocess
import sys

import pytest

NOTESAPI_DIR = pathlib.Path(__file__).resolve().parents[1] / "notesapi"

CLEAN_ENV = {k: v for k, v in os.environ.items() if not k.startswith("NOTES_API_")}


def _run_python(code: str, env: dict | None = None) -> dict:
    """Run ``code`` in a fresh interpreter with ``notesapi`` importable.

    Returns the JSON object the snippet printed on its last stdout line.
    """
    full_env = dict(CLEAN_ENV)
    if env:
        full_env.update(env)
    prelude = "import sys, json; sys.path.insert(0, r'%s')" % str(NOTESAPI_DIR)
    proc = subprocess.run(
        [sys.executable, "-c", prelude + "\n" + code],
        capture_output=True,
        text=True,
        env=full_env,
        timeout=180,
    )
    assert proc.returncode == 0, f"subprocess failed:\n{proc.stdout}\n{proc.stderr}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


# ---------------------------------------------------------------------------
# config: environment contract + import safety
# ---------------------------------------------------------------------------
class TestConfig:
    def test_import_is_side_effect_free(self):
        result = _run_python(
            "import gc, threading, sqlite3, config\n"
            "conns = [o for o in gc.get_objects() if isinstance(o, sqlite3.Connection)]\n"
            "print(json.dumps({'threads': threading.active_count(), 'conns': len(conns)}))\n"
        )
        assert result["threads"] == 1, "importing config must not spawn threads"
        assert result["conns"] == 0, "importing config must not open DB connections"

    def test_defaults_without_env_overrides(self):
        result = _run_python(
            "import config\n"
            "print(json.dumps({'db_path': config.DB_PATH, 'env': config.ENV,\n"
            "                  'host': config.HOST, 'port': config.PORT,\n"
            "                  'secret': config.SECRET_KEY}))\n"
        )
        assert pathlib.Path(result["db_path"]).name == "notes.db"
        assert pathlib.Path(result["db_path"]).parent == NOTESAPI_DIR
        assert result["env"] == "development"
        assert result["host"] == "127.0.0.1"
        assert result["port"] == 8000
        assert isinstance(result["secret"], str) and result["secret"]

    def test_env_overrides_are_honoured(self):
        result = _run_python(
            "import config\n"
            "print(json.dumps({'db_path': config.DB_PATH, 'env': config.ENV,\n"
            "                  'host': config.HOST, 'port': config.PORT,\n"
            "                  'secret': config.SECRET_KEY}))\n",
            env={
                "NOTES_API_DB_PATH": os.path.join("tmp", "override.db"),
                "NOTES_API_ENV": "production",
                "NOTES_API_HOST": "0.0.0.0",
                "NOTES_API_PORT": "9999",
                "NOTES_API_SECRET_KEY": "sekret-123",
            },
        )
        assert pathlib.Path(result["db_path"]).name == "override.db"
        assert result["env"] == "production"
        assert result["host"] == "0.0.0.0"
        assert result["port"] == 9999 and isinstance(result["port"], int)
        assert result["secret"] == "sekret-123"

    def test_legacy_secret_alias_is_accepted(self):
        """``NOTES_API_SECRET`` (short spelling) is accepted as an alias."""
        result = _run_python(
            "import config\nprint(json.dumps({'secret': config.SECRET_KEY}))\n",
            env={"NOTES_API_SECRET": "alias-secret", "NOTES_API_SECRET_KEY": ""},
        )
        assert result["secret"] == "alias-secret"


# ---------------------------------------------------------------------------
# db: public interface preservation
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def db():
    import importlib

    return importlib.import_module("db")


@pytest.fixture(scope="session")
def config():
    import importlib

    return importlib.import_module("config")


@pytest.fixture(scope="session")
def auth():
    import importlib

    return importlib.import_module("auth")


class TestDbInterface:
    def test_module_reexports_config_db_path(self, db, config):
        assert db.DEFAULT_DB_PATH == config.DB_PATH

    @pytest.mark.parametrize("name", ["get_connection", "init_db", "reset_db"])
    def test_signatures_unchanged(self, db, config, name):
        import inspect

        func = getattr(db, name)
        sig = inspect.signature(func)
        assert list(sig.parameters) == ["db_path"], f"{name} parameter names changed"
        assert sig.parameters["db_path"].default == db.DEFAULT_DB_PATH == config.DB_PATH
        # db.py uses ``from __future__ import annotations``, so annotations are
        # stored as strings; normalise before comparing.
        assert str(sig.return_annotation) == "sqlite3.Connection"

    def test_memory_connection_behaviour(self, db):
        conn = db.get_connection(":memory:")
        try:
            assert conn.row_factory is sqlite3.Row
            assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        finally:
            conn.close()

    def test_init_db_creates_expected_tables(self, db):
        conn = db.init_db(":memory:")
        try:
            tables = {
                r["name"]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            assert conn.row_factory is sqlite3.Row
        finally:
            conn.close()
        assert {"users", "notes", "tags", "note_tags"} <= tables

    def test_reset_db_rebuilds_schema(self, db, tmp_path):
        target = tmp_path / "reset.db"
        conn = db.reset_db(str(target))
        try:
            conn.execute(
                "INSERT INTO users (email, name) VALUES ('a@example.com', 'a')"
            )
            conn.commit()
            assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
        finally:
            conn.close()
        conn = db.reset_db(str(target))
        try:
            assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# auth: password hashing
# ---------------------------------------------------------------------------
class TestPasswordHashing:
    def test_hash_format_and_verify_roundtrip(self, auth):
        stored = auth.hash_password("correct horse battery staple")
        algo, iters, salt, digest = stored.split("$")
        assert algo == "pbkdf2_sha256"
        assert int(iters) == auth.DEFAULT_ITERATIONS
        assert salt and digest
        assert auth.verify_password("correct horse battery staple", stored) is True
        assert auth.verify_password("wrong password", stored) is False

    def test_salt_is_random_per_hash(self, auth):
        first = auth.hash_password("same-password")
        second = auth.hash_password("same-password")
        assert first != second, "per-password random salt is missing"
        assert first.split("$")[2] != second.split("$")[2]
        assert auth.verify_password("same-password", first)
        assert auth.verify_password("same-password", second)

    def test_uses_constant_time_comparison(self, auth):
        source = pathlib.Path(auth.__file__).read_text(encoding="utf-8")
        assert "hmac.compare_digest" in source, "constant-time compare missing"

    @pytest.mark.parametrize(
        "stored",
        ["", "garbage", "pbkdf2_sha256$abc$def$ghi", "a$b", "pbkdf2_sha256$1$2"],
    )
    def test_verify_password_is_total_on_malformed_input(self, auth, stored):
        assert auth.verify_password("whatever", stored) is False

    def test_verify_password_never_raises_on_non_string(self, auth):
        for bad in (None, 123, b"bytes", object()):
            assert auth.verify_password("whatever", bad) is False


# ---------------------------------------------------------------------------
# auth: tokens
# ---------------------------------------------------------------------------
class TestTokens:
    def test_issue_and_verify_roundtrip(self, auth):
        token = auth.create_token("user-1", secret="unit-secret")
        payload = auth.verify_token(token, secret="unit-secret")
        assert payload is not None
        assert payload["sub"] == "user-1"
        assert payload["exp"] > payload["iat"]
        assert payload["exp"] - payload["iat"] == auth.DEFAULT_TTL_SECONDS

    def test_payload_tampering_is_detected(self, auth):
        token = auth.create_token("user-1", secret="unit-secret")
        head, sig = token.split(".")
        flipped = ("A" if head[0] != "A" else "B") + head[1:]
        assert auth.verify_token(flipped + "." + sig, secret="unit-secret") is None

    def test_signature_tampering_is_detected(self, auth):
        token = auth.create_token("user-1", secret="unit-secret")
        head, sig = token.split(".")
        flipped = ("A" if sig[0] != "A" else "B") + sig[1:]
        assert auth.verify_token(head + "." + flipped, secret="unit-secret") is None

    def test_wrong_secret_is_rejected(self, auth):
        token = auth.create_token("user-1", secret="unit-secret")
        assert auth.verify_token(token, secret="a-different-secret") is None

    def test_expired_token_is_rejected(self, auth):
        token = auth.create_token(
            "user-1", ttl_seconds=60, now=1000.0, secret="unit-secret"
        )
        assert auth.verify_token(token, now=1030.0, secret="unit-secret") is not None
        assert auth.verify_token(token, now=1061.0, secret="unit-secret") is None

    @pytest.mark.parametrize("bad", ["", "garbage", "a.b.c.d", "no-dot", None, 42])
    def test_malformed_tokens_return_none(self, auth, bad):
        assert auth.verify_token(bad, secret="unit-secret") is None

    def test_resolve_secret_prefers_environment(self, auth, monkeypatch):
        monkeypatch.setenv("NOTES_API_SECRET", "env-secret")
        assert auth.resolve_secret() == "env-secret"
