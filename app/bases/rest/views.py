try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping
from werkzeug.wrappers import Response as ResponseBase
from flask_restful.utils import unpack, OrderedDict

from flask_restful import Resource, request
from app import db
from .decorators import *
from typing import Type

__all__ = ['GenericView', 'CreateMixin', 'UpdateMixin',
           'GetMixin', 'DeleteMixin', 'ViewSetMixin']


class GenericView(Resource):
    method_decorators = [
        check_perms_decorator,
        authorize_decorator,
    ]

    def dispatch_request(self, *args, **kwargs):
        meth = getattr(self, request.method.lower(), None)
        if meth is None and request.method == 'HEAD':
            meth = getattr(self, 'get', None)
        assert meth is not None, 'Unimplemented method %r' % request.method

        if isinstance(self.method_decorators, Mapping):
            decorators = self.method_decorators.get(request.method.lower(), [])
        else:
            decorators = self.method_decorators

        for decorator in decorators:
            meth = decorator(meth)

        resp = meth(self, *args, **kwargs)

        if isinstance(resp, ResponseBase):
            return resp

        representations = self.representations or OrderedDict()

        mediatype = request.accept_mimetypes.best_match(representations, default=None)
        if mediatype in representations:
            data, code, headers = unpack(resp)
            resp = representations[mediatype](data, code, headers)
            resp.headers['Content-Type'] = mediatype
            return resp

        return resp

    model: Type[db.Model]
    lookup_field = 'id'

    def get_queryset(self,  *args, **kwargs):
        return self.model.query

    def get_object(self, *args, **kwargs):
        return self.get_queryset(*args, **kwargs)\
            .get(**{self.lookup_field: kwargs[self.lookup_field]})


class CreateMixin:
    pass


class UpdateMixin:
    pass


class GetMixin:
    pass


class DeleteMixin:
    pass


class ViewSetMixin:
    page_size = 10

    def get(self, *args, **kwargs):
        queryset = self.get_queryset(*args, **kwargs)
        page_number = int(request.args.get('page_number', 1))
        page_size = int(request.args.get('page_size', self.page_size))

        results = queryset.paginate(page_number, page_size, False).items

        return {"results": [item.serialize() for item in results]}
