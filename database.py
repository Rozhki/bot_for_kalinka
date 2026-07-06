import os
from datetime import datetime

import aiosqlite

DB_PATH = os.path.join("data", "requests.db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    username TEXT,
    full_name TEXT NOT NULL,
    department TEXT NOT NULL,
    problem_type TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Новая',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

STATUSES = ("Новая", "В работе", "Выполнена", "Отменена")


async def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(CREATE_TABLE_SQL)

        # Создаёт колонку username в базе в случае, если она отсутствует
        cursor = await conn.execute("PRAGMA table_info(requests)")
        existing_columns = {row[1] for row in await cursor.fetchall()}
        if "username" not in existing_columns:
            await conn.execute("ALTER TABLE requests ADD COLUMN username TEXT")

        await conn.commit()


async def create_request(
    telegram_id: int,
    full_name: str,
    department: str,
    problem_type: str,
    description: str,
    priority: str,
    username: str | None = None,
) -> int:
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            """
            INSERT INTO requests
                (telegram_id, username, full_name, department, problem_type,
                 description, priority, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Новая', ?, ?)
            """,
            (
                telegram_id,
                username,
                full_name,
                department,
                problem_type,
                description,
                priority,
                now,
                now,
            ),
        )
        await conn.commit()
        return cursor.lastrowid


async def get_user_requests(telegram_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM requests WHERE telegram_id = ? ORDER BY id DESC",
            (telegram_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_all_requests(status: str | None = None) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        if status:
            cursor = await conn.execute(
                "SELECT * FROM requests WHERE status = ? ORDER BY id DESC",
                (status,),
            )
        else:
            cursor = await conn.execute("SELECT * FROM requests ORDER BY id DESC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_request_by_id(request_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_status(request_id: int, new_status: str) -> None:
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE requests SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, request_id),
        )
        await conn.commit()


async def get_statistics() -> dict:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        stats: dict = {}

        cursor = await conn.execute("SELECT COUNT(*) AS cnt FROM requests")
        stats["total"] = (await cursor.fetchone())["cnt"]

        for status in STATUSES:
            cursor = await conn.execute(
                "SELECT COUNT(*) AS cnt FROM requests WHERE status = ?", (status,)
            )
            stats[status] = (await cursor.fetchone())["cnt"]

        cursor = await conn.execute(
            "SELECT problem_type, COUNT(*) AS cnt FROM requests GROUP BY problem_type"
        )
        rows = await cursor.fetchall()
        stats["by_type"] = {row["problem_type"]: row["cnt"] for row in rows}

        return stats
