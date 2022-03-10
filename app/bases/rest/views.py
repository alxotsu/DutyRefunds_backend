try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping
from typing import Type
from werkzeug.wrappers import Response as ResponseBase
from flask_restful.utils import unpack, OrderedDict
from flask_restful import Resource, request
from app import db, Config
from app.bases.rest.serializers import ModelSerializer
from .decorators import *
from app.bases.exceptions import *

__all__ = ['GenericView', 'CreateMixin', 'UpdateMixin',
           'GetMixin', 'DeleteMixin', 'ViewSetMixin']


class GenericView(Resource):
    method_decorators = [
        check_perms_decorator,
        authorize_decorator,
        data_extract_decorator,
        cross_origin()
    ]
    serializer_class: ModelSerializer
    lookup_field = 'id'

    @staticmethod
    def handle_exception(exception: Exception):
        db.session.rollback()

        if Config.DEBUG_MODE:
            raise exception
        else:
            return ExceptionCaster.cast_exception(exception).to_response()

    def dispatch_request(self, *args, **kwargs):
        meth = getattr(self, request.method.lower(), None)
        if meth is None and request.method == 'HEAD':
            meth = getattr(self, 'get', None)
        assert meth is not None, 'Unimplemented method %r' % request.method

        for decorator in self.method_decorators:
            meth = decorator(meth)

        try:
            resp = meth(self, *args, **kwargs)
        except Exception as e:
            resp = self.handle_exception(e)

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

    def get_queryset(self,  *args, **kwargs):
        return self.serializer_class.model.query

    _object = None

    def get_object(self, *args, **kwargs):
        if self._object:
            return self._object
        queryset = self.get_queryset(*args, **kwargs)
        self._object = queryset.filter_by(**kwargs).first()

        if self._object is None:
            raise APIException(f"{self.serializer_class.model.__name__} is not found", 404)

        return self._object


class CreateMixin:
    def post(self, *args, **kwargs):
        serializer = self.serializer_class(data=request.request_data)
        instance = serializer.create()
        db.session.add(instance)
        db.session.commit()

        serializer.instance = instance
        return serializer.serialize(), 201


class UpdateMixin:
    def put(self, *args, **kwargs):
        instance = self.get_object(*args, **kwargs)
        serializer = self.serializer_class(instance=instance, data=request.request_data)
        instance = serializer.update()
        db.session.add(instance)
        db.session.commit()

        serializer.instance = instance
        return serializer.serialize(), 200


class GetMixin:
    def get(self, *args, **kwargs):
        instance = self.get_object(*args, **kwargs)
        serializer = self.serializer_class(instance=instance)

        return serializer.serialize(), 200


class DeleteMixin:
    def delete(self, *args, **kwargs):
        instance = self.get_object(*args, **kwargs)
        db.session.delete(instance)
        db.session.commit()

        return "Ok", 204


class ViewSetMixin:
    page_size = 10

    def get(self, *args, **kwargs):
        queryset = self.get_queryset(*args, **kwargs)
        page_number = int(request.args.get('page_number', 1))
        page_size = int(request.args.get('page_size', self.page_size))

        results = queryset.paginate(page_number, page_size, False).items
        serializer = self.serializer_class(instance=results, many=True)

        return {"results": serializer.serialize()}, 200
