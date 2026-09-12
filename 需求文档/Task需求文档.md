# Task需求文档

## 1. 背景与概述
TaskManager 旨在为复杂 Agent 系统提供一个统一的任务调度和管理接口，支持多任务拆分、依赖管理和状态追踪。系统允许多个 Agent 并发读写任务状态，保证了任务的有序执行。

## 2. 存储设计
- **文件路径**: 数据统一存储于当前目录下的 `.task/tasks.json` 文件中。
- **并发控制**: 由于可能存在多个 Subagent 同时读写任务文件的场景，文件读写时必须加锁（文件锁，如 FileLock 机制）以保证数据一致性。
- **持久化**: `TaskManager` 类在实例化或执行读操作前加载文件，并在每次状态发生变更后立即执行落盘（存入 json 文件）操作。

## 3. 数据模型 (Task Schema)
每一条任务（Task）采用以下字段结构：
- `id` (string): 任务的唯一标识，使用 UUID 自动生成。
- `subject` (string): 任务的主题或简述。
- `description` (string): 任务的详细描述与执行要求。
- `state` (enum): 当前任务的执行状态，仅包含以下三种：
  - `pending` (待处理/排队中，包括已被阻塞的情况)
  - `in_process` (执行中)
  - `complete` (已完成)
- `owner` (string): 当前认领并执行该任务的 Agent 标识（初始为空）。
- `blockBy` (list<string>): 任务依赖列表，存储该任务所依赖的其他前置 `Task.id`。
- `created_at` (string/timestamp): 任务创建时间（可选参数，便于审计追踪）。
- `updated_at` (string/timestamp): 任务最后更新时间（可选参数，便于审计追踪）。

## 4. 任务生命周期与流转规则
1. **创建任务**: 任务生成后初始状态即为 `pending`。
2. **认领任务**:
   - Agent 只能认领状态为 `pending` 且**所有的前置依赖任务（即 `blockBy` 列表中的任务 ID）都已达到 `complete` 状态**的任务。
   - 认领成功后，状态变更为 `in_process`，并更新 `owner` 字段。
3. **完成任务**:
   - Agent 完成一个状态为 `in_process` 的任务后，将其标记为 `complete`。
   - 任务完成后，系统需遍历整个任务池，寻找所有依赖于该任务的下游任务（即 `blockBy` 中包含刚刚完成任务 ID 的所有 `pending` 任务）。判断这些下游任务是否满足了认领条件（即所有的依赖全部为 `complete`），这相当于动态实现了任务“解锁”过程。

## 5. 新增工具方法 (Tool Schema)
TaskManager 需对外提供以下 6 个核心工具方法（将直接映射给 LLM Tools 调用）：

1. **创建任务 (create_task)**
   - **参数**: `subject` (string), `description` (string)
   - **行为**: 创建一个新任务，生成 UUID，状态设为 `pending`，并保存到本地。
   - **返回**: 新任务的 `id`。

2. **分配依赖任务 (assign_dependencies)**
   - **参数**: `task_id` (string), `depends_on_ids` (list<string>)
   - **行为**: 对指定任务进行依赖分配，将 `depends_on_ids` 加入到目标任务的 `blockBy` 列表中。主要是针对新创建的任务，或为正在规划的执行链设置前置阻塞条件。
   - **返回**: 操作成功/失败状态。

3. **认领任务 (claim_task)**
   - **参数**: `task_id` (string), `owner` (string)
   - **行为**: 认领一个状态为 `pending` 的任务。执行前**必须校验**其 `blockBy` 列表中的所有前置任务状态均为 `complete`。校验通过后，将状态修改为 `in_process` 并记录 `owner`。
   - **返回**: 认领成功返回任务具体信息；如果前置依赖未完成、或任务已被他人认领，则返回明确的失败原因。

4. **完成与解锁任务 (complete_task)**
   - **参数**: `task_id` (string)
   - **行为**: 将一个状态为 `in_process` 的任务（通常需要校验调用者 owner，但这层在 Agent 中可控）标记为 `complete`。执行完毕后，遍历所有 `pending` 状态的任务，检查并返回**刚刚因为此任务的完成而彻底解除阻塞**（所有依赖均已完结）的下游可接手任务列表。
   - **返回**: 解锁的新下游任务列表。

5. **获取任务 (get_task)**
   - **参数**: `task_id` (string)
   - **行为**: 根据 ID 查找并返回单一任务的完整字段详情。
   - **返回**: JSON 格式的任务对象。

6. **获取任务列表 (list_tasks)**
   - **参数**: `state` (enum, optional), `owner` (string, optional)
   - **行为**: 根据条件过滤返回任务集合。便于 Agent 查询自己名下执行中的任务，或者从系统池中扫描当前所有“可认领（`pending`）且无阻塞”的任务。
   - **返回**: 任务列表集合。

## 6. 建议架构实现
建议通过编写一个单一的 `TaskManager` 类，来统一封装上述 6 个方法的底层读写逻辑。其内部职责包括隔离并处理好文件锁（FileLock）的竞争和并发问题，对外仅对 Agent 或各业务逻辑暴露极其简单透明的接口（API），保证数据的强一致性。