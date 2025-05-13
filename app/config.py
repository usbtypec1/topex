import pathlib
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from typing import Final


ROOT_PATH: Final[pathlib.Path] = pathlib.Path(__file__).parent.parent
CONFIG_FILE_PATH = ROOT_PATH / "config.toml"


@dataclass
class Config:
    telegram_bot_token: str
    admin_user_ids: set[int]
    main_channel_url: str
    learning_chanel_url: str


@lru_cache
def load_config() -> Config:
    config = tomllib.loads(CONFIG_FILE_PATH.read_text(encoding='utf-8'))

    return Config(
        telegram_bot_token=config["telegram"]["bot_token"],
        admin_user_ids=set(config["telegram"]["admin_user_ids"]),
        main_channel_url=config["telegram"]["main_channel_url"],
        learning_chanel_url=config["telegram"]["learning_chanel_url"],
    )
