from app import db
from api.models import *

if __name__ == '__main__':
    db.create_all()
