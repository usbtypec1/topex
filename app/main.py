import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    async_sessionmaker, AsyncEngine, create_async_engine,
)

from app import admin, user
from app.database.models import Base
from app.utils.sheets import (
    GetAllParcelData, GetMailingMessage, GetNewAdress,
    GetParcelsFromStorage, UpdateUserDataSheets,
)
from app.utils.strings import UpdateUserDiscount, UpdateUsersType
from config import load_config
from middlewares import DatabaseRepositoryMiddleware


async def scheduler_jobs(bot: Bot):
    await GetMailingMessage(bot)
    await asyncio.sleep(5)
    await GetAllParcelData(bot)
    await asyncio.sleep(5)
    await GetNewAdress()

    await UpdateUserDataSheets()
    await asyncio.sleep(5)
    await UpdateUserDiscount()
    await asyncio.sleep(5)
    await GetParcelsFromStorage(bot)


async def on_shutdown(dispatcher: Dispatcher):
    engine: AsyncEngine = dispatcher['engine']
    await engine.dispose()


async def main():
    logging.basicConfig(level=logging.INFO)

    engine = create_async_engine(
        "sqlite+aiosqlite:///../DataBase.sqlite3", echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine)

    config = load_config()

    bot = Bot(token=config.telegram_bot_token)
    # redis = Redis(host='127.0.0.1', port=6379, decode_responses=True)
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(DatabaseRepositoryMiddleware(session_factory))
    dp['engine'] = engine
    dp['session_factory'] = session_factory
    dp.shutdown.register(on_shutdown)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduler_jobs, IntervalTrigger(minutes=1), args=(bot,))
    scheduler.add_job(
        UpdateUsersType, CronTrigger(day=1, hour=12, minute=0), args=(bot,)
    )
    scheduler.start()

    dp.include_routers(admin.admin_router, user.router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
