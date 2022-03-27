from api.models import db
from api.models import *

__all__ = ['main']


def main():
    username = input("Username: ")
    email = input("Email: ")

    user = User(username=username, email=email, role=User.ROLE.ADMIN,
                bank_name=username)
    user.authtoken = [Authtoken()]
    db.session.add(user)
    db.session.commit()

    print(user.authtoken[0].key)


if __name__ == '__main__':
    main()
