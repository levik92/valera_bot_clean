from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage 

from database import db_manager
from middlewares import setup_middlewares
from handlers import setup_routers


def create_dispatcher() -> Dispatcher:
    storage = MemoryStorage()
    dp = Dispatcher(
        storage=storage,
        session_pool=db_manager.session_maker
    )
    
    setup_middlewares(dp)
    setup_routers(dp)

    return dp