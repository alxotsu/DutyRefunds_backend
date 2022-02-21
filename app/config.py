"""
Environment requirements:

    Flask:
        DEBUG
            type: int | None
            default: 0
            description:
                0 - False
                1 - True

    Database:
        DB_USER:
            type: str | None
            default: "postgres"
        DB_PASSWORD:
            type: str
        DB_URL:
            type: str | None
            default: "localhost:5432"
        DB_NAME:
            type: str

    Email:
        EMAIL_HOST_USER:
            type: str | None
            default: None
        EMAIL_HOST_PASSWORD:
            type: str | None
            default: None

"""

from os import environ, getenv, path
from pathlib import Path

__all__ = ['Config']


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent

    DEBUG_MODE = bool(int(getenv("DEBUG", 0)))

    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{getenv("DB_USER", "postgres")}:{environ["DB_PASSWORD"]}@{getenv("DB_URL", "localhost:5432")}/{environ["DB_NAME"]}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_MIGRATE_REPO = path.join(BASE_DIR, 'api/migrations')

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = getenv('EMAIL_HOST_USER')
    MAIL_DEFAULT_SENDER = getenv('EMAIL_HOST_USER')
    MAIL_PASSWORD = getenv('EMAIL_HOST_PASSWORD')
