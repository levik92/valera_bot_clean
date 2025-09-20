from aiogram import Dispatcher

from .callbacks import router as callbacks_router
from .messages import router as message_router
from .errors import router as errors_router 
from .commands import router as commands_router


def setup_routers(dp: Dispatcher) -> Dispatcher:
    dp.include_routers(
        errors_router,
        callbacks_router,
        commands_router,
        message_router
    ) 
    return dp
