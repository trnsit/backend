import httpx
import secrets
import urllib.parse

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .db.session import get_session
from app.security.jwt import create_access_token, decode_access_token
from app.security.password import hash_password
from .models import User, UserOAuthToken

router = APIRouter(prefix='/auth/google', tags=['google-oauth'])

# 1. Sends user to Google:
@router.get('/login')
async def get_google_login_url():
    # Create a signed temporary token to prevent CSRF attacks:
    state_token = create_access_token(
        data={'purpose': 'google_state'}, 
        expires_delta=timedelta(minutes=10)
    )

    # Creating the URL we have to send user to:
    params = {
        'client_id': settings.google_client_id, # Our platform's public ID (registered with Google Console). Tells Google: "This is Transit asking."
        'redirect_uri': settings.google_redirect_uri, # Tells Google, "When Alice finishes logging in, send her back to the endpoint that we created* for the callback function (here, http://localhost:8000/auth/google/callback)."
        'response_type': 'code', # Tells Google, "Don't send the sensitive token to the browser. Send a temporary one-time code. Almost always 'code' (constant). 'token' is the other option, which is not suggested."
        'scope': 'openid email profile', # This space-separated list tells Google, "We only want to know Alice's email and basic profile—not her Google Drive or emails."
        'state': state_token, # A temporary security badge we create so nobody can fake this request (CSRF protection).
        'access_type': 'offline', # Request refresh token
        'prompt': 'select_account'
    }

    """ By default, Google gives your app an access_token that dies after 1 hour.
    If access_token is set to 'online', when the 1 hour expires, the user must click 'Login with Google' again in their browser.
    access_token set to 'offline' tells Google to give a long-lived refresh_token, too.
    With a refresh_token, when the 1-hour access token expires, your backend can quietly ask Google for a fresh token in the background without disturbing the user. """

    """ Most people are logged into multiple Google accounts on their computer (e.g., personal@gmail.com and work@company.com).
    Without 'prompt': 'select_account': Google might silently auto-pick whatever default account is currently active in the browser.
    With 'prompt': 'select_account': Google will always display the friendly Account Picker screen: "Choose an account to continue to Transit".
    This gives the user the choice of which email they want to use. """

    authorization_url = f'https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}'

    """ 'urllib.parse.urlencode(params)' takes a Python dictionary and turns it into a valid, safe URL query string (with &, =, and special characters properly escaped).
    client_id=123456.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fauth%2Fgoogle%2Fcallback&scope=openid+email+profile&response_type=code

    If you tried to write an f-string manually: f"https://accounts.google.com/...?redirect_uri={redirect_uri}&scope={scope}"

    two major problems happen:
        1. Spaces break URLs: A URL cannot contain raw spaces ("openid email profile"). urlencode safely converts spaces to + or %20.
        2. Slashes and colons break URLs: http://localhost... contains : and /, which confuse web browsers. urlencode safely converts them into %3A%2F%2F.

    urlencode takes { "key": "value" } ⟶ outputs "key=value&key2=value2" with all spaces and special characters made 100% web-safe. """

    return {'url': authorization_url}

# 2. Google sends user to us:
# *This is that callback function.

@router.get('/callback')
async def google_callback(
    code: str, # FastAPI automatically extracts 'code' from URL query.
    state: str, # FastAPI automatically extracts 'state' from URL query.
    session: AsyncSession = Depends(get_session)
):
    # 1. Verify the state parameter to prevent CSRF
    payload = decode_access_token(state)

    if not payload or payload.get('purpose') != 'google_state':
        raise HTTPException(status_code=400, detail='Invalid or expired state parameter.')

    # 2. Exchange the Authorization Code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': settings.google_client_id,
                'client_secret': settings.google_client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': settings.google_redirect_uri,
            }
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail='Failed to retrieve token from Google.')

        token_data = token_response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in')

        if not access_token:
            raise HTTPException(status_code=400, detail='No access token received from Google.')

        # 3. Retrieve User Profile from Google userinfo API
        userinfo_response = await client.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail='Failed to fetch user info from Google.')

        userinfo = userinfo_response.json()
        email = userinfo.get('email')

        if not email:
            raise HTTPException(status_code=400, detail='Google account has no email address.')

    # 4. Check if user already exists in local database:
    user_query = await session.execute(select(User).where(User.email == email))
    user = user_query.scalar_one_or_none()

    if user and not user.is_active:
        raise HTTPException(
            status_code=403,
            detail='User account is inactive or disabled'
        )

    # Create a new user since they are signing up via Google
    if not user:
        # Generate a secure random password as they authenticate via SSO
        random_password = secrets.token_urlsafe(32)
        password_hash = hash_password(random_password)

        user = User(
            email=email,
            password_hash=password_hash,
            is_active=True
        )

        session.add(user)
        await session.flush() # Populates user.id without committing

    # 5. Store or update the Google OAuth credentials
    token_query = await session.execute(
        select(UserOAuthToken).where(
            UserOAuthToken.user_id == user.id,
            UserOAuthToken.provider == 'google'
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
            provider='google',
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        session.add(oauth_token)

    await session.commit()

    # 6. Generate our own local JWT access token for this user
    local_access_token = create_access_token(data={'sub': user.email, 'user_id': str(user.id), 'is_active': user.is_active})

    # Redirect back to the frontend login-success handler page
    return RedirectResponse(
        url=f'http://localhost:3000/login-success?token={local_access_token}'
    )
