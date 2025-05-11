import configparser
import asyncio
import os

from aiogram.filters import Filter
from aiogram.types import Message

DIR = os.path.abspath(__file__)[:-14]

config = configparser.ConfigParser()
config.read(f"{DIR}/settings.ini")
SQLALCHEMY_URL = config["SqlAlchemy"]["SQLALCHEMY_URL"]

TOKEN = config["Telegram"]["TOKEN"]

bot_username = config["Telegram"]["USERNAME"]

reg_web = config["Telegram"]["reg_web"]
channel_link = config["Telegram"]["channel_link"]


def get_admins():
    get_id = config["Telegram"]["ADMINS"]
    ADMIN_ID = []

    if "," in get_id:
        get_id = get_id.split(",")
        for a in get_id:
            ADMIN_ID.append(str(a))
    else:
        try:
            ADMIN_ID = [str(get_id)]
        except ValueError:
            ADMIN_ID = [0]
            print("Не указан Admin_ID")
    return ADMIN_ID


class Admin(Filter):
    def __init__(self):
        get_id = config["Telegram"]["ADMINS"]
        ADMIN_ID = []

        if "," in get_id:
            get_id = get_id.split(",")
            for a in get_id:
                ADMIN_ID.append(str(a))
        else:
            try:
                ADMIN_ID = [str(get_id)]
            except ValueError:
                ADMIN_ID = [0]
                print("Не указан Admin_ID")
        
        self.admins = ADMIN_ID

    async def __call__(self, message: Message):
        return str(message.from_user.id) in self.admins

