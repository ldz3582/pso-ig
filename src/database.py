from __future__ import annotations

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "hfsp.db"


def get_db() -> sqlite3.Connection:
    """返回一个数据库连接，启用外键支持和字典行模式。"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """初始化数据库，创建表并插入默认管理员账号。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                display_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY,
                staff_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                department TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                position TEXT DEFAULT '',
                device_ids TEXT DEFAULT '[]',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 插入默认管理员账号（仅在不存在时）
        cursor = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            ("admin",),
        )
        if cursor.fetchone() is None:
            conn.execute(
                "INSERT INTO users (username, password, role, display_name) VALUES (?, ?, ?, ?)",
                ("admin", "admin123", "admin", "管理员"),
            )

        conn.commit()
    finally:
        conn.close()
