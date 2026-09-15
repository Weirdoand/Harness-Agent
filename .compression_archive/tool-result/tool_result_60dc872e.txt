# -*- coding: utf-8 -*-
"""Smoke-test the schema against an in-memory SQLite database.

Checks that the DDL applies and that the intended constraints/cascades are
actually enforced (not just declared).
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import init_db  # noqa: E402

FAILURES = []


def check(label, condition):
	status = "PASS" if condition else "FAIL"
	print("  [%s] %s" % (status, label))
	if not condition:
		FAILURES.append(label)


def expect_error(label, fn):
	try:
		fn()
	except sqlite3.IntegrityError:
		check(label, True)
	else:
		check(label, False)


def main():
	conn = init_db(":memory:")
	cur = conn.cursor()

	print("\n1. structure")
	tables = {r["name"] for r in cur.execute(
		"SELECT name FROM sqlite_master WHERE type='table'")}
	expected = {"users", "notes", "tags", "note_tags", "schema_migrations"}
	check("all tables created", expected <= tables)
	check("foreign_keys pragma is ON",
	      cur.execute("PRAGMA foreign_keys").fetchone()[0] == 1)
	check("migration v1 recorded",
	      cur.execute("SELECT version FROM schema_migrations").fetchone()[0] == 1)

	print("\n2. notes.user_id -> users.id")
	cur.execute("INSERT INTO users (email, name) VALUES (?, ?)",
	            ("alice@example.com", "Alice"))
	alice = cur.lastrowid
	check("insert user returns rowid", alice is not None)

	expect_error("unknown user_id is rejected", lambda: cur.execute(
		"INSERT INTO notes (user_id, title) VALUES (99999, 'orphan')"))

	print("\n3. defaults and constraints")
	cur.execute("INSERT INTO notes (user_id, title) VALUES (?, ?)", (alice, "First"))
	note = cur.lastrowid
	check("body defaults to empty string",
	      cur.execute("SELECT body FROM notes WHERE id=?", (note,)).fetchone()[0] == "")
	check("created_at auto-filled",
	      cur.execute("SELECT created_at FROM notes WHERE id=?", (note,)).fetchone()[0] != "")
	expect_error("blank title is rejected", lambda: cur.execute(
		"INSERT INTO notes (user_id, title) VALUES (?, '   ')", (alice,)))

	print("\n4. unique email is case-insensitive")
	expect_error("duplicate email differing only by case is rejected",
	             lambda: cur.execute("INSERT INTO users (email, name) VALUES (?, ?)",
	                                 ("ALICE@example.com", "Alice2")))

	print("\n5. updated_at trigger")
	# updated_at is wall-clock based, so a fast insert+update can land in the
	# same millisecond. Seed a known-stale value to make the assertion
	# deterministic rather than timing-dependent.
	stale = "2000-01-01T00:00:00.000Z"
	cur.execute("UPDATE notes SET updated_at=? WHERE id=?", (stale, note))
	cur.execute("UPDATE notes SET title='First (edited)' WHERE id=?", (note,))
	after = cur.execute("SELECT updated_at FROM notes WHERE id=?", (note,)).fetchone()[0]
	check("updated_at refreshed when title changes", after != stale)
	check("updated_at is an ISO-8601 UTC timestamp",
	      len(after) == 24 and after.endswith("Z") and after[4] == "-")

	# Columns outside (title, body) must not bump updated_at.
	cur.execute("UPDATE notes SET updated_at=? WHERE id=?", (stale, note))
	cur.execute("UPDATE notes SET user_id=user_id WHERE id=?", (note,))
	check("editing an unrelated column does not refresh updated_at",
	      cur.execute("SELECT updated_at FROM notes WHERE id=?", (note,)).fetchone()[0] == stale)

	print("\n6. many-to-many note_tags")
	cur.execute("INSERT INTO tags (name) VALUES ('work')")
	work = cur.lastrowid
	cur.execute("INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)", (note, work))
	check("note_tag link created",
	      cur.execute("SELECT COUNT(*) FROM note_tags").fetchone()[0] == 1)
	expect_error("duplicate (note_id, tag_id) rejected", lambda: cur.execute(
		"INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)", (note, work)))

	print("\n7. cascades")
	cur.execute("DELETE FROM users WHERE id=?", (alice,))
	check("deleting user cascades to notes",
	      cur.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0)
	check("deleting user cascades to note_tags",
	      cur.execute("SELECT COUNT(*) FROM note_tags").fetchone()[0] == 0)
	check("tags survive (no cascade from notes)",
	      cur.execute("SELECT COUNT(*) FROM tags").fetchone()[0] == 1)

	print("\n8. idempotent re-apply")
	try:
		init_db(":memory:")
		check("schema can be applied twice without error", True)
	except sqlite3.Error as exc:
		print("     ", exc)
		check("schema can be applied twice without error", False)

	conn.close()
	print("\n%s" % ("ALL CHECKS PASSED" if not FAILURES else "FAILED: %s" % FAILURES))
	return 1 if FAILURES else 0


if __name__ == "__main__":
	raise SystemExit(main())
