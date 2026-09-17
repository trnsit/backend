from fastapi import FastAPI

from app.core.config import settings
from .routes import router as intelligence_router

app = FastAPI(
    title='Transit - Intelligence Service',
    version='1.0.0',
    debug=settings.debug
)

app.include_router(intelligence_router)
