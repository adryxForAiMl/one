from pydantic import BaseSettings

class Settings(BaseSettings):
    # API configuration
    API_TITLE: str = "SentinelAPI"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Zero-Trust API Vulnerability Scanner"
    API_PREFIX: str = "/api"

    # Database configuration
    DATABASE_URL: str = "sqlite:///./test.db"

    # Security settings
    SECRET_KEY: str = "your_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()