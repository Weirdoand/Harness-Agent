---
name: Notes API 后端重构任务集与测试要求
type: 项目事实
description: 三个重构任务、依赖关系、测试覆盖要求与当前状态。
---

Notes API 后端重构执行集记录于共享任务板：(1) f5d814aa-d60e-4a14-8bca-78c1e8391b7c — refactor: extract backend configuration（owner teammate_2，主工作树原地执行，无前置依赖，已完成）；(2) 4eacba45-44ad-436f-9ff4-62d671adb576 — refactor: add authentication module（owner teammate_1，隔离 worktree 纯增量，不得改变现有接口，已完成）；(3) d0fa4f4a-4c48-4222-a6d3-8534f3857430 — refactor: add backend test suite（owner teammate_2），blockBy 为 f5d814aa 与 4eacba45，需在配置与认证完成后进行；为 config、auth 及既有 db 接口写可执行 pytest 风格测试，覆盖 config 环境变量契约与导入安全、db 公共接口签名不变（get_connection/init_db/reset_db 及 DEFAULT_DB_PATH 向后兼容）、认证哈希/校验/token 有效与篡改场景，认证部分对应 notesapi/test_auth.py 并确保全绿。依赖通过 assign_dependencies 写入并回读校验。后端测试文件位于 tests/test_backend.py 时使用 pytest 运行，示例结果：32 passed, 30 subtests passed in 0.80s。