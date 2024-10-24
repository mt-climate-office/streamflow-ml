import os
from typing import AsyncIterator, Annotated


from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text
from sqlalchemy import URL
from dotenv import load_dotenv

load_dotenv()


url = URL.create(
    "postgresql+asyncpg",
    host=os.getenv("POSTGRES_HOST"),
    username=os.getenv("POSTGRES_USER"),
    database=os.getenv("POSTGRES_DB"),
    password=os.getenv("POSTGRES_PASSWORD"),
    port=5434,
)

async_engine = create_async_engine(url)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    future=True,
)


async def get_session() -> AsyncIterator[async_sessionmaker]:
    try:
        yield AsyncSessionLocal
    except SQLAlchemyError as e:
        print(e)
        raise


AsyncSession = Annotated[async_sessionmaker, Depends(get_session)]


async def init_db(async_engine, base):
    async with async_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS flow;"))
        await conn.run_sync(base.metadata.create_all)
        # await conn.execute(
        #     text("SELECT create_hypertable('flow.data', by_range('date', INTERVAL '1 year'));")
        # )
