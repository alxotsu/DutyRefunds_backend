from flask_restful import Resource, request
from .decorators import *

__all__ = ['GenericView', 'CreateMixin', 'UpdateMixin',
           'GetMixin', 'DeleteMixin', 'ViewSetMixin']


class GenericView(Resource):
    method_decorators = [
        check_perms_decorator,
        authorize_decorator,
    ]


class CreateMixin:
    pass


class UpdateMixin:
    pass


class GetMixin:
    pass


class DeleteMixin:
    pass


class ViewSetMixin:
    pass
