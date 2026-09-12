# -*- coding: utf-8 -*-
"""Complete the 'setup database schema' task and report newly unblocked tasks."""
import os
import sys

REPO = r"H:\AI Files\Harness-Agent"
sys.path.insert(0, REPO)
os.chdir(REPO)

TaskManager = None
for modname in ("task_manager", "llm_chat"):
	try:
		m = __import__(modname)
		TaskManager = getattr(m, "TaskManager")
		print("loaded TaskManager from:", modname)
		break
	except Exception as e:  # noqa: BLE001
		print("import %s failed: %r" % (modname, e))

if TaskManager is None:
	raise SystemExit("could not import TaskManager")

SCHEMA_TASK = "28f6a0c0-7bab-4bc1-b1f2-50aa0f9fa758"


def main():
	tm = TaskManager()
	unlocked = tm.complete_task(SCHEMA_TASK)
	print("completed task:", SCHEMA_TASK)
	print("newly unblocked tasks:")
	for t in unlocked:
		print("  - %s | %s" % (t["id"], t["subject"]))
	tm.print_task_panel()


if __name__ == "__main__":
	main()
