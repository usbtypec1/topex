from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from aiogram.fsm.storage.memory import MemoryStorage
from redis.asyncio import Redis
from aiogram.fsm.storage.redis import RedisStorage

from src.config import TOKEN

bot = Bot(
    token=TOKEN
)

redis = Redis(host='127.0.0.1', port=6379, decode_responses=True)
storage = RedisStorage(redis)

dp = Dispatcher(storage=storage)