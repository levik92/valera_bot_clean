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
# from functools import partial  # partial is unused now and kept commented out for future reference
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.formatting import Bold
from aiogram.filters import CommandStart

import openai

from .config import get_settings, Settings
from .db import Database
from .logic import build_messages


# In‑memory rate‑limiting store: maps user_id to last usage timestamp
_last_usage: dict[int, float] = {}

# Map of users to pending action type. When a user selects a menu command that
# requires additional input (e.g. analysis of a chat or profile), we store the
# type here. The next message they send will be processed according to this
# action and then the entry will be removed.
pending_action: dict[int, str] = {}


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Return the reply keyboard used by the bot.

    The keyboard reflects the core features of Valera as described in the
    specification: analysis of chats, analysis of female profiles and your
    own profile, generating topics for conversation, checking balance and
    topping up, and inviting friends.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📨 Анализ переписки"), KeyboardButton(text="💃 Анкета девушки")],
            [KeyboardButton(text="🧑 Моя анкета"), KeyboardButton(text="🧊 Темы для разговора")],
            [KeyboardButton(text="💰 Баланс/Пополнить"), KeyboardButton(text="👥 Пригласить друга")],
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
        "Привет! Я Валера, твой тренер по соблазнению и общению.\n"
        f"У тебя на счету {settings.start_bonus} токенов для начала.\n"
        "Используй меню ниже, чтобы выбрать анализ переписки, анкет или темы для разговора."
    )
    await message.answer(text, reply_markup=get_main_keyboard())


async def handle_balance(message: types.Message, db: Database) -> None:
    """Send the user's current token balance."""
    user_id = message.from_user.id
    user = await db.ensure_user(user_id)
    balance = user["balance"]
    await message.answer(f"На твоём счету {balance} токенов.")


async def handle_instruction(message: types.Message) -> None:
    """
    Send usage instructions. Currently unused because the main menu options are self‑explanatory.
    This handler remains available in case a future button or command is added to display help.
    """
    await message.answer(
        "Выбери нужную функцию в меню: анализ переписки, анализ анкет или темы для разговора.\n"
        "После выбора функции пришли мне текст или фото, и я помогу. Каждая генерация стоит 1 токен.\n"
        "Дополнительные токены можно получить, пригласив друзей через реферальную ссылку.",
        parse_mode="HTML",
    )


async def handle_top_up(message: types.Message) -> None:
    """Instruct user on how to top up tokens. Deprecated: use handle_balance_topup instead."""
    await message.answer(
        "Чтобы пополнить баланс, используйте кнопку \"Баланс/Пополнить\" в меню."
    )

async def handle_balance_topup(message: types.Message, db: Database, settings: Settings) -> None:
    """
    Show the user's balance and provide information about available token packs
    and the cost in Telegram Stars. This handler combines balance checking and
    top‑up information as specified in the project requirements.
    """
    user_id = message.from_user.id
    user = await db.ensure_user(user_id)
    balance = user["balance"]
    tariff_text = (
        "Тарифы:\n"
        "⭐ 25 токенов — 199 ⭐\n"
        "⭐⭐ 100 токенов — 759 ⭐\n"
        "⭐⭐⭐ 300 токенов — 2190 ⭐\n"
        "👑 1000 токенов — 6490 ⭐"
    )
    await message.answer(
        f"На твоём счету {balance} токенов.\n\n{tariff_text}\n\n"
        "Чтобы пополнить баланс, воспользуйся встроенной оплатой Telegram Stars.",
        reply_markup=None,
    )


async def handle_invite(message: types.Message, bot: Bot, settings: Settings) -> None:
    """
    Provide the user with a personalised referral link. The link includes the
    user's ID as a start parameter so that both the inviter and invitee can
    receive bonus tokens after the invitee makes their first generation.
    """
    user_id = message.from_user.id
    # Retrieve the bot username via Bot.get_me().
    me = await bot.get_me()
    username = me.username
    link = f"https://t.me/{username}?start={user_id}"
    await message.answer(
        f"Пригласи друга по этой ссылке:\n{link}\n\n"
        f"Друг получит +{settings.ref_bonus} токенов после первой генерации, и ты тоже."
    )


async def handle_analyze_chat_command(message: types.Message) -> None:
    """
    Prepare to analyse a conversation. This sets a pending action for the
    current user. The next message they send (text or image) will be treated
    as the conversation to analyse.
    """
    user_id = message.from_user.id
    pending_action[user_id] = "conversation"
    await message.answer(
        "Пришли текст переписки или скриншот, и я дам анализ: расскажу, насколько она заинтересована,"
        " выделю намёки и предложу несколько вариантов ответа."
    )


async def handle_girl_profile_command(message: types.Message) -> None:
    """
    Prepare to analyse a girl's dating profile. Sets pending action to
    'girl_profile' so that the next message will be treated accordingly.
    """
    user_id = message.from_user.id
    pending_action[user_id] = "girl_profile"
    await message.answer(
        "Пришли анкету девушки (текст или фото), и я опишу её личность, интересы, стиль общения"
        " и предложу подход, который поможет вызвать её интерес."
    )


async def handle_my_profile_command(message: types.Message) -> None:
    """
    Prepare to analyse the user's own dating profile. Sets pending action to
    'my_profile'.
    """
    user_id = message.from_user.id
    pending_action[user_id] = "my_profile"
    await message.answer(
        "Отправь свою анкету (текст или скрин), я дам подробный разбор, оценку от 1 до 10"
        " и расскажу, что улучшить, чтобы она стала привлекательнее."
    )


