from random import sample
import string
from datetime import datetime

from app import db

__all__ = ['User', 'Authtoken', 'EmailConfirm', 'Courier', 'Case', 'Document']

CHARS_POOL = string.ascii_lowercase + string.ascii_uppercase + string.digits


def generate_key(length: int, chars_pool=CHARS_POOL):
    return ''.join(sample(chars_pool, length))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.VARCHAR(32), nullable=False)
    email = db.Column(db.VARCHAR, index=True, unique=True, nullable=True)
    subs_on_marketing = db.Column(db.Boolean, default=False, nullable=False)
    role = db.Column(db.SmallInteger, nullable=False, default=0)
    bank_name = db.Column(db.VARCHAR(32), nullable=False)
    card_number = db.Column(db.VARCHAR(16), nullable=True)
    bank_code = db.Column(db.VARCHAR(16), nullable=True)
    timeline = db.Column(db.JSON, nullable=False)
    gclid = db.Column(db.VARCHAR, nullable=True)

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
                        nullable=False)
    key = db.Column(db.VARCHAR(6), nullable=False, default=lambda: generate_key(6, '1234567890'))
    email = db.Column(db.VARCHAR, index=True, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='email_confirm_obj')

    def update_key(self):
        self.key = generate_key(6, '1234567890')
        self.created_at = datetime.utcnow()

    def __repr__(self):
        return f'Email "{self.email}" confirm for User {self.user_id}'


class Courier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(64), nullable=False, unique=True)
    required_documents = db.Column(db.JSON)

    def __repr__(self):
        return f'Courier "{self.name}"'

    def calc_cost(self, duty: int, vat: int) -> int:
        from api.calculators import CALCULATORS
        calculator = CALCULATORS[self.name] \
            if self.name in CALCULATORS \
            else CALCULATORS['other']

        return calculator(duty, vat)


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id", ondelete="CASCADE"),
                        nullable=False)
    category = db.Column(db.VARCHAR(64), nullable=False)
    file = db.Column(db.VARCHAR, nullable=False)

    def __repr__(self):
        return f'Document {self.category} for Case {self.case_id}'


class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    courier_id = db.Column(db.Integer, db.ForeignKey("courier.id"), nullable=False)
    duty = db.Column(db.DECIMAL, nullable=False)
    vat = db.Column(db.DECIMAL, nullable=False)
    refund = db.Column(db.DECIMAL, nullable=False)
    cost = db.Column(db.DECIMAL, nullable=False)
    our_fee = db.Column(db.DECIMAL, nullable=False)
    description = db.Column(db.VARCHAR(256))
    tracking_number = db.Column(db.Integer, nullable=True)
    signature = db.Column(db.VARCHAR, nullable=False)
    timeline = db.Column(db.JSON, nullable=False)
    hmrc_payment = db.Column(db.DECIMAL, nullable=False)
    epu_number = db.Column(db.Integer, nullable=False)
    import_entry_number = db.Column(db.Integer, nullable=False)
    import_entry_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    custom_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.SmallInteger, nullable=False, default=0)

    documents = db.relationship('Document', backref='case', lazy='dynamic')

    unique_constraint = db.UniqueConstraint("courier_id", "tracking_number")

    class STATUS:
        NEW = 0
        SUBMISSION = 1
        SUBMITTED = 2
        HMRC_AGREED = 3
        PAID = 4

    def __repr__(self):
        return f'Case {self.id}'
