from fastapi import FastAPI

from app.core.config import settings

from .routes import router as repository_router

app = FastAPI(
    title='Transit - Repositories Service',
    version='1.0.0',
    debug=settings.debug
)

app.include_router(repository_router)
