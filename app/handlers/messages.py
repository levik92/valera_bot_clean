from aiogram import Bot, Router, F
from aiogram.types import PreCheckoutQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database import requests
from states import CommunicationSG
from utils import analyze_photo, chat_with_gpt
from config_reader import settings


router = Router()


@router.pre_checkout_query()
async def process_pre_checkout_query(
    pre_checkout_query: PreCheckoutQuery,
):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def star_payment(
    message: Message, 
    session: AsyncSession
):
    payload = message.successful_payment.invoice_payload
    amount, tokens = payload.split("_")
    await message.answer(
        f"Платеж на сумму {amount} звезд зачислен! Вы получаете {tokens} токенов"
    )
    await requests.update_user_requests(
        session,
        message.from_user.id,
        int(tokens)
    )


@router.message(CommunicationSG.correspondence)
async def correspondence(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext
):
    if message.text:
        result = await chat_with_gpt(message.text)
        await message.answer(result)
    elif message.photo:
        await message.answer("Анализирую фото...")
        file = await bot.get_file(message.photo[-1].file_id)
        file_path = file.file_path
        photo_url = f"https://api.telegram.org/file/bot{settings.bot_token.get_secret_value()}/{file_path}"
        
        result = await analyze_photo(photo_url, message.caption)
        await message.answer(result)
    await requests.decrease_user_request(
        session,
        message.from_user.id,
    )
    


@router.message(CommunicationSG.girl_analysis)
async def correspondence(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext
):
    if message.text:
        result = await chat_with_gpt(message.text)
        await message.answer(result)
    elif message.photo:
        await message.answer("Анализирую фото...")
        file = await bot.get_file(message.photo[-1].file_id)
        file_path = file.file_path
        photo_url = f"https://api.telegram.org/file/bot{settings.bot_token.get_secret_value()}/{file_path}"
        
        result = await analyze_photo(photo_url, message.caption)
        await message.answer(result)
    await requests.decrease_user_request(
        session,
        message.from_user.id,
    )
    


@router.message(CommunicationSG.my_analysis)
async def correspondence(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext
):
    if message.text:
        result = await chat_with_gpt(message.text)
        await message.answer(result)
    elif message.photo:
        await message.answer("Анализирую фото...")
        file = await bot.get_file(message.photo[-1].file_id)
        file_path = file.file_path
        photo_url = f"https://api.telegram.org/file/bot{settings.bot_token.get_secret_value()}/{file_path}"
        
        result = await analyze_photo(photo_url, message.caption)
        await message.answer(result)
    await requests.decrease_user_request(
        session,
        message.from_user.id,
    )
    


@router.message(CommunicationSG.pause)
async def correspondence(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext
):
    if not message.text:
        return
    
    result = await chat_with_gpt(message.text)
    await message.answer(result)
    await requests.decrease_user_request(
        session,
        message.from_user.id,
    )
    