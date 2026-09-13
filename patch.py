import sys

filepath = r'h:\AI Files\Harness-Agent\llm_chat.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Find where to insert CronManager
insert_idx_1 = -1
for i, line in enumerate(lines):
    if '# 定义供 LLM 调用的基础工具 Schema' in line:
        insert_idx_1 = i
        break

if insert_idx_1 != -1:
    cron_manager_code = """
# ---------- CronManager ----------
import time
import threading
import uuid
import json
import os
from datetime import datetime
try:
    from croniter import croniter
except ImportError:
    pass

class CronJob:
    def __init__(self, cron_expression: str, prompt: str, is_recurring: bool = False, is_persistent: bool = False, job_id: str = None, has_pending_task: bool = False, last_trigger_time: float = 0.0):
        self.job_id = job_id or str(uuid.uuid4())[:8]
        self.cron_expression = cron_expression
        self.prompt = prompt
        self.is_recurring = is_recurring
        self.is_persistent = is_persistent
        self.has_pending_task = has_pending_task
        self.last_trigger_time = last_trigger_time
        
    def to_dict(self):
        return {
            "job_id": self.job_id,
            "cron_expression": self.cron_expression,
            "prompt": self.prompt,
            "is_recurring": self.is_recurring,
            "is_persistent": self.is_persistent,
            "has_pending_task": self.has_pending_task,
            "last_trigger_time": self.last_trigger_time
        }
        
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

class CronManager:
    def __init__(self, data_dir=".cron"):
        self.jobs = {}
        self.pending_queue = []
        self.data_dir = data_dir
        self.file_path = os.path.join(self.data_dir, "cron_jobs.json")
        self.lock = threading.Lock()
        
        os.makedirs(self.data_dir, exist_ok=True)
        self.load_jobs()
        
        # Start background threads
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.executor_thread = threading.Thread(target=self._executor_loop, daemon=True)
        
        self.scheduler_thread.start()
        self.executor_thread.start()

    def load_jobs(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for job_data in data:
                        job = CronJob.from_dict(job_data)
                        self.jobs[job.job_id] = job
            except Exception as e:
                print(f"[CronManager] 加载持久化任务失败: {e}")

    def save_jobs(self):
        persistent_jobs = [j.to_dict() for j in self.jobs.values() if j.is_persistent]
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(persistent_jobs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CronManager] 保存持久化任务失败: {e}")

    def create_job(self, cron_expression: str, prompt: str, is_recurring: bool = False, is_persistent: bool = False) -> str:
        try:
            if not croniter.is_valid(cron_expression):
                return "创建失败：无效的 Cron 表达式。"
        except NameError:
            pass
            
        with self.lock:
            if len(self.jobs) >= 100:
                return "创建失败：定时任务数量已达上限 (100个)。"
                
            job = CronJob(
                cron_expression=cron_expression,
                prompt=prompt,
                is_recurring=is_recurring,
                is_persistent=is_persistent
            )
            self.jobs[job.job_id] = job
            if job.is_persistent:
                self.save_jobs()
            return f"成功创建 Cron 定时任务，ID: {job.job_id}"

    def cancel_job(self, job_id: str) -> str:
        with self.lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
                self.save_jobs()
                return f"成功取消定时任务 {job_id}。"
            return f"取消失败：未找到 ID 为 {job_id} 的任务。"

    def get_jobs(self) -> str:
        with self.lock:
            if not self.jobs:
                return "当前无活跃的定时任务。"
            job_lines = []
            for j in self.jobs.values():
                job_lines.append(f"- ID: {j.job_id} | Cron: '{j.cron_expression}' | Recurring: {j.is_recurring} | Persistent: {j.is_persistent} | Prompt: {j.prompt}")
            return "\\n".join(job_lines)

    def _scheduler_loop(self):
        while True:
            try:
                now = datetime.now()
                now_timestamp = now.timestamp()
                
                with self.lock:
                    for job in self.jobs.values():
                        if job.has_pending_task:
                            continue
                            
                        try:
                            if croniter.match(job.cron_expression, now):
                                if now_timestamp - job.last_trigger_time >= 60:
                                    job.has_pending_task = True
                                    job.last_trigger_time = now_timestamp
                                    self.pending_queue.append(job.job_id)
                        except NameError:
                            pass
            except Exception as e:
                print(f"[CronManager] Scheduler Error: {e}")
                
            time.sleep(1)

    def _executor_loop(self):
        while True:
            job_id_to_run = None
            with self.lock:
                if self.pending_queue:
                    job_id_to_run = self.pending_queue.pop(0)
                    
            if job_id_to_run:
                job = None
                with self.lock:
                    job = self.jobs.get(job_id_to_run)
                
                if job:
                    print(f"\\n\\033[95m[CronManager] 触发定时任务 {job.job_id}: {job.prompt}\\033[0m")
                    try:
                        def run_agent():
                            global agent_loop
                            agent_loop(messages=[{"role": "user", "content": f"【Cron 定时任务触发】\\n{job.prompt}"}], latest_user_input=f"CronTask:{job.prompt}")
                            
                        t = threading.Thread(target=run_agent, daemon=True)
                        t.start()
                    except Exception as e:
                        print(f"[CronManager] 执行任务失败 {job.job_id}: {e}")
                        
                    with self.lock:
                        job.has_pending_task = False
                        if not job.is_recurring:
                            if job.job_id in self.jobs:
                                del self.jobs[job.job_id]
                            self.save_jobs()
            else:
                time.sleep(1)

cron_manager = CronManager()

"""
    lines.insert(insert_idx_1, cron_manager_code)

