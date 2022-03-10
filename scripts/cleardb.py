from api.models import *
from api.models import db
from datetime import datetime, timedelta

__all__ = ['main']


def main():
    now = datetime.utcnow()
    users = User.query.filter(User.registration_time <= now - timedelta(minutes=5),
                              User.email == None)
    for user in users:
        db.session.delete(user)

    confirm_objs = EmailConfirm.query.filter(EmailConfirm.created_at <= now - timedelta(5))
    for confirm_obj in confirm_objs:
        db.session.delete(confirm_obj)

    db.session.commit()


if __name__ == '__main__':
    main()
