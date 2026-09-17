from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from ..config import settings

engine = create_async_engine(settings.repositories_database_url)
SessionLocal = async_sessionmaker(bind=engine)

async def get_session():
    session = SessionLocal()

    try:
        yield session

    finally:
        await session.close()
