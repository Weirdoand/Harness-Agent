---
name: Notes API 后端重构任务集与测试要求
type: 项目事实
description: Notes API 后端重构的三个任务、owner、依赖关系及测试覆盖要求。
---

Notes API 后端重构执行集记录于共享任务板：(1) f5d814aa-d60e-4a14-8bca-78c1e8391b7c — refactor: extract backend configuration（owner teammate_2，主工作树原地执行，无前置依赖）；(2) 4eacba45-44ad-436f-9ff4-62d671adb576 — refactor: add authentication module（owner teammate_1，隔离 worktree 纯增量，不得改变现有接口）；(3) d0fa4f4a-4c48-4222-a6d3-8534f3857430 — refactor: add backend test suite（owner teammate_2），blockBy 为 f5d814aa 与 4eacba45，需在配置与认证完成后进行；为 config、auth 及既有 db 接口写可执行测试。