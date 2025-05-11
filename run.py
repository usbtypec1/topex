import asyncio
import logging
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app import admin, user
from app.database.models import async_main
from app.utils.sheets import (
    GetAllParcelData, GetMailingMessage, GetNewAdress,
    GetParcelsFromStorage, UpdateUserDataSheets,
)
from app.utils.strings import UpdateUserDiscount, UpdateUsersType
from loader import bot, dp


async def scheduler_jobs():
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
    

async def main():
    await async_main()
    
    # logging.getLogger('apscheduler').setLevel(logging.CRITICAL)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduler_jobs, 'interval', seconds=60, args=())
    scheduler.add_job(UpdateUsersType, 'cron', day='1', hour='12', minute='00', args=(bot,))
    scheduler.start()
    
    dp.include_routers(admin.admin_router, user.router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
