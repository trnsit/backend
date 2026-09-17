from fastapi import FastAPI

from .config import settings
from .routes import router as scans_router

app = FastAPI(
    title='Transit - Scans Service',
    version='1.0.0',
    debug=settings.debug
)

app.include_router(scans_router)

@app.get('/health', tags=['health'])
async def health():
    return {'status': 'healthy', 'service': 'scans'}
