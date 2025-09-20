from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery, LabeledPrice
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database import requests
from keyboards import get_main_kb, get_buy_credits_kb, PurchaseOptionsCD
from config_reader import settings
from states import CommunicationSG


router = Router()


@router.callback_query(F.data == "start_chat")
async def start_chat(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer()
    await callback.message.answer(
        "Ок! Пришли переписку — текстом или скринами. Я помогу понять, как она к тебе относится, и предложу лучшие ответы.",
    )
    await state.set_state(CommunicationSG.correspondence)


@router.callback_query(F.data == "girl_profile")
async def girl_profile(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer()
    await callback.message.answer(
        "Пришли анкету девушки: текст или фото. Я расскажу, какая она, чем увлекается и как лучше завести разговор.",
    )
    await state.set_state(CommunicationSG.girl_analysis)


@router.callback_query(F.data == "my_profile")
async def my_profile(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer()
    await callback.message.answer(
        "Давай посмотрим на твой профиль. Пришли текст или фото, и я скажу, что супер, а что можно подтянуть.",
    )
    await state.set_state(CommunicationSG.my_analysis)


@router.callback_query(F.data == "awkward_pauses")
async def awkward_pauses(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer()
    await callback.message.answer(
        "Опиши, где вы сейчас (чат или свидание) и что обсуждали. Я подкину темы, чтобы заполнить паузу и поддержать вайб.",
    )
    await state.set_state(CommunicationSG.pause)


@router.callback_query(F.data == "check")
async def check_sub(
    callback: CallbackQuery,
    bot: Bot
):
    info = await bot.get_chat_member(
        f"@{settings.tg_channel_link}",
        callback.from_user.id
    )
    if info.status == "left":
        await callback.answer(
            "Вы не подписаны на канал!",
            show_alert=True
        )
        return
    await callback.answer()
    await callback.message.answer("Благодарю за подписку! Теперь можем общаться полноценно 😉")


@router.callback_query(F.data == "buy_credits")
async def buy_credits(
    callback: CallbackQuery,
):
    await callback.answer()
    await callback.message.answer(
        "Выбери пакет для пополнения баланса:",
        reply_markup=get_buy_credits_kb()
    )


@router.callback_query(PurchaseOptionsCD.filter())
async def buy_credits(
    callback: CallbackQuery,
    callback_data: PurchaseOptionsCD,
):
    await callback.answer()
    await callback.message.answer_invoice(
        f"Пакет на {callback_data.tokens} токенов",
        f"Пополнение баланса: Пакет на {callback_data.tokens} токенов",
        payload=f"{callback_data.amount}_{callback_data.tokens}",
        provider_token=settings.provider_token,
        currency="XTR",
        prices=[LabeledPrice(label="XTR", amount=callback_data.amount)]
    )


@router.callback_query(F.data == "show_balance")
async def show_balance(
    callback: CallbackQuery,
    session: AsyncSession,
):
    await callback.answer()
    user = await requests.get_user(session, callback.from_user.id)
    await callback.message.answer(
        f"""
💰 Твой баланс: {user.requests} токен(ов).
1 токен = 1 ответ Валеры.

🎁 Пригласи друга и вы оба получите +10 токенов!

🔗 Чтобы узнать свою персональную ссылку, перейди в раздел «Пригласить друга».
        """
    )


@router.callback_query(F.data == "show_referral")
async def show_referral(
    callback: CallbackQuery,
    bot: Bot
):
    await callback.answer()
    info = await bot.get_me()
    await callback.message.answer(
        "🔗 Твоя персональная реферальная ссылка:\n"
        f"https://t.me/{info.username}?start=r_{callback.from_user.id}\n\n"
        "Пригласи друга и вы оба получите +10 токенов!"
    )
