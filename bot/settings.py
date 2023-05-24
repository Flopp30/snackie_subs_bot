"""
Config file
"""
import logging
import os
from logging import Logger
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine.url import URL

# logging
logger: Logger = logging.getLogger()

file_handler = logging.FileHandler('log.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Dirs
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# DB
DB_DRIVER = os.getenv("POSTGRES_DRIVER", "postgresql+asyncpg")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5432))
DB_NAME = os.getenv("POSTGRES_DB", "test_db")
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

POSTGRES_URL = URL.create(
    drivername=DB_DRIVER,
    host=DB_HOST,
    port=DB_PORT,
    username=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
)

# TG
TG_BOT_KEY = os.getenv("TG_BOT_KEY")
ADMIN_TG_ID = os.getenv("ADMIN_TG_ID")
TG_BOT_URL = os.getenv("TG_BOT_URL")

# YOOKASSA
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_API_ENDPOINT = os.getenv("YOOKASSA_API_ENDPOINT")

# PAYMENTS
TOTAL_AWAIT_PAYMENT_SEC = 3600
INTERVAL_FOR_CHECKING_PAYMENT_SEC = 5


# Owned bot administration


class OwnedBot:
    def __init__(self, name: str, api_token: str, tg_chat_id: int) -> None:
        self.name = name
        self.api_token = api_token
        self.tg_chat_id = tg_chat_id

    def get_ban_url(self, user_id: int) -> str:
        return f"https://api.puzzlebot.top/" \
               f"?token={self.api_token}&method=userBan" \
               f"&tg_chat_id={self.tg_chat_id}&user_id={user_id}&until_date=1988150461"

    def get_unban_url(self, user_id: int) -> str:
        return f"https://api.puzzlebot.top/" \
               f"?token={self.api_token}&method=userUnban" \
               f"&tg_chat_id={self.tg_chat_id}&user_id={user_id}"


WORKOUT_BOT_API_KEY = os.getenv("WORKOUT_BOT_API_KEY")
WORKOUT_BOT_CHAT_ID = int(os.getenv("WORKOUT_BOT_CHAT_ID"))
ROOKIE_BOT_API_KEY = os.getenv("ROOKIE_BOT_API_KEY")
ROOKIE_BOT_CHAT_ID = int(os.getenv("ROOKIE_BOT_CHAT_ID"))

PRO_WORKOUT_BOT_API_KEY = os.getenv("PRO_WORKOUT_BOT_API_KEY")
PRO_WORKOUT_BOT_CHAT_ID = int(os.getenv("PRO_WORKOUT_BOT_CHAT_ID"))

WORKOUT_BOT = OwnedBot(
    name="Workout bot",
    api_token=WORKOUT_BOT_API_KEY,
    tg_chat_id=WORKOUT_BOT_CHAT_ID
)

ROOKIE_BOT = OwnedBot(
    name="Rookie bot",
    api_token=ROOKIE_BOT_API_KEY,
    tg_chat_id=ROOKIE_BOT_CHAT_ID
)

PRO_WORKOUT_BOT = OwnedBot(
    name="Pro workout bot",
    api_token=PRO_WORKOUT_BOT_API_KEY,
    tg_chat_id=PRO_WORKOUT_BOT_CHAT_ID
)

OWNED_BOTS = [
    WORKOUT_BOT,
    ROOKIE_BOT,
    PRO_WORKOUT_BOT,
]

# Request
HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                  "(KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}
