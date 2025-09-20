from typing import Callable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database import requests


class RequestsCounterMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Any],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        session: AsyncSession = data['session']

        user = await requests.get_user(
            session, 
            event.from_user.id
        )
        if not user:
            return await handler(event, data)
        if user.requests <= 0:
            await event.answer(
                "У вас закончились запросы! Чтобы их пополнить, купите пакет токенов"
            )
            return
        return await handler(event, data)
