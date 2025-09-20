from contextlib import suppress

from aiogram import Bot, Dispatcher

from factory import create_dispatcher, create_bot
from database import create_tables, db_manager


async def on_startup(bot: Bot):
    await create_tables()
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot started")


async def on_shutdown():
    await db_manager.dispose()
    print("Bot stopped")


def main():
    bot: Bot = create_bot()
    dp: Dispatcher = create_dispatcher()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.run_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )

     
if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        main()
