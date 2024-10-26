import aiosqlite
import datetime
from typing import List, Dict, Optional


class Database:
    def __init__(self, db_name: str = "feedback.db"):
        self.db_name = db_name

    async def init(self):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    registration_date TEXT,
                    is_blocked INTEGER DEFAULT 0
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_id INTEGER,
                    to_id INTEGER,
                    message TEXT,
                    date TEXT,
                    is_read INTEGER DEFAULT 0
                )
            """)
            await db.commit()

    async def add_user(self, user_id: int, username: str, full_name: str) -> None:
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, full_name, registration_date) VALUES (?, ?, ?, ?)",
                (user_id, username, full_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            await db.commit()

    async def get_user_info(self, user_id: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                    "SELECT user_id, username, full_name, registration_date FROM users WHERE user_id = ?",
                    (user_id,)
            ) as cursor:
                user = await cursor.fetchone()
                if user:
                    return {
                        "user_id": user[0],
                        "username": user[1],
                        "full_name": user[2],
                        "registration_date": user[3]
                    }
                return None

    async def add_message(self, from_id: int, to_id: int, message: str) -> None:
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "INSERT INTO messages (from_id, to_id, message, date) VALUES (?, ?, ?, ?)",
                (from_id, to_id, message, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            await db.commit()

    async def get_dialog_history(self, user_id: int, admin_id: int, limit: int = 10, offset: int = 0) -> List[Dict]:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                    """
                    SELECT m.*, u.username, u.full_name 
                    FROM messages m
                    JOIN users u ON m.from_id = u.user_id
                    WHERE (m.from_id = ? AND m.to_id = ?) OR (m.from_id = ? AND m.to_id = ?)
                    ORDER BY m.date DESC LIMIT ? OFFSET ?
                    """,
                    (user_id, admin_id, admin_id, user_id, limit, offset)
            ) as cursor:
                messages = await cursor.fetchall()
                return [
                    {
                        "id": msg[0],
                        "from_id": msg[1],
                        "to_id": msg[2],
                        "message": msg[3],
                        "date": msg[4],
                        "is_read": msg[5],
                        "username": msg[6],
                        "full_name": msg[7]
                    }
                    for msg in messages
                ]

    async def get_all_dialogs(self, admin_id: int) -> List[Dict]:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                    """
                    SELECT DISTINCT u.user_id, u.username, u.full_name
                    FROM messages m
                    JOIN users u ON (m.from_id = u.user_id OR m.to_id = u.user_id)
                    WHERE m.from_id = ? OR m.to_id = ?
                    """,
                    (admin_id, admin_id)
            ) as cursor:
                dialogs = await cursor.fetchall()
                return [
                    {
                        "user_id": dialog[0],
                        "username": dialog[1],
                        "full_name": dialog[2]
                    }
                    for dialog in dialogs
                ]

    async def block_user(self, user_id: int) -> None:
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,))
            await db.commit()

    async def is_user_blocked(self, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT is_blocked FROM users WHERE user_id = ?", (user_id,)) as cursor:
                result = await cursor.fetchone()
                return bool(result and result[0])


db = Database()
async def init_db():
    await db.init()