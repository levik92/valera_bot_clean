from typing import Callable, Dict, Any, Union

from aiogram import Bot, BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from config_reader import settings
from keyboards import get_subscription_kb


class ChannelSubscriptionMiddleware(BaseMiddleware):
    def __init__(self, channel_id: int):
        self.channel_id = channel_id

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Any],
            event: Union[Message, CallbackQuery, TelegramObject],
            data: Dict[str, Any],
    ) -> Any:
        bot: Bot = data['bot']
        
        status = await bot.get_chat_member(
            chat_id=f"@{settings.tg_channel_link}", 
            user_id=event.from_user.id
        )
        if isinstance(event, Message):
            if event.text == "/start":
                return await handler(event, data)
        if status.status != "left":
            return await handler(event, data)
        else:
            if isinstance(event, CallbackQuery):
                if event.data == "check":
                    return await handler(event, data)
                else:
                    await event.answer()
                    return await event.message.answer(
                        f"Перед тем как я тебе помогу, подпишись на мой канал и мы продолжим @{settings.tg_channel_link}",
                        reply_markup=get_subscription_kb()
                    )
            return await event.answer(
                f"Перед тем как я тебе помогу, подпишись на мой канал и мы продолжим @{settings.tg_channel_link}",
                reply_markup=get_subscription_kb()
            )
 