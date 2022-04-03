"""
Environment requirements:

    Flask:
        DEBUG
            type: int | None
            default: 0
            description:
                0 - False
                1 - True
        CELERY_BROKER:
            type: str | None
            default: "redis://127.0.0.1:6379/0"

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

    APIs:
        SD_API_KEY:
            type: str | None
            default: None
        AT_API_KEY:
            type: str | None
            default: None
        AT_URL:
            type: str | None
            default: None

"""

from os import environ, getenv, path, sep
from pathlib import Path

__all__ = ['Config']


class Config:
    BASE_DIR = str(Path(__file__).resolve().parent.parent).replace(sep, '/')

    DEBUG_MODE = bool(int(getenv("DEBUG", 0)))
    CSRF_ENABLED = True

    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{getenv("DB_USER", "postgres")}:{environ["DB_PASSWORD"]}@{getenv("DB_URL", "localhost:5432")}/{environ["DB_NAME"]}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = BASE_DIR + '/media/'

    SWAGGER_FORMS = BASE_DIR + '/api/swagger_forms/'

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = getenv('EMAIL_HOST_USER')
    MAIL_DEFAULT_SENDER = getenv('EMAIL_HOST_USER')
    MAIL_PASSWORD = getenv('EMAIL_HOST_PASSWORD')

    SIMPLE_DUTY_KEY = getenv('SD_API_KEY')
    AIRTABLE_API_KEY = getenv('AT_API_KEY')
    AIRTABLE_URL = getenv('AT_URL')

    CELERY_BROKER_URL = getenv("CELERY_BROKER", 'redis://127.0.0.1:6379/0')
