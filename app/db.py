"""Database helper module for Valera bot.

This module provides a thin abstraction layer over SQLite (via aiosqlite) or
PostgreSQL (via asyncpg) depending on the presence of a DATABASE_URL.  It
contains helper methods to initialise the schema and manage user balances
and referrals.
"""

from __future__ import annotations

import os
from typing import Optional, Tuple, Union, Dict

import asyncio

import aiosqlite
import asyncpg

from .config import get_settings, Settings


class Database:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.database_url = settings.database_url
        self.is_postgres = bool(self.database_url and self.database_url.startswith("postgres"))
        # These will be initialised in `connect()`
        self.pool: Optional[asyncpg.Pool] = None
        self.sqlite: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Initialise the database connection and create tables if needed."""
        if self.is_postgres:
            self.pool = await asyncpg.create_pool(self.database_url)
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id BIGINT PRIMARY KEY,
                        balance INTEGER NOT NULL,
                        referrer_id BIGINT,
                        first_generated BOOLEAN DEFAULT FALSE
                    );
                    """
                )
        else:
            # default to a local sqlite database file
            db_path = os.path.join(os.path.dirname(__file__), "..", "database.db")
            self.sqlite = await aiosqlite.connect(db_path)
            await self.sqlite.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    balance INTEGER NOT NULL,
                    referrer_id INTEGER,
                    first_generated INTEGER DEFAULT 0
                );
                """
            )
            await self.sqlite.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self.pool:
            await self.pool.close()
        if self.sqlite:
            await self.sqlite.close()

    async def _fetch_one(self, query: str, params: Tuple = ()) -> Optional[Dict]:
        """Internal helper to execute a SELECT and return a single row."""
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *params)
                return dict(row) if row else None
        else:
            cur = await self.sqlite.execute(query, params)
            row = await cur.fetchone()
            if row is None:
                return None
            columns = [c[0] for c in cur.description]
            return {columns[i]: row[i] for i in range(len(columns))}

    async def _execute(self, query: str, params: Tuple = ()) -> None:
        """Internal helper to execute an INSERT/UPDATE/DELETE."""
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute(query, *params)
        else:
            await self.sqlite.execute(query, params)
            await self.sqlite.commit()

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Retrieve a user record or `None` if not present."""
        query = "SELECT id, balance, referrer_id, first_generated FROM users WHERE id = $1" if self.is_postgres else "SELECT id, balance, referrer_id, first_generated FROM users WHERE id = ?"
        params = (user_id,)
        return await self._fetch_one(query, params)

    async def create_user(self, user_id: int, referrer_id: Optional[int] = None) -> Dict:
        """Insert a new user with the starting bonus. Returns the created record."""
        # prevent self‑referral
        if referrer_id == user_id:
            referrer_id = None
        bonus = self.settings.start_bonus
        if self.is_postgres:
            query = "INSERT INTO users(id, balance, referrer_id, first_generated) VALUES($1, $2, $3, FALSE)"
            await self._execute(query, (user_id, bonus, referrer_id))
        else:
            query = "INSERT INTO users(id, balance, referrer_id, first_generated) VALUES(?, ?, ?, 0)"
            await self._execute(query, (user_id, bonus, referrer_id))
        return {
            "id": user_id,
            "balance": bonus,
            "referrer_id": referrer_id,
            "first_generated": False,
        }

    async def ensure_user(self, user_id: int, referrer_id: Optional[int] = None) -> Dict:
        """Get the user record, creating a new one if it doesn't exist."""
        user = await self.get_user(user_id)
        if user:
            return user
        return await self.create_user(user_id, referrer_id)

    async def update_balance(self, user_id: int, delta: int) -> None:
        """Adjust a user's balance by delta (can be positive or negative)."""
        if self.is_postgres:
            query = "UPDATE users SET balance = balance + $1 WHERE id = $2"
            params = (delta, user_id)
        else:
            query = "UPDATE users SET balance = balance + ? WHERE id = ?"
            params = (delta, user_id)
        await self._execute(query, params)

    async def set_first_generated(self, user_id: int) -> None:
        """Mark that the user has completed their first generation."""
        if self.is_postgres:
            query = "UPDATE users SET first_generated = TRUE WHERE id = $1"
        else:
            query = "UPDATE users SET first_generated = 1 WHERE id = ?"
        await self._execute(query, (user_id,))

    async def has_generated_before(self, user_id: int) -> bool:
        """Return True if the user has already generated once."""
        user = await self.get_user(user_id)
        if not user:
            return False
        fg = user.get("first_generated")
        # SQLite stores as 0/1; Postgres as bool
        return bool(fg)

    async def get_referrer(self, user_id: int) -> Optional[int]:
        """Return the referrer_id for a user, if any."""
        user = await self.get_user(user_id)
        if user:
            return user.get("referrer_id")
        return None
