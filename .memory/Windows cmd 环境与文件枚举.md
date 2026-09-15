---
name: Windows cmd 环境与文件枚举
type: 项目事实
description: 环境为 Windows cmd，无 Unix find，递归枚举用 dir /a /s /b。
---

Harness-Agent 项目所在环境是 Windows cmd，没有 Unix 的 find。cmd 自带的 find 是纯字符串查找工具，会把 -type/-f/-iname/-print 等参数当文件名并报错。递归枚举文件应使用 Windows 原生命令，如 dir /a /s /b，而不是 Unix 风格 find。