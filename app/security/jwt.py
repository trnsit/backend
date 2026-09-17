import jwt

from datetime import datetime, timedelta, timezone

from app.core.config import settings

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    # Calculate when this token should die (expire)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta

    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30) # Default: 30 mins

    # Add standard 'exp' (expiration) timestamp into the payload
    to_encode.update({"exp": expire})

    # Sign and pack everything using our SECRET_KEY and HS256 algorithm
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

    return encoded_jwt

def decode_access_token(token: str) -> dict | None:
    try:
        """ PyJWT checks:
            1. Was this signed with our SECRET_KEY?
            2. Has the 'exp' time expired? """

        decoded_token = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])

        return decoded_token # Returns {"sub": "alice@gmail.com", "exp": ...}

    except jwt.PyJWTError:
        return None
