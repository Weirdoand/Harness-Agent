---
name: Notes API 认证模块实现与安全约束
type: 项目事实
description: 认证任务已完成，纯增量 auth.py + test_auth.py，32 测试全绿，PBKDF2/HMAC-SHA256。
---

认证模块任务（owner teammate_1，任务号 1f0c0b9c / 原 4eacba45）已完成。分支 refactor/auth，worktree .worktrees/auth-refactor，工作树干净。新增 additive 文件 workspace/notesapi/auth.py（约 310 行）与 test_auth.py，测试 32 个全绿（0.680s）。提交：f0db370 test: add auth module test suite；803e862 refactor: add authentication module (password hashing + token issue/verify), additive only；基线主分支 2b5f5c2。硬约束：只能做加法，不得修改或改变任何已有接口；必须在隔离 git worktree 中执行（优先复用 .worktrees/auth-refactor，分支 refactor/auth）；不得触碰 notesapi/db.py、schema.sql、verify_schema.py；完成后校验受保护文件未改动、worktree 干净，在分支提交并 complete_task。实现要求：密码哈希用 PBKDF2-HMAC-SHA256 + 随机盐 + hmac.compare_digest 常量时间比较；token 签发/校验用 HMAC-SHA256，覆盖篡改与过期检测。注意主树与 worktree 各可能存在一份 auth.py，需确认实现一致。