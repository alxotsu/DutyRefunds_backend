"""
Server:
    :param DEBUG
        :type int | None
        :default 0
        :description
            0 - False
            1 - True

Database:
    :param DB_USER:
        :type str | None
        :default "postgres"
    :param DB_PASSWORD:
        :type str
    :param DB_URL:
        :type str | None
        :default "localhost:5432"
    :param DB_NAME:
        :type str

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

