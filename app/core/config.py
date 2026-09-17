from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict # Pydantic Settings is an external package, not a part of Pydantic itself.

ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"

# Create the settings class for the app
class Settings(BaseSettings):
    debug: bool

    # Database URLs for Decoupled Microservices
    accounts_database_url: str
    repositories_database_url: str
    scans_database_url: str

    secret_key: str
    jwt_algorithm: str = 'HS256'

    # Google OAuth Config.
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    # GitHub OAuth Config.
    github_client_id: str
    github_client_secret: str
    github_redirect_uri: str

    # Ollama Config.
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # model_config - extra behavioural configuration for this Pydantic model:
    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH) # Tell FastAPI to look in the env file

settings = Settings()
