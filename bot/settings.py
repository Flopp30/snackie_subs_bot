"""
Config file
"""
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine.url import URL

# logging

logger = logging.getLogger()


file_handler = logging.FileHandler('log.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# Dirs
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# Keys
TG_BOT_KEY = os.getenv("TG_BOT_KEY", "")
YOOKASSA_KEY = os.getenv("YOOKASSA_KEY", "")

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
