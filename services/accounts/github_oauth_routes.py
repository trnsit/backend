import secrets
import httpx
import urllib.parse

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.security.password import hash_password

from .config import settings
from .db.session import get_session
from app.security.jwt import create_access_token, decode_access_token
from .models import User, UserOAuthToken

router = APIRouter(prefix='/auth/github', tags=['github-oauth'])

@router.get('/login')
async def get_github_login_url():
    state_token = create_access_token(
        data={'purpose': 'github_state'},
        expires_delta=timedelta(minutes=10)
    )

    params = {
        'client_id': settings.github_client_id,
        'redirect_uri': settings.github_redirect_uri,
        'scope': 'read:user user:email repo', # Access profile, verified email, and repos
        'state': state_token
    }

    authorization_url = f'https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}'

    return {'url': authorization_url}

@router.get('/callback')
async def github_callback(code: str, state: str, session: AsyncSession = Depends(get_session)):
    # Verify CSRF state token
    payload = decode_access_token(state)

    if not payload or payload.get('purpose') != 'github_state':
        raise HTTPException(status_code=400, detail='Invalid or expired state parameter.')

    # Exchange authorization code for GitHub access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            'https://github.com/login/oauth/access_token',
            headers={'Accept': 'application/json'},
            data={
                'client_id': settings.github_client_id,
                'client_secret': settings.github_client_secret,
                'code': code,
                'redirect_uri': settings.github_redirect_uri,
            }
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail='Failed to retrieve token from GitHub.')

        token_data = token_response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in')

        if not access_token:
            raise HTTPException(
                status_code=400,
                detail=f"GitHub authorization failed: {token_data.get('error_description', 'No access token received')}"
            )

        # Retrieve User's Primary Verified Email from GitHub
        emails_response = await client.get(
            'https://api.github.com/user/emails',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/vnd.github+json',
                'User-Agent': 'Transit-App'
            }
        )

        if emails_response.status_code != 200:
            raise HTTPException(status_code=400, detail='Failed to fetch email from GitHub.')

        emails = emails_response.json()
        email = None

        # Find primary verified email
        for item in emails:
            if item.get('primary') and item.get('verified'):
                email = item['email'].strip().lower()

                break

        # Fallback to any verified email if primary wasn't flagged
        if not email:
            for item in emails:
                if item.get('verified'):
                    email = item['email'].strip().lower()

                    break

        if not email:
            raise HTTPException(status_code=400, detail='No verified email associated with this GitHub account.')

    # Check if user already exists in local database
    user_query = await session.execute(select(User).where(User.email == email))
    user = user_query.scalar_one_or_none()

    if user and not user.is_active:
        raise HTTPException(
            status_code=403,
            detail='User account is inactive or disabled'
        )

    # Auto-provision new user if they don't exist yet
    if not user:
        random_password = secrets.token_urlsafe(32)
        password_hash = hash_password(random_password)
        user = User(
            email=email,
            password_hash=password_hash,
            is_active=True
        )

        session.add(user)
        await session.flush()

    # Store or update the GitHub OAuth credentials
    token_query = await session.execute(
        select(UserOAuthToken).where(
            UserOAuthToken.user_id == user.id,
            UserOAuthToken.provider == 'github'
        )
    )

    oauth_token = token_query.scalar_one_or_none()
    expires_at = None

    if expires_in:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

    if oauth_token:
        oauth_token.access_token = access_token

        if refresh_token:
            oauth_token.refresh_token = refresh_token

        oauth_token.expires_at = expires_at

    else:
        oauth_token = UserOAuthToken(
            user_id=user.id,
            provider='github',
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )

        session.add(oauth_token)

    await session.commit()

    # Generate local Transit JWT access token
    local_access_token = create_access_token(
        data={'sub': user.email, 'user_id': str(user.id), 'is_active': user.is_active}
    )

    # Redirect back to frontend
    return RedirectResponse(
        url=f'{settings.frontend_url}/login-success?token={local_access_token}'
    )
