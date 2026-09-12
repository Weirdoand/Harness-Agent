# -*- coding: utf-8 -*-
"""Create the project task graph via the repo's own TaskManager."""
import os
import sys

REPO = r"H:\AI Files\Harness-Agent"
sys.path.insert(0, REPO)
os.chdir(REPO)

TaskManager = None
TaskState = None
for modname in ("task_manager", "llm_chat"):
	try:
		m = __import__(modname)
		TaskManager = getattr(m, "TaskManager")
		TaskState = getattr(m, "TaskState")
		print("loaded TaskManager from:", modname)
		break
	except Exception as e:  # noqa: BLE001
		print("import %s failed: %r" % (modname, e))

if TaskManager is None:
	raise SystemExit("could not import TaskManager")


def main():
	tm = TaskManager()

	# Allow re-runs: start from a clean slate.
	tm._write_tasks([])

	schema = tm.create_task("setup database schema", "Design and set up the database schema.")
	endpoints = tm.create_task("create API endpoints", "Create API endpoints. Depends on the database schema.")
	tests = tm.create_task("write tests", "Write tests. Depends on the API endpoints.")
	docs = tm.create_task("write docs", "Write documentation. Depends on the database schema.")

	# Dependencies:
	#   endpoints <- schema
	#   tests     <- endpoints
	#   docs      <- schema
	tm.assign_dependencies(endpoints, [schema])
	tm.assign_dependencies(tests, [endpoints])
	tm.assign_dependencies(docs, [schema])

	tm.print_task_panel()

	with open(tm.file_path, encoding="utf-8") as f:
		print(f.read())


if __name__ == "__main__":
	main()
