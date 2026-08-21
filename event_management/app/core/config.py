from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:n4iP6KwKSumMM.3@localhost:3306/event_management"
    secret_key: str = "change-this-in-production"
    access_token_expire_minutes: Optional[int] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
