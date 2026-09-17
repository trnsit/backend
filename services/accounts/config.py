from app.core.config import BaseServiceSettings

class AccountsSettings(BaseServiceSettings):
    accounts_database_url: str

    # Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    # GitHub OAuth
    github_client_id: str
    github_client_secret: str
    github_redirect_uri: str

settings = AccountsSettings()
