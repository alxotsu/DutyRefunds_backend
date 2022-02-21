from flask import request
from app import db
from api import models

__all__ = ['authorize_decorator', 'check_perms_decorator']


def authorize_decorator(method: callable):
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization', None)
        token_model = models.Authtoken.query.get(token)
        if token_model:
            request.user = token_model.user
        else:
            request.user = None

        return method(*args, **kwargs)
    return wrapper


def check_perms_decorator(method: callable):
    def wrapper(self, *args, **kwargs):
        if hasattr(self, f"{request.method.lower()}_perms"):
            try:
                getattr(self, f"{request.method.lower()}_perms")(*args, **kwargs)
            except Exception as e:  # TODO replace on APIException
                return e, 403
        return method(*args, **kwargs)
    return wrapper
