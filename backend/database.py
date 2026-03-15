"""
Database module — SQLite via aiosqlite.
Tables: users, reddit_tokens, posts, scheduled_jobs, subreddits
"""

import aiosqlite
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """Create all tables if they don't exist."""
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS reddit_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_type TEXT DEFAULT 'bearer',
                expires_at REAL,
                scope TEXT,
                reddit_username TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                platform TEXT DEFAULT 'reddit',
                status TEXT DEFAULT 'draft',
                -- status: draft | pending | approved | scheduled | published | failed
                target_subreddits TEXT,
                -- JSON array of subreddit names
                tags TEXT,
                original_idea TEXT,
                ai_model TEXT,
                ai_prompt_used TEXT,
                published_urls TEXT,
                -- JSON array of reddit URLs after publishing
                error_log TEXT,
                scheduled_at TEXT,
                published_at TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS scheduled_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                subreddit TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                -- pending | running | completed | failed
                result_url TEXT,
                error TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (post_id) REFERENCES posts(id)
            );

            CREATE TABLE IF NOT EXISTS subreddits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT,
                subscribers INTEGER,
                description TEXT,
                is_joined INTEGER DEFAULT 0,
                discovered_at TEXT DEFAULT (datetime('now'))
            );
        """)
        await db.commit()
    finally:
        await db.close()


# ── Token helpers ──

async def save_reddit_token(token_data: dict):
    db = await get_db()
    try:
        # Upsert: delete old, insert new
        await db.execute("DELETE FROM reddit_tokens")
        await db.execute(
            """INSERT INTO reddit_tokens
               (access_token, refresh_token, token_type, expires_at, scope, reddit_username)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                token_data["access_token"],
                token_data.get("refresh_token"),
                token_data.get("token_type", "bearer"),
                token_data.get("expires_at"),
                token_data.get("scope"),
                token_data.get("reddit_username"),
            ),
        )
        await db.commit()
    finally:
        await db.close()


async def get_reddit_token():
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM reddit_tokens ORDER BY id DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await db.close()


# ── Post helpers ──

async def create_post(data: dict) -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO posts
               (title, body, platform, status, target_subreddits, tags,
                original_idea, ai_model, ai_prompt_used)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["title"],
                data["body"],
                data.get("platform", "reddit"),
                data.get("status", "pending"),
                json.dumps(data.get("target_subreddits", [])),
                json.dumps(data.get("tags", [])),
                data.get("original_idea", ""),
                data.get("ai_model", ""),
                data.get("ai_prompt_used", ""),
            ),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_posts(status: str = None) -> list:
    db = await get_db()
    try:
        if status:
            cursor = await db.execute(
                "SELECT * FROM posts WHERE status = ? ORDER BY created_at DESC", (status,)
            )
        else:
            cursor = await db.execute("SELECT * FROM posts ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_post(post_id: int) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def update_post(post_id: int, data: dict):
    db = await get_db()
    try:
        sets = []
        vals = []
        for key, val in data.items():
            if key in ("title", "body", "status", "target_subreddits", "tags",
                       "published_urls", "error_log", "scheduled_at", "published_at"):
                sets.append(f"{key} = ?")
                if key in ("target_subreddits", "tags", "published_urls"):
                    vals.append(json.dumps(val) if isinstance(val, list) else val)
                else:
                    vals.append(val)
        sets.append("updated_at = ?")
        vals.append(datetime.utcnow().isoformat())
        vals.append(post_id)
        await db.execute(
            f"UPDATE posts SET {', '.join(sets)} WHERE id = ?", vals
        )
        await db.commit()
    finally:
        await db.close()


async def delete_post(post_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        await db.execute("DELETE FROM scheduled_jobs WHERE post_id = ?", (post_id,))
        await db.commit()
    finally:
        await db.close()


# ── Scheduled job helpers ──

async def create_scheduled_job(post_id: int, subreddit: str, scheduled_time: str) -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO scheduled_jobs (post_id, subreddit, scheduled_time)
               VALUES (?, ?, ?)""",
            (post_id, subreddit, scheduled_time),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def update_scheduled_job(job_id: int, data: dict):
    db = await get_db()
    try:
        sets = []
        vals = []
        for key, val in data.items():
            if key in ("status", "result_url", "error"):
                sets.append(f"{key} = ?")
                vals.append(val)
        vals.append(job_id)
        if sets:
            await db.execute(
                f"UPDATE scheduled_jobs SET {', '.join(sets)} WHERE id = ?", vals
            )
            await db.commit()
    finally:
        await db.close()


async def get_jobs_for_post(post_id: int) -> list:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM scheduled_jobs WHERE post_id = ? ORDER BY scheduled_time",
            (post_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_pending_jobs() -> list:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM scheduled_jobs WHERE status = 'pending' ORDER BY scheduled_time"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


# ── Subreddit helpers ──

async def save_subreddits(subs: list[dict]):
    db = await get_db()
    try:
        for s in subs:
            await db.execute(
                """INSERT OR REPLACE INTO subreddits
                   (name, display_name, subscribers, description)
                   VALUES (?, ?, ?, ?)""",
                (s["name"], s.get("display_name", s["name"]),
                 s.get("subscribers", 0), s.get("description", "")),
            )
        await db.commit()
    finally:
        await db.close()


async def get_saved_subreddits() -> list:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM subreddits ORDER BY subscribers DESC"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def mark_subreddit_joined(name: str, joined: bool = True):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE subreddits SET is_joined = ? WHERE name = ?",
            (1 if joined else 0, name),
        )
        await db.commit()
    finally:
        await db.close()
