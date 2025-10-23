import os
from pydantic_settings import BaseSettings, SettingsConfigDict


# Pydantic Settings автоматически ищет и загружает .env файл
class Settings(BaseSettings):
    # Указываем, что нужно искать файл .env в текущей директории
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # Основные настройки FastAPI
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # Настройки базы данных
    DATABASE_URL: str


# Создаем единственный экземпляр настроек, который будет использоваться во всем приложении
settings = Settings()
