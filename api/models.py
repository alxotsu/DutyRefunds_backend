from random import sample
import string, decimal
from datetime import datetime

from app import db

__all__ = ['User', 'Authtoken', 'EmailConfirm', 'Courier',
           'Case', 'Document', 'CalculateResult']

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
    registration_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    gclid = db.Column(db.VARCHAR, nullable=True)

    cases = db.relationship('Case', backref='user', lazy='dynamic', cascade="all,delete")
    email_confirm_obj = db.relationship('EmailConfirm', backref='user',
                                        lazy='dynamic', cascade="all,delete")

    def __repr__(self):
        return f'User #{self.id} "{self.username}"'

    class ROLE:
        USER = 0
        ADMIN = 1


class Authtoken(db.Model):
    key = db.Column(db.VARCHAR(20), primary_key=True, default=lambda: generate_key(20), )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"),
                        nullable=False, unique=True)

    user = db.relationship('User', backref='authtoken')

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

    def update_key(self):
        self.key = generate_key(6, '1234567890')
        self.created_at = datetime.utcnow()

    def __repr__(self):
        return f'Email "{self.email}" confirm for User {self.user_id}'


class Courier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(64), nullable=False, unique=True)
    required_documents = db.Column(db.JSON)
    drl_pattern = db.Column(db.VARCHAR, nullable=True)
    drl_content = db.Column(db.JSON)

    results = db.relationship('CalculateResult', backref='courier', lazy='dynamic')
    cases = db.relationship('Case', backref='courier', lazy='dynamic')

    def __repr__(self):
        return f'Courier "{self.name}"'

    def calc_cost(self, duty: decimal, vat: decimal) -> decimal:
        from api.calculators import CALCULATORS
        calculator = CALCULATORS[self.name] \
            if self.name in CALCULATORS \
            else CALCULATORS['other']

        return float(calculator(duty, vat))


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id", ondelete="CASCADE"),
                        nullable=False)
    category = db.Column(db.VARCHAR(64), nullable=False)
    files = db.Column(db.ARRAY(db.VARCHAR), nullable=False, default=list())
    allowed_types = db.Column(db.ARRAY(db.VARCHAR), nullable=False)
    required = db.Column(db.Boolean, nullable=False)

    unique_constraint = db.UniqueConstraint("case_id", "category")

    def __repr__(self):
        return f'Document {self.category} for Case {self.case_id}'


class CalculateResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    duty = db.Column(db.DECIMAL, nullable=False)
    vat = db.Column(db.DECIMAL, nullable=False)
    cost = db.Column(db.DECIMAL, nullable=False)
    courier_id = db.Column(db.Integer, db.ForeignKey("courier.id"), nullable=False)
    description = db.Column(db.VARCHAR(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def calc_cost(self):
        return self.courier.calc_cost(self.duty, self.vat)


class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    courier_id = db.Column(db.Integer, db.ForeignKey("courier.id"), nullable=False)
    result_id = db.Column(db.Integer, db.ForeignKey("calculate_result.id"), nullable=False,
                          unique=True)
    tracking_number = db.Column(db.VARCHAR(12), nullable=False)
    signature = db.Column(db.VARCHAR, nullable=False)
    drl_document = db.Column(db.VARCHAR, nullable=True)
    hmrc_document = db.Column(db.VARCHAR, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    hmrc_payment = db.Column(db.DECIMAL, nullable=True)
    epu_number = db.Column(db.Integer, nullable=True)
    import_entry_number = db.Column(db.Integer, nullable=True)
    import_entry_date = db.Column(db.Date, nullable=True)
    custom_number = db.Column(db.Integer, nullable=True)
    status = db.Column(db.SmallInteger, nullable=False, default=0)
    airtable_id = db.Column(db.VARCHAR, nullable=True)

    documents = db.relationship('Document', backref='case', lazy='dynamic',
                                cascade="all,delete")
    result = db.relationship('CalculateResult', backref='case',
                             cascade="all,delete")

    class STATUS:
        NEW = 0
        SUBMISSION = 1
        SUBMITTED = 2
        HMRC_AGREED = 3
        PAID = 4

    def __repr__(self):
        return f'Case {self.id}'
