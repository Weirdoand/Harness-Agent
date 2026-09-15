-- Notes API — database schema
-- Target engine: SQLite 3 (foreign keys enabled per-connection).
-- Idempotent: safe to run repeatedly.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- schema_migrations: tracks which schema versions have been applied.
-- ---------------------------------------------------------------------------
-- Timestamps use millisecond precision (%f) so that an update occurring in the
-- same wall-clock second as the insert is still observable.
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- ---------------------------------------------------------------------------
-- users
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT    NOT NULL,
    name        TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CONSTRAINT ck_users_email CHECK (length(trim(email)) > 0)
);
-- Case-insensitive uniqueness for emails.
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_lower ON users (lower(email));

-- ---------------------------------------------------------------------------
-- notes  (one user -> many notes)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    title       TEXT    NOT NULL,
    body        TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CONSTRAINT ck_notes_title CHECK (length(trim(title)) > 0)
);
CREATE INDEX IF NOT EXISTS ix_notes_user_id    ON notes (user_id);
CREATE INDEX IF NOT EXISTS ix_notes_created_at ON notes (created_at DESC);

-- ---------------------------------------------------------------------------
-- tags
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_tags_name_lower ON tags (lower(name));

-- ---------------------------------------------------------------------------
-- note_tags  (many-to-many between notes and tags)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS note_tags (
    note_id     INTEGER NOT NULL REFERENCES notes (id) ON DELETE CASCADE,
    tag_id      INTEGER NOT NULL REFERENCES tags  (id) ON DELETE CASCADE,

    PRIMARY KEY (note_id, tag_id)
);
CREATE INDEX IF NOT EXISTS ix_note_tags_tag_id ON note_tags (tag_id);

-- ---------------------------------------------------------------------------
-- updated_at maintenance
-- ---------------------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS trg_notes_set_updated_at
AFTER UPDATE OF title, body ON notes
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE notes
       SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
     WHERE id = NEW.id;
END;

-- ---------------------------------------------------------------------------
-- Record this migration.
-- ---------------------------------------------------------------------------
INSERT OR IGNORE INTO schema_migrations (version) VALUES (1);
