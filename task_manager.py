"""独立的任务管理契约实现，供测试和轻量集成使用。"""
import json, os, uuid, tempfile
from filelock import FileLock
from enum import Enum
from datetime import datetime, timezone

class TaskState(str, Enum):
    PENDING = "pending"; IN_PROCESS = "in_process"; COMPLETE = "complete"

class TaskManager:
    def __init__(self, data_dir=".task"):
        self.data_dir = data_dir; os.makedirs(data_dir, exist_ok=True); self.lock_path=os.path.join(data_dir,"tasks_global.lock")
    def _files(self): return [os.path.join(self.data_dir, x) for x in os.listdir(self.data_dir) if x.startswith("task_") and x.endswith(".json")]
    def _read(self):
        out=[]
        for p in self._files():
            try:
                with open(p, encoding="utf-8") as f: out.append(json.load(f))
            except (OSError, ValueError): pass
        return out
    def _write(self,t):
        target=os.path.join(self.data_dir, f"task_{t['id']}.json")
        fd,tmp=tempfile.mkstemp(dir=self.data_dir,prefix=".task-",suffix=".tmp")
        try:
            with os.fdopen(fd,"w",encoding="utf-8") as f: json.dump(t,f,ensure_ascii=False); f.flush(); os.fsync(f.fileno())
            os.replace(tmp,target)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
    def create_task(self, subject, description, worktree=None):
        i=str(uuid.uuid4()); now=datetime.now(timezone.utc).isoformat()
        with FileLock(self.lock_path): self._write({"id":i,"subject":subject,"description":description,"state":"pending","owner":None,"blockBy":[],"worktree":worktree,"created_at":now,"updated_at":now})
        return i
    def get_task(self, task_id):
        with FileLock(self.lock_path): return next((t for t in self._read() if t["id"]==task_id),None)
    def assign_dependencies(self, task_id, depends_on_ids):
        with FileLock(self.lock_path):
            ts=self._read(); t=next((x for x in ts if x["id"]==task_id),None); ids=list(dict.fromkeys(depends_on_ids or []))
            if not t or t["state"]!="pending" or t.get("owner") or any(x not in {y["id"] for y in ts} for x in ids) or task_id in ids: return False
            graph={x["id"]:set(x.get("blockBy",[])) for x in ts}; graph[task_id].update(ids)
            def cycle(n, stack, seen):
                if n in stack:return True
                if n in seen:return False
                seen.add(n); return any(cycle(x,stack|{n},seen) for x in graph.get(n,()))
            if cycle(task_id,set(),set()): return False
            t["blockBy"]=list(dict.fromkeys(t.get("blockBy",[])+ids)); self._write(t); return True
    def claim_task(self, task_id, owner):
        with FileLock(self.lock_path):
            ts=self._read(); t=next((x for x in ts if x["id"]==task_id),None)
            if not t:return {"success":False,"error":"任务不存在"}
            if not owner:return {"success":False,"error":"owner 不能为空"}
            if t["state"]!="pending":return {"success":False,"error":"任务状态必须为 pending"}
            if any(next((d for d in ts if d["id"]==i),{}).get("state")!="complete" for i in t.get("blockBy",[])):return {"success":False,"error":"前置依赖任务未完成"}
            if any(x.get("owner")==owner and x.get("state")=="in_process" for x in ts):return {"success":False,"error":"该 owner 已有执行中的任务"}
            t.update(state="in_process",owner=owner); self._write(t); return {"success":True,"task":t}
    def complete_task(self, task_id, owner=None):
        with FileLock(self.lock_path):
            t=next((x for x in self._read() if x["id"]==task_id),None)
            if not owner or not t or t["state"]!="in_process" or t.get("owner")!=owner: return []
            t["state"]="complete"; self._write(t); return [x for x in self._read() if x["state"]=="pending" and task_id in x.get("blockBy",[])]
    def release_task(self, task_id, owner):
        with FileLock(self.lock_path):
            t=next((x for x in self._read() if x["id"]==task_id),None)
            if not t or t.get("owner")!=owner: return False
            t.update(state="pending", owner=None); self._write(t); return True
    def bind_worktree(self, task_id, path):
        with FileLock(self.lock_path):
            t=next((x for x in self._read() if x["id"]==task_id),None)
            if not t or t.get("state")!="pending" or t.get("owner"): return False
            t["worktree"]=path; self._write(t); return True
    def can_bind_worktree(self, task_id):
        with FileLock(self.lock_path):
            t=next((x for x in self._read() if x["id"]==task_id),None)
            return bool(t and t.get("state")=="pending" and not t.get("owner") and not t.get("worktree"))
    def list_tasks(self,state=None,owner=None):
        with FileLock(self.lock_path): return [x for x in self._read() if (state is None or x.get("state")==state) and (owner is None or x.get("owner")==owner)]
