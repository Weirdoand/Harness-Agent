# -*- coding: utf-8 -*-
"""Introspect the TaskManager API."""
import os
import sys
import inspect

REPO = r"H:\AI Files\Harness-Agent"
sys.path.insert(0, REPO)
os.chdir(REPO)

from llm_chat import TaskManager, TaskState

print("=== TaskState members ===")
for name in dir(TaskState):
	if not name.startswith("_"):
		print(" ", name, "=", getattr(TaskState, name))

print("\n=== public methods ===")
for name, member in inspect.getmembers(TaskManager):
	if name.startswith("_"):
		continue
	if inspect.isfunction(member) or inspect.ismethod(member):
		try:
			sig = str(inspect.signature(member))
		except Exception:  # noqa: BLE001
			sig = "(?)"
		print(" ", name + sig)
