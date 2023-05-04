from pydantic import BaseSettings


class Settings(BaseSettings):
    POSTGRES_USER: str = "dummy"
    POSTGRES_PASSWORD: str = "dummy"
    POSTGRES_DB: str = "dummy"
    DATABASE_URL: str = "postgresql://dummy:dummy@db:5432/dummy"

    CELERY_BROKER_URL: str = "amqp://dummy:dummy@rabbitmq:5672//"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    RABBITMQ_DEFAULT_USER: str = "dummy"
    RABBITMQ_DEFAULT_PASS: str = "dummy"

    class Config:
        env_file = ".env"


settings = Settings()