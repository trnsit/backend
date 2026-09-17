from fastapi import FastAPI

from app.core.config import settings

from .routes import router as scans_router

app = FastAPI(
    title='Transit - Scans Service',
    version='1.0.0',
    debug=settings.debug
)

app.include_router(scans_router)
