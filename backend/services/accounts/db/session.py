from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings

engine = create_async_engine(settings.accounts_database_url)
SessionLocal = async_sessionmaker(bind=engine)

async def get_session():
    session = SessionLocal()

    try:
        yield session

    finally:
        await session.close()
