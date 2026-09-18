from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict # Pydantic Settings is an external package, not a part of Pydantic itself.

ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"

# Create the settings class for the app
class BaseServiceSettings(BaseSettings):
    debug: bool

    frontend_url: str = 'http://localhost:3000'

    secret_key: str
    jwt_algorithm: str = 'HS256'

    # model_config - extra behavioural configuration for this Pydantic model:
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH, # Tell FastAPI to look in the env file
        extra='ignore' # Allow services to ignore variables meant for other services
    )

settings = BaseServiceSettings()