async def handle_topics_command(message: types.Message) -> None:
    """
    Prepare to generate conversation topics. Sets pending action to 'topics'
    so that the next message will be used as optional context for the topic
    generation. If the user doesn't send any context, a generic list of
    flirty and fun topics will be generated.
    """
    user_id = message.from_user.id
    pending_action[user_id] = "topics"
    await message.answer(
        "Напиши пару слов о контексте (например, где вы общаетесь или что уже обсуждали),"
        " и я подкину флиртующие темы для разговора. Если контекст не нужен — пришли любое сообщение."
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
    url_pattern = re.compile(r"https?://\S+")
    if message.text:
        for url in url_pattern.findall(message.text):
            if any(url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                image_links.append(url)
    prompt = message.caption if message.caption else message.text or ""
    # Determine if the user has a pending action set via the menu. Pop it so
    # subsequent messages are treated normally.
    action = pending_action.pop(user_id, None)

    # Adjust the prompt based on the action to provide context and specific
    # instructions for the assistant. If there is no pending action, the
    # prompt is used as-is.
    if action == "conversation":
        # In the conversation scenario, instruct Valera to analyse the messages,
        # highlight interest and hints, offer several reply options and give
        # recommendations on how to develop the conversation.
        prompt_for_api = (
            f"Вот переписка:\n{prompt}\n\n"
            "1. Дай краткий анализ её ответов (о чём они говорят, насколько она заинтересована, есть ли намёки).\n"
            "2. Подготовь 2–3 варианта ответов и поясни, почему каждый вариант работает.\n"
            "3. Добавь комментарии, как развивать разговор дальше."
        )
    elif action == "girl_profile":
        prompt_for_api = (
            f"Вот анкета девушки:\n{prompt}\n\n"
            "Проанализируй её: опиши личность, интересы, стиль общения и подскажи, какой подход лучше использовать,"
            " чтобы вызвать её интерес и сблизиться."
        )
    elif action == "my_profile":
        prompt_for_api = (
            f"Вот моя анкета:\n{prompt}\n\n"
            "Дай подробный разбор (что хорошо, что плохо), поставь оценку по шкале от 1 до 10"
            " и предложи, что улучшить, чтобы анкета сильнее цепляла девушек."
        )
    elif action == "topics":
        context_part = f"{prompt}\n\n" if prompt else ""
        prompt_for_api = (
            f"{context_part}Подкинь лёгкие, флиртующие и интересные темы для онлайн или оффлайн общения,"
            " чтобы закрыть неловкие паузы и создать правильный вайб."
        )
    else:
        prompt_for_api = prompt
    # Build the message payload for OpenAI
    chat_messages = build_messages(prompt_for_api, image_links)
    # Deduct cost pre‑emptively
    await db.update_balance(user_id, -settings.generate_cost)
    # Perform the API call
    try:
        completion = await openai.ChatCompletion.acreate(
            model="gpt-5",
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
    """Register all handlers to the dispatcher.

    This function binds the required dependencies (database, bot instance and settings)
    to each handler via closures. Aiogram requires the registered handler to be a
    coroutine function; using functools.partial does not always propagate the coroutine
    metadata correctly, which can lead to unawaited coroutine warnings. Therefore we
    define simple wrapper coroutine functions that call the original handlers with
    the bound arguments. These wrappers are then registered with the dispatcher along
    with the appropriate message filters.
    """

    # Wrapper for the /start command to bind db and settings
    async def start_handler(message: types.Message) -> None:
        await handle_start(message, db=db, settings=settings)

    # There is no separate balance handler: balance and top‑up are handled together via
    # handle_balance_topup(). If a future dedicated balance button is added, a wrapper
    # similar to this can be created and registered.
    async def balance_handler(message: types.Message) -> None:  # pragma: no cover
        await handle_balance(message, db=db)

    # Wrapper for text/photo messages to bind bot, db, and settings
    async def generate_handler(message: types.Message) -> None:
        await handle_generate(message, bot=bot, db=db, settings=settings)
    # Register the command and button handlers with filters. The order matters: more specific
    # handlers should be registered before the generic generate_handler.
    dp.message.register(start_handler, CommandStart())
    )
    # Unified balance and top‑up handler triggered by the combined button
async def balance_topup_handler(message: types.Message) -> None:
    await handle_balance_topup(message, db=db, settings=settings)

async def invite_handler(message: types.Message) -> None:
    await handle_invite(message, bot=bot, settings=settings)

dp.message.register(balance_topup_handler, F.text == "💰 Баланс/Пополнить")
dp.message.register(invite_handler,        F.text == "👥 Пригласить друга")


    # Analyse chat
    dp.message.register(
        handle_analyze_chat_command,
        F.text == "📨 Анализ переписки",
    )
    # Analyse girl profile
    dp.message.register(
        handle_girl_profile_command,
        F.text == "💃 Анкета девушки",
    )
    # Analyse my profile
    dp.message.register(
        handle_my_profile_command,
        F.text == "🧑 Моя анкета",
    )
    # Generate topics
    dp.message.register(
        handle_topics_command,
        F.text == "🧊 Темы для разговора",
    )
    # Register generic generate handler without a filter so it catches all other messages
    dp.message.register(
        generate_handler,
    )