# 2. Add tools to BASE_TOOLS
insert_idx_2 = -1
for i, line in enumerate(lines):
    if 'task_schema = {' in line:
        insert_idx_2 = i
        break

if insert_idx_2 != -1:
    cron_tools = """
    {
        "type": "function",
        "function": {
            "name": "create_cron_job",
            "description": "创建一个定时任务，允许 LLM 在未来某个时间点或按特定周期主动执行特定的 prompt 任务。当使用时间表达式如 '每天早上8点' 时，必须使用这个工具转换为 cron 执行。",
            "parameters": {
                "type": "object",
                "properties": {
                    "cron_expression": {
                        "type": "string",
                        "description": "标准 Cron 表达式（如 '0 8 * * *' 每天早八点）。"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "任务触发时发送给 LLM 执行的指令文本。"
                    },
                    "is_recurring": {
                        "type": "boolean",
                        "description": "是否循环执行。若为 false，则触发一次后自动销毁；若为 true，则按 Cron 周期不断触发。"
                    },
                    "is_persistent": {
                        "type": "boolean",
                        "description": "是否将此任务持久化存储到本地，以便重启后也能恢复执行。"
                    }
                },
                "required": ["cron_expression", "prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_cron_job",
            "description": "提前终止或取消一个指定的定时任务。",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "需要取消的任务的唯一 ID。"
                    }
                },
                "required": ["job_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cron_jobs",
            "description": "查询当前系统中所有活跃的定时任务列表，以便进行自我检查和管理。",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
"""
    # Find the end of BASE_TOOLS list
    # The line right before insert_idx_2 is likely `]` closing BASE_TOOLS
    # Wait, in the code, `BASE_TOOLS = [ ... ]`
    # Let's insert the dicts into BASE_TOOLS by finding the last `]` before `task_schema = {`
    # Actually, simpler to just inject `BASE_TOOLS.extend([...])` after `BASE_TOOLS` is fully defined
    
    inject_extend = """
BASE_TOOLS.extend([
""" + cron_tools + """
])
"""
    lines.insert(insert_idx_2, inject_extend)


# 3. Add to BASE_FUNCTIONS
insert_idx_3 = -1
for i, line in enumerate(lines):
    if '"manage_task": manage_task' in line:
        insert_idx_3 = i
        break

if insert_idx_3 != -1:
    funcs_injection = """    "manage_task": manage_task,
    "create_cron_job": cron_manager.create_job,
    "cancel_cron_job": cron_manager.cancel_job,
    "get_cron_jobs": cron_manager.get_jobs
"""
    lines[insert_idx_3] = funcs_injection

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Patch applied')
