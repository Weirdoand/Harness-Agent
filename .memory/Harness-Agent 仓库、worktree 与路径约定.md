---
name: Harness-Agent 仓库、worktree 与路径约定
type: 项目事实
description: 仓库根、主分支、隔离 worktree、归档路径及隔离改动约定。
---

仓库根 H:/AI Files/Harness-Agent，主分支 main（基线 2b5f5c2，remote origin/main）；主工作区 H:/AI Files/Harness-Agent/workspace。隔离 worktree .worktrees/auth-refactor 对应分支 refactor/auth，曾用于 Notes API 认证重构。工具结果归档在 .compression_archive/tool-result/。约定：需要隔离的改动在 worktree 内进行，默认在主工作目录原地修改、不使用 worktree，除非任务明确要求；改动不得污染 main。认证任务必须在独立 worktree（如 .worktrees/auth-refactor）执行；其他任务禁止触碰 .worktrees/ 和 auth.py。曾出现 allocate_worktree 因 FileLock 死锁不可用（错误涉及 lock '.task\task'），此时改用既有/手动创建的 worktree。受保护文件：notesapi/db.py、schema.sql、verify_schema.py，收口时需 sha256 比对。