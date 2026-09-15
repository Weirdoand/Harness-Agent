---
name: Notes API 重构任务集与测试套件要求
type: 项目事实
description: 三个重构任务、依赖关系、测试覆盖要求与历史任务节点。
---

Notes API 后端重构执行集记录于共享任务板：(1) f5d814aa-d60e-4a14-8bca-78c1e8391b7c — refactor: extract backend configuration（teammate_2，主工作树原地执行，无前置依赖）；(2) 4eacba45-44ad-436f-9ff4-62d671adb576 — refactor: add authentication module（teammate_1，隔离 worktree 纯增量，不得改变现有接口）；(3) d0fa4f4a-4c48-4222-a6d3-8534f3857430 — refactor: add backend test suite（teammate_2），blockBy 为 f5d814aa 与 4eacba45，需在配置与认证完成后进行；为 config、auth 及既有 db 接口写可执行 pytest 风格测试，覆盖 config 环境变量契约与导入安全、db 公共接口签名不变（get_connection/init_db/reset_db 及 DEFAULT_DB_PATH 向后兼容）、认证哈希/校验/token 有效与篡改场景，认证部分对应 notesapi/test_auth.py 并确保全绿。依赖通过 assign_dependencies 写入并回读校验。历史任务节点：setup database schema 28f6a0c0（无前置）、create API endpoints b461b75b（被其阻塞）、write tests 24a231d4（被 b461b75b 阻塞）、write docs e311b609（被 28f6a0c0 阻塞）；write tests 24a231d4 处于 pending。