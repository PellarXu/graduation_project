from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Resume Screening System"
    DEBUG: bool = True

    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "123456"
    MYSQL_DB: str = "resume_system"

    class Config:
        env_file = ".env"


settings = Settings()
