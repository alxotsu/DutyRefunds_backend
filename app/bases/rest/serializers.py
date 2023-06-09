from pathlib import Path
from os import remove
from datetime import datetime, date
from typing import Type
from werkzeug.utils import secure_filename
from flask import request
from app import db, Config
from app.bases.exceptions import APIException

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
                if isinstance(value, (datetime, date)):
                    value = str(value)
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
                    getattr(self, field).instance = getattr(instance, field)
                    data[field] = getattr(self, field).update()
                setattr(instance, field, data[field])

            return instance

        if self.many:
            return [update_obj(self.instance[i], self.data[i])
                    for i in range(min(len(self.instance), len(self.data)))]

        return update_obj(self.instance, self.data)


class FileSerializer:
    def __init__(self, path: str, name_prefix: str,
                 allowed_files=('.jpg', '.pdf'), many=False):
        self.path = path
        self.name_prefix = name_prefix
        self.allowed_files = allowed_files
        self.instance = None
        self.data = None
        self.many = many

    def serialize(self):
        if not self.instance:
            return self.instance

        url = request.host_url + 'upload/'
        if self.many:
            return [url + file for file in self.instance]
        return url + self.instance

    def create(self):
        if self.many:
            files = list()
            i = 0
            time_postfix = datetime.utcnow().isoformat().replace(':', '-')
            full_path = Config.UPLOAD_FOLDER + self.path

            from werkzeug.datastructures import FileStorage
            if isinstance(self.data,  FileStorage):
                self.data = [self.data]
            for file in self.data:
                i += 1
                file_res = '.' + secure_filename(file.filename).split('.')[-1]
                filename = self.name_prefix + time_postfix + f"({i})" + file_res

                if file_res not in self.allowed_files:
                    raise APIException(f"Forbidden file type. {self.allowed_files} only", 400)
                files.append((file, filename))

            Path(full_path).mkdir(parents=True, exist_ok=True)
            result = list()
            for file_obj in files:
                file_obj[0].save(full_path + file_obj[1])
                result.append(self.path + file_obj[1])
            return result

        else:
            file = self.data

            file_res = '.' + secure_filename(file.filename).split('.')[-1]
            full_path = Config.UPLOAD_FOLDER + self.path
            filename = self.name_prefix + datetime.utcnow().isoformat().replace(':', '-') + file_res

            if file_res not in self.allowed_files:
                raise APIException(f"Forbidden file type. {self.allowed_files} only", 403)

            Path(full_path).mkdir(parents=True, exist_ok=True)
            file.save(full_path + filename)

            return self.path + filename

    def update(self):
        result = self.create()

        if self.instance:
            if self.many:
                result = self.instance + result
            else:
                old_full_path = Config.UPLOAD_FOLDER + self.instance
                remove(old_full_path)

        return result

