"""
Async engine for SqlAlchemy
"""
from contextlib import asynccontextmanager

from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine as _create_async_engine
)
from sqlalchemy.orm import sessionmaker

from bot.settings import POSTGRES_URL


def create_async_engine(url: URL | str) -> AsyncEngine:
    """
    Create async engine with constant params
    :param url:
    :return:
    """
    return _create_async_engine(url=url, echo=True, pool_pre_ping=True)


engine = create_async_engine(POSTGRES_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession)


@asynccontextmanager
async def get_async_session() -> async_sessionmaker:
    async with AsyncSessionLocal() as async_session:
        try:
            yield async_session
        finally:
            await async_session.close()
