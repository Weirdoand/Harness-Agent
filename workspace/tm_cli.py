# -*- coding: utf-8 -*-
"""Thin CLI over the repo's TaskManager (the harness task tools return empty output).

Usage:
    python workspace/tm_cli.py list [state]
    python workspace/tm_cli.py claim  <task_id> <owner>
    python workspace/tm_cli.py complete <task_id>
"""
import os
import sys

REPO = r"H:\AI Files\Harness-Agent"
sys.path.insert(0, REPO)
os.chdir(REPO)

from llm_chat import TaskManager  # noqa: E402


def short(tid):
	return (tid or "")[:8]


def show(t):
	print("  %s | %-26s | blockBy=%s | state=%s | owner=%s" % (
		short(t["id"]), t["subject"],
		[short(x) for x in t.get("blockBy", [])],
		t.get("state"), t.get("owner") or "-"))


def main():
	if len(sys.argv) < 2:
		raise SystemExit(__doc__)
	cmd = sys.argv[1]
	tm = TaskManager()

	if cmd == "list":
		state = sys.argv[2] if len(sys.argv) > 2 else None
		print("tasks (state=%s):" % (state or "any"))
		for t in tm.list_tasks(state=state):
			show(t)

	elif cmd == "claim":
		tid, owner = sys.argv[2], sys.argv[3]
		res = tm.claim_task(tid, owner)
		print("claim result:", res.get("state"), "| owner:", res.get("owner"))

	elif cmd == "complete":
		tid = sys.argv[2]
		unblocked = tm.complete_task(tid)
		print("completed %s" % short(tid))
		if unblocked:
			print("newly unblocked (%d):" % len(unblocked))
			for t in unblocked:
				show(t)
		else:
			print("newly unblocked: none")

	else:
		raise SystemExit("unknown command: %s" % cmd)

	print()
	print("--- task panel ---")
	tm.print_task_panel()


if __name__ == "__main__":
	main()
