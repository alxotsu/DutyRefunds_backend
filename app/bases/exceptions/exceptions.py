from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from smtplib import SMTPRecipientsRefused

__all__ = ['APIException', 'ExceptionCaster']


class APIException(Exception):
    def __init__(self, detail, code: int = 400):
        self.detail = detail
        self.code = code

    def to_response(self):
        return {'error': self.detail}, self.code


def cast_http_exception(exception):
    return APIException(exception.__class__.__name__, exception.code)


def cast_integrity_error(exception):
    return APIException(exception.__class__.__name__, 409)


def cast_smtp_recipients_refused_exception(exception: SMTPRecipientsRefused):
    from api.models import EmailConfirm, db
    for email in exception.recipients:
        conf_obj = EmailConfirm.query.filter_by(email=email).first()
        if conf_obj is None:
            continue
        if conf_obj.user.email is None:
            db.session.delete(conf_obj.user)
        else:
            db.session.delete(conf_obj)
    db.session.commit()
    return APIException(exception.__class__.__name__, 400)


class ExceptionCaster:
    EXCEPTION_CAST = {
        HTTPException: cast_http_exception,
        IntegrityError: cast_integrity_error,
        SMTPRecipientsRefused: cast_smtp_recipients_refused_exception,
    }

    @classmethod
    def cast_exception(cls, exception) -> APIException:
        if isinstance(exception, APIException):
            return exception
        for exception_type, caster in cls.EXCEPTION_CAST.items():
            if issubclass(type(exception), exception_type):
                return caster(exception)
        return APIException(exception.__class__.__name__, 400)
