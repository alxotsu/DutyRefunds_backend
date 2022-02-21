from typing import Type
from app import db

__all__ = ['ModelSerializer', 'FileSerializer']


class ModelSerializer:
    model: Type[db.Model]
    fields: list[str]
    read_only_fields = list()
    write_only_fields = list()

    def __init__(self, instance: Type[db.Model] or list[Type[db.Model]] = None,
                 data: dict = None, many=False):
        self.instance = instance
        self.data = data
        self.many = many

    def serialize(self):
        def serialize_obj(instance: Type[db.Model]):
            res = dict()
            for field in self.fields:
                if field in self.write_only_fields:
                    continue
                value = getattr(instance, field)
                if hasattr(self, field):
                    getattr(self, field).instance = value
                    value = getattr(self, field).serialize()
                res[field] = value

            return res

        if self.many:
            return [serialize_obj(obj) for obj in self.instance]

        return serialize_obj(self.instance)

    def create(self):
        def create_obj(data: dict):
            exclude_fields = list()
            for field in data:
                if field not in self.fields or field in self.read_only_fields:
                    exclude_fields.append(field)
                    continue
                if hasattr(self, field):
                    getattr(self, field).data = data[field]
                    data[field] = getattr(self, field).create()

            for field in exclude_fields:
                data.pop(field)

            return self.model(**data)

        if self.many:
            return [create_obj(obj) for obj in self.data]

        return create_obj(self.data)

    def update(self):
        def update_obj(instance: Type[db.Model], data: dict):
            for field in data:
                if field not in self.fields or field in self.read_only_fields:
                    continue
                if hasattr(self, field):
                    getattr(self, field).data = data[field]
                    getattr(self, field).instance = instance
                    data[field] = getattr(self, field).update()
                setattr(instance, field, data[field])

            return instance

        if self.many:
            return [update_obj(self.instance[i], self.data[i])
                    for i in range(min(len(self.instance), len(self.data)))]

        return update_obj(self.instance, self.data)


class FileSerializer:
    def __init__(self, path):
        self.path = path
        self.instance = None
        self.data = None

    def serialize(self):
        return self.instance

    def create(self):  # TODO files implementation
        pass

    def update(self):
        pass

