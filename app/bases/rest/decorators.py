from flask import request
from api import models
from flask_cors import cross_origin

__all__ = ['data_extract_decorator', 'authorize_decorator',
           'check_perms_decorator', 'cross_origin']


def data_extract_decorator(method: callable):
    def wrapper(*args, **kwargs):
        data = dict()
        for field, value in request.files.lists():
            if len(value) == 1:
                data[field] = value[0]
            else:
                data[field] = value
        for field, value in request.form.items():
            data[field] = value
        if request.json:
            for field, value in request.json.items():
                data[field] = value
        request.request_data = data
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
            getattr(self, f"{request.method.lower()}_perms")(*args, **kwargs)
        return method(*args, **kwargs)
    return wrapper
