import os
from pathlib import Path

__all__ = ['Config']


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
                                             f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_MIGRATE_REPO = os.path.join(BASE_DIR, 'api/migrations')
