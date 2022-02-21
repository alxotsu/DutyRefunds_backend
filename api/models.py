from random import sample
import string
from datetime import datetime

from app import db

__all__ = ['User', 'Authtoken', 'EmailConfirm', 'Courier', 'Case', 'Document']

CHARS_POOL = string.ascii_lowercase + string.ascii_uppercase + string.digits


def generate_key(length: int):
    return ''.join(sample(CHARS_POOL, length))


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.VARCHAR(32), nullable=False)
    email = db.Column(db.VARCHAR, index=True, unique=True, nullable=True)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    subs_on_marketing = db.Column(db.Boolean, default=False, nullable=False)
    signature = db.Column(db.VARCHAR)
    role = db.Column(db.SmallInteger, nullable=False, default=0)

    cases = db.relationship('Case', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'User #{self.id} "{self.username}"'

    class ROLE:
        USER = 0
        ADMIN = 1


class Authtoken(db.Model):
    key = db.Column(db.VARCHAR(20), primary_key=True, default=lambda: generate_key(20), )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"),
                        nullable=False, unique=True)

    user = db.relationship('User')

    def update_key(self):
        self.key = generate_key(20)

    def __repr__(self):
        return f'Key "{self.key}" from User {self.user_id}'


class EmailConfirm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"),
                        nullable=False, unique=True)
    key = db.Column(db.VARCHAR(6), nullable=False, default=lambda: generate_key(6))
    email = db.Column(db.VARCHAR, index=True, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='email_confirm_obj')

    def update_key(self):
        self.key = generate_key(6)

    def __repr__(self):
        return f'Email "{self.email}" confirm for User {self.user_id}'


class Courier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(64), nullable=False, unique=True)
    calculator_script_filename = db.Column(db.VARCHAR(64))
    required_documents = db.Column(db.JSON)

    def __repr__(self):
        return f'Courier "{self.name}"'


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id", ondelete="CASCADE"),
                        nullable=False)
    category = db.Column(db.VARCHAR(64), nullable=False)
    file = db.Column(db.VARCHAR, nullable=False)

    unique_constraint = db.UniqueConstraint("case_id", "category")

    def __repr__(self):
        return f'Document {self.category} for Case {self.case_id}'


class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    courier_id = db.Column(db.Integer, db.ForeignKey("courier.id"), nullable=False)
    tracking_number = db.Column(db.VARCHAR, nullable=True)
    duty = db.Column(db.Integer, nullable=False)
    VAT = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Integer, nullable=False)
    description = db.Column(db.VARCHAR(256))
    status = db.Column(db.SmallInteger, nullable=False, default=0)

    documents = db.relationship('Document', backref='case', lazy='dynamic')

    unique_constraint = db.UniqueConstraint("courier_id", "tracking_number")

    class STATUS:
        CREATING = 0
        WAITING_DOCS = 1
        PROCESSING = 2
        DONE = 3

    def __repr__(self):
        return f'Case {self.id}'
