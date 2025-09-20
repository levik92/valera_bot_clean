from aiogram import Bot, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database import requests
from keyboards import get_main_kb


router = Router()


@router.message(CommandStart())
async def start(
    message: Message, 
    bot: Bot,
    command: CommandObject,
    session: AsyncSession,
    state: FSMContext
):
    await state.clear()
    user = await requests.get_user(
        session, 
        message.from_user.id
    )
    if not user:
        user = await requests.add_user(
            session,
            message.from_user.id,
            message.from_user.first_name,
            message.from_user.username,
        )
    if command.args:
        option, value = command.args.split("_")
        match option:
            case "r":
                try:
                    inviter_id = int(value)
                except ValueError:
                    return None
                warning_text = "Произошла ошибка. Пожалуйста, перезапустите бота командой /start"
                inviter = await requests.get_user(
                    session,
                    inviter_id
                )
                if not inviter:
                    return await message.answer(warning_text)
                
                guest = await requests.get_referral(
                    session,
                    user.tg_id,
                    inviter_id,
                )
                if guest:
                    return await message.answer(warning_text)
                if inviter.tg_id == user.tg_id:
                    return await message.answer(warning_text)

                await requests.add_referral(
                    session,
                    inviter_id,
                    user.tg_id,
                )
                await bot.send_message(
                    inviter.tg_id, "Вы успешно пригласили друга и получаете +10 токенов"
                )
                await requests.update_user_requests(
                    session,
                    inviter.tg_id,
                    10
                )
                await requests.update_user_requests(
                    session,
                    user.tg_id,
                    10
                )
                await message.answer("Вы стали рефералом! В награду вы получаете +10 токенов")
                return
    await message.answer(
    f"""
Ну что ж, {message.from_user.first_name}! Я Валера, твой персональный тренер по соблазнению и отношениям. 
Я помогу проанализировать переписку, анкету девушки и помочь классно продолжить беседу и понять что к чему. Даже помогу заполнить неловкие паузы во время беседы либо подскажу как улучшить твою анкету! 
Выбери ниже, что тебе интересно либо просто напиши в чат, что тебя волнует:
    """,
        reply_markup=get_main_kb()
    )