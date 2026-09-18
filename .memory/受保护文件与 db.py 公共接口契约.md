---
name: 受保护文件与 db.py 公共接口契约
type: 项目事实
description: db.py/schema.sql/verify_schema.py 受保护；db.py 公共接口与行为不得改变。
---

重构时 notesapi/db.py、notesapi/schema.sql、notesapi/verify_schema.py 为受保护文件，改动前需建立 sha256 基线，收口时比对确认未变。db.py 对外公共接口 get_connection / init_db / reset_db 的参数名、默认值、返回类型必须完全不变（参数名 db_path、identity 默认值、返回注解 sqlite3.Connection）；模块级常量 DEFAULT_DB_PATH 必须向后兼容。内部约定：连接集中创建，开启 SQLite 外键 PRAGMA foreign_keys = ON，row_factory 使用 sqlite3.Row；HERE 为模块目录绝对路径，SCHEMA_PATH = HERE/schema.sql。schema.sql 为 SQLite DDL，含 users、notes、tags、note_tags、schema_migrations 表，含 CHECK 约束、lower(email) 唯一索引、外键 ON DELETE CASCADE，DDL 幂等，schema_migrations 以毫秒级时间戳记录版本。verify_schema.py 是脚本式 smoke check（非 pytest），用内存 SQLite 校验约束与级联真正生效。任何重构不得改变对外行为。