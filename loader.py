from aiogram import Bot, Dispatcher

from redis.asyncio import Redis
from aiogram.fsm.storage.redis import RedisStorage

from app.config import TOKEN

bot = Bot(
    token=TOKEN
)

redis = Redis(host='127.0.0.1', port=6379, decode_responses=True)
storage = RedisStorage(redis)

dp = Dispatcher(storage=storage)