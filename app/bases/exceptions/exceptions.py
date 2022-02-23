from werkzeug.exceptions import HTTPException

__all__ = ['APIException', 'ExceptionCaster']


class APIException(Exception):
    def __init__(self, detail, code: int = 400):
        self.detail = detail
        self.code = code

    def to_response(self):
        return self.detail, self.code


def cast_http_exception(exception):
    return APIException(exception.__class__.__name__, exception.code)


class ExceptionCaster:
    EXCEPTION_CAST = {
        HTTPException: cast_http_exception,
    }

    @classmethod
    def cast_exception(cls, exception) -> APIException:
        if isinstance(exception, APIException):
            return exception
        for exception_type, caster in cls.EXCEPTION_CAST.items():
            if issubclass(type(exception), exception_type):
                return caster(exception)
        return APIException(exception.__class__.__name__, 400)
