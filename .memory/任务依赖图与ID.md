---
name: 任务依赖图与ID
type: 项目事实
description: 项目任务及其依赖关系：数据库schema -> API端点 -> 测试；数据库schema -> 文档。
---

项目任务依赖关系（持久）：
- 任务ID 28f6a0c0-7bab-4bc1-b1f2-50aa0f9fa758: setup database schema（描述：Design and set up the database schema. 无前置依赖）
- 任务ID b461b75b-695b-40e6-aaf4-d89c5af6de95: create API endpoints（描述：Create API endpoints. Depends on the database schema. 被 setup database schema 阻塞）
- 任务：write tests（被 create API endpoints 阻塞）
- 任务：write docs（被 setup database schema 阻塞）