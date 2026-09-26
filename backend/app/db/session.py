import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

logger = logging.getLogger("pulseguard.db")


class Base(DeclarativeBase):
    pass


# Normalise the DATABASE_URL:
# - If the URL is a bare "postgresql://" connection string, upgrade it to asyncpg.
# - If the URL already starts with "postgresql+asyncpg://" it passes through unchanged.
# - SQLite (aiosqlite) is accepted for local development / CI.
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

connect_args = {}
if "sqlite" in db_url:
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    connect_args=connect_args,
    pool_pre_ping=("sqlite" not in db_url),
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    global engine, AsyncSessionLocal
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Database schemas initialized successfully using {engine.url.drivername}.")
    except Exception as e:
        if "postgresql" in str(engine.url):
            logger.warning(
                f"PostgreSQL connection failed ({e}).\n"
                "==> Falling back to local SQLite database ('sqlite+aiosqlite:///./pulseguard.db').\n"
                "==> To use PostgreSQL, ensure PostgreSQL is running and update credentials in backend/.env."
            )
            fallback_url = "sqlite+aiosqlite:///./pulseguard.db"
            engine = create_async_engine(
                fallback_url,
                echo=False,
                future=True,
                connect_args={"check_same_thread": False},
                pool_pre_ping=False,
            )
            AsyncSessionLocal.configure(bind=engine)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database schemas initialized successfully on fallback SQLite database.")
        else:
            raise
