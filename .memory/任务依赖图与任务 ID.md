---
name: 任务依赖图与任务 ID
type: 项目事实
description: 项目四个开发任务及其依赖关系与持久化 ID。
---

项目任务依赖关系（持久）：
- 任务 ID 28f6a0c0-7bab-4bc1-b1f2-50aa0f9fa758：setup database schema（Design and set up the database schema. 无前置依赖）
- 任务 ID b461b75b-695b-40e6-aaf4-d89c5af6de95：create API endpoints（Create API endpoints. 被 setup database schema 阻塞）
- 任务：write tests（ID 24a231d4，被 create API endpoints 阻塞）
- 任务：write docs（ID e311b609，被 setup database schema 阻塞）
依赖关系：create API endpoints ← setup database schema；write tests ← create API endpoints；write docs ← setup database schema。