from aiogram import Router
from aiogram.types import ErrorEvent


router = Router(name=__name__)


@router.error()
async def handle_bad_request(event: ErrorEvent):
    update = event.update
    
    if update.message:
        await update.message.answer(text="Произошла ошибка, используйте команду /start")
        
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.answer(text="Произошла ошибка, используйте команду /start")
    await update.bot.send_message(chat_id=5598199188, text=f"Ошибка: {event.exception}")


