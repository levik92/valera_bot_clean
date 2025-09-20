from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict    


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding='utf-8',
        env_nested_delimiter="__",
        extra="allow"
    )
    bot_token: SecretStr
    openai_api_key: SecretStr
    db_url: str
    tg_channel_id: int
    tg_channel_link: str
    provider_token: str
       

settings = Settings()