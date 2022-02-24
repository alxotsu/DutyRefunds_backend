from flask import request
from app import db
from api import models

__all__ = ['data_extract_decorator', 'authorize_decorator',
           'check_perms_decorator']


def data_extract_decorator(method: callable):
    def wrapper(*args, **kwargs):
        if request.json is None:
            data = dict()
            for field, value in request.files.items():
                data[field] = value
            for field, value in request.form.items():
                data[field] = value
            request.request_data = data
        else:
            request.request_data = request.json
        return method(*args, **kwargs)
    return wrapper


def authorize_decorator(method: callable):
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization', None)
        if token is None:
            request.user = None
        else:
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
            getattr(self, f"{request.method.lower()}_perms")(self, *args, **kwargs)
        return method(self, *args, **kwargs)
    return wrapper
