import os
import shutil
import unittest
from task_manager import TaskManager, TaskState

class TestTaskManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = ".test_task"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        self.tm = TaskManager(data_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_task(self):
        task_id = self.tm.create_task("Test Task", "Desc")
        self.assertIsNotNone(task_id)
        
        task = self.tm.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task["subject"], "Test Task")
        self.assertEqual(task["state"], TaskState.PENDING.value)

    def test_assign_dependencies(self):
        t1 = self.tm.create_task("Task 1", "")
        t2 = self.tm.create_task("Task 2", "")
        
        res = self.tm.assign_dependencies(t2, [t1])
        self.assertTrue(res)
        
        task2 = self.tm.get_task(t2)
        self.assertIn(t1, task2["blockBy"])

    def test_claim_task_success(self):
        t1 = self.tm.create_task("T1", "")
        res = self.tm.claim_task(t1, "AgentA")
        self.assertTrue(res["success"])
        self.assertEqual(res["task"]["owner"], "AgentA")
        self.assertEqual(res["task"]["state"], TaskState.IN_PROCESS.value)

    def test_claim_task_blocked(self):
        t1 = self.tm.create_task("T1", "")
        t2 = self.tm.create_task("T2", "")
        self.tm.assign_dependencies(t2, [t1])
        
        # T1 pending, so T2 cannot be claimed
        res = self.tm.claim_task(t2, "AgentA")
        self.assertFalse(res["success"])
        self.assertIn("未完成", res["error"])

    def test_complete_task_unlocks_downstream(self):
        t1 = self.tm.create_task("T1", "")
        t2 = self.tm.create_task("T2", "")
        self.tm.assign_dependencies(t2, [t1])
        
        self.tm.claim_task(t1, "AgentA")
        
        # Complete T1, it should unlock T2
        unlocked = self.tm.complete_task(t1)
        self.assertEqual(len(unlocked), 1)
        self.assertEqual(unlocked[0]["id"], t2)
        
        # Now T2 should be claimable
        res = self.tm.claim_task(t2, "AgentB")
        self.assertTrue(res["success"])

    def test_list_tasks(self):
        t1 = self.tm.create_task("T1", "")
        t2 = self.tm.create_task("T2", "")
        self.tm.claim_task(t1, "AgentA")
        
        pending_tasks = self.tm.list_tasks(state=TaskState.PENDING.value)
        self.assertEqual(len(pending_tasks), 1)
        self.assertEqual(pending_tasks[0]["id"], t2)

if __name__ == '__main__':
    unittest.main()
