from __future__ import annotations

import secrets
from typing import Any

from database import get_db

# 活跃会话存储: token -> 用户信息
active_sessions: dict[str, dict[str, Any]] = {}


def login(username: str, password: str) -> str | None:
    """验证用户名密码，成功则返回 token，失败返回 None。"""
    conn = get_db()
    try:
        cursor = conn.execute(
            "SELECT id, username, role, display_name FROM users WHERE username = ? AND password = ?",
            (username, password),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        user_info = {
            "id": row["id"],
            "username": row["username"],
            "role": row["role"],
            "display_name": row["display_name"],
        }

        # 生成随机 token 并存储会话
        token = secrets.token_hex(32)
        active_sessions[token] = user_info
        return token
    finally:
        conn.close()


def verify_token(token: str) -> dict[str, Any] | None:
    """验证 token，返回用户信息或 None。"""
    return active_sessions.get(token)


def logout(token: str) -> None:
    """清除指定 token 的会话。"""
    active_sessions.pop(token, None)
