from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    cognito_user_pool_id: str
    cognito_app_client_id: str

    # Aquí puedes ir mudando las demás variables en el futuro (DB, Trello, etc.)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
