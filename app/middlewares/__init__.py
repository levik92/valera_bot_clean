from aiogram import Dispatcher
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from aiogram.utils.chat_action import ChatActionMiddleware

from database import db_manager
from config_reader import settings
from .requests_counter import RequestsCounterMiddleware
from .subscription_check import ChannelSubscriptionMiddleware
from .db import DBMiddleware


def setup_middlewares(dp: Dispatcher): 
    dp.callback_query.middleware(CallbackAnswerMiddleware())
    dp.message.middleware(RequestsCounterMiddleware())
    dp.message.middleware(ChannelSubscriptionMiddleware(
        2432026169
    ))
    dp.message.middleware(ChatActionMiddleware())
    dp.callback_query.middleware(ChannelSubscriptionMiddleware(
        2432026169
    ))
    dp.update.middleware(DBMiddleware(db_manager.session_maker))
    return dp
    