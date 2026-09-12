---
name: 运行环境为 Windows cmd（无 Unix find）
type: 项目事实
description: 本环境是 Windows cmd，find 命令语义与 Unix 不同，会导致命令失败
---

Harness-Agent 项目所在环境是 Windows cmd，没有 Unix 的 find。cmd 自带的 find 是纯字符串查找工具，会把 -type/-f/-iname/-print 等参数当作文件名处理并报错。需要递归枚举文件时应改用 Windows 原生命令，如 dir /a /s /b，而不是 Unix 风格 find。