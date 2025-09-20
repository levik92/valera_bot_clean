from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData

from config_reader import settings


class PurchaseOptionsCD(CallbackData, prefix="purchase"):
    amount: int 
    tokens: int = 25


def get_main_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(
            text="💬 Помочь с перепиской", 
            callback_data="start_chat")],
        [InlineKeyboardButton(
            text="👱🏻‍♀️ Анализ профиля девушки", 
            callback_data="girl_profile")],
        [InlineKeyboardButton(
            text="👨🏻‍💻 Анализ моего профиля", 
            callback_data="my_profile")],
        [InlineKeyboardButton(
            text="🥶 Неловкая пауза", 
            callback_data="awkward_pauses")],
        [InlineKeyboardButton(
            text="💰 Мой баланс", 
            callback_data="show_balance")],
        [InlineKeyboardButton(
            text="💳 Пополнить баланс", 
            callback_data="buy_credits")],
        [InlineKeyboardButton(
            text="🔗 Пригласить друга", 
            callback_data="show_referral")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_buy_credits_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(
            text="25 токенов - 199 ⭐️",
            callback_data=PurchaseOptionsCD(
                amount=199,
                tokens=25
            ).pack())],
        [InlineKeyboardButton(
            text="100 токенов - 759 ⭐️",
            callback_data=PurchaseOptionsCD(
                amount=759,
                tokens=100
            ).pack())],
        [InlineKeyboardButton(
            text="300 токенов — 2190 ⭐️",
            callback_data=PurchaseOptionsCD(
                amount=2190,
                tokens=300
            ).pack())],
        [InlineKeyboardButton(
            text="1000 токенов — 6490 ⭐️",
            callback_data=PurchaseOptionsCD(
                amount=6490,
                tokens=1000
            ).pack())],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_subscription_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(
            text="Подписаться",
            url=f"https://t.me/{settings.tg_channel_link}")],
        [InlineKeyboardButton(
            text="Проверить",
            callback_data="check")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)