"""Telegram bot handlers for Valera bot.

This module defines all the event handlers for user interactions. It relies on
`aiogram` version 3 and uses a simple state‑free approach: each message is
handled independently. User balances and referrals are managed in the database
module. OpenAI API calls are issued through the openai package.
"""

from __future__ import annotations

import asyncio
import re
import time
from typing import List, Optional

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.formatting import Bold

import openai

from .config import get_settings, Settings
from .db import Database
from .logic import build_messages


# In‑memory rate‑limiting store: maps user_id to last usage timestamp
_last_usage: dict[int, float] = {}


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Return the reply keyboard used by the bot."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Запустить Валеру")],
            [KeyboardButton(text="💰 Мой баланс"), KeyboardButton(text="ℹ️ Инструкция")],
            [KeyboardButton(text="💳 Пополнить")],
        ],
        resize_keyboard=True,
    )


async def handle_start(message: types.Message, db: Database, settings: Settings) -> None:
    """Handle the /start command. Registers the user and processes referrals."""
    user_id = message.from_user.id
    # Extract referrer ID from start payload (e.g. /start 12345)
    referrer_id: Optional[int] = None
    if message.text:
        parts = message.text.strip().split()
        if len(parts) >= 2 and parts[1].isdigit():
            referrer_id = int(parts[1])
    # Ensure user exists in DB
    await db.ensure_user(user_id, referrer_id)
    # Compose the greeting
    text = (
        "Привет! Я Валера, твой виртуальный помощник.\n"
        f"У тебя на счету {settings.start_bonus} токенов для начала.\n"
        "Используй меню ниже, чтобы начать."
    )
    await message.answer(text, reply_markup=get_main_keyboard())


async def handle_balance(message: types.Message, db: Database) -> None:
    """Send the user's current token balance."""
    user_id = message.from_user.id
    user = await db.ensure_user(user_id)
    balance = user["balance"]
    await message.answer(f"На твоём счету {balance} токенов.")


async def handle_instruction(message: types.Message) -> None:
    """Send usage instructions."""
    await message.answer(
        "Отправь мне текст, ссылку на изображение или фотографию, и я сгенерирую ответ.\n"
        "Каждая генерация стоит 1 токен.\n"
        "Ты можешь получить дополнительные токены, поделившись реферальной ссылкой: \n"
        "<code>/start {your_id}</code> — поменяй {your_id} на свой ID.",
        parse_mode="HTML",
    )


async def handle_top_up(message: types.Message) -> None:
    """Instruct user on how to top up tokens."""
    await message.answer(
        "Чтобы пополнить баланс, свяжитесь с владельцем бота."
    )


async def handle_generate(message: types.Message, bot: Bot, db: Database, settings: Settings) -> None:
    """Handle a user prompt and produce a response via OpenAI API."""
    user_id = message.from_user.id
    # Check allowed users if specified
    if settings.allowed_user_ids and user_id not in settings.allowed_user_ids:
        await message.answer("Извините, вам запрещено пользоваться этим ботом.")
        return
    # Cooldown check
    last_time = _last_usage.get(user_id, 0)
    now = time.time()
    if now - last_time < settings.cooldown_seconds:
        remaining = int(settings.cooldown_seconds - (now - last_time))
        await message.answer(f"Подождите {remaining} сек. перед следующей генерацией.")
        return
    _last_usage[user_id] = now
    # Ensure user exists
    user = await db.ensure_user(user_id)
    if user["balance"] < settings.generate_cost:
        await message.answer("Недостаточно токенов. Пополните баланс.")
        return
    # Build image links if any photos were sent
    image_links: List[str] = []
    # Telegram sends photos in message.photo for images; attachments from other sources may be in document
    if message.photo:
        # choose the highest resolution available (last in list)
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        image_url = f"https://api.telegram.org/file/bot{settings.bot_token}/{file.file_path}"
        image_links.append(image_url)
    # Extract image URLs from entities or plain text
    url_pattern = re.compile(r"https?://\\S+")
    if message.text:
        for url in url_pattern.findall(message.text):
            if any(url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                image_links.append(url)
    prompt = message.caption if message.caption else message.text or ""
    # Build the message payload for OpenAI
    chat_messages = build_messages(prompt, image_links)
    # Deduct cost pre‑emptively
    await db.update_balance(user_id, -settings.generate_cost)
    # Perform the API call
    try:
        completion = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=chat_messages,
            max_tokens=512,
            temperature=0.7,
        )
        reply_content = completion.choices[0].message.content.strip()
    except Exception as e:
        # Refund on failure
        await db.update_balance(user_id, settings.generate_cost)
        await message.answer("Произошла ошибка при обращении к OpenAI API. Попробуйте снова позже.")
        return
    # Mark first generation and apply referral bonus
    if not await db.has_generated_before(user_id):
        await db.set_first_generated(user_id)
        ref_id = await db.get_referrer(user_id)
        if ref_id:
            await db.update_balance(ref_id, settings.ref_bonus)
            await db.update_balance(user_id, settings.ref_bonus)
    # Send the reply
    await message.answer(reply_content)


def register_handlers(dp: Dispatcher, bot: Bot, db: Database, settings: Settings) -> None:
    """Register all handlers to the dispatcher."""
    # /start command
    dp.message.register(
        lambda msg: handle_start(msg, db, settings),
        F.text.startswith("/start"),
    )
    # Balance
    dp.message.register(
        lambda msg: handle_balance(msg, db),
        F.text == "💰 Мой баланс",
    )
    # Instruction
    dp.message.register(
        handle_instruction,
        F.text == "ℹ️ Инструкция",
    )
    # Top up
    dp.message.register(
        handle_top_up,
        F.text == "💳 Пополнить",
    )
    # Any other text or photo triggers generation
    dp.message.register(
        lambda msg: handle_generate(msg, bot, db, settings)
    )
