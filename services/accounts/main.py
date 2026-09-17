from fastapi import FastAPI

from app.core.config import settings

from .routes import router as user_router
from .google_oauth_routes import router as google_oauth_router
from .github_oauth_routes import router as github_oauth_router

app = FastAPI(
    title='Transit - Accounts Service',
    version='1.0.0',
    debug=settings.debug
)

app.include_router(user_router)
app.include_router(google_oauth_router)
app.include_router(github_oauth_router)
