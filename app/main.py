"""Entry point for the Valera bot.

This module initialises the configuration, database, bot and dispatcher, then
starts polling. It is designed to run on platforms like Heroku where a
single process runs an asynchronous event loop.
"""

from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
import openai

from .config import get_settings
from .db import Database
from .handlers import register_handlers


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    if not settings.openai_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    openai.api_key = settings.openai_key
    # Create DB and bot
    db = Database(settings)
    await db.connect()
    bot = Bot(token=settings.bot_token, parse_mode="HTML")
            # Delete webhook to ensure polling works
        await bot.delete_webhook(drop_pending_updates=True)

    dp = Dispatcher()
    register_handlers(dp, bot, db, settings)
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
