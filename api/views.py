from flask import send_from_directory
from flasgger import swag_from
from flask_mail import Mail, Message
from flask_restful import request
from app.bases import *
from app import mail, Config
from api.models import Authtoken, User, EmailConfirm
from api.serializers import *
from api.models import db


__all__ = ['FileView', 'AccountsViewSet', 'AccountView', 'TokenView']


class FileView(GenericView):
    @swag_from(Config.SWAGGER_FORMS + 'fileview_get.yml')
    def get(self, *args, **kwargs):
        return send_from_directory(Config.UPLOAD_FOLDER, kwargs['path'])


class AccountsViewSet(GenericView, ViewSetMixin, CreateMixin):
    serializer_class = UserSerializer

    get = swag_from(Config.SWAGGER_FORMS + 'accountsviewset_get.yml')(ViewSetMixin.get)

    @swag_from(Config.SWAGGER_FORMS + 'accountsviewset_post.yml')
    def post(self, *args, **kwargs):
        serializer = self.serializer_class(data=request.request_data)
        instance = serializer.create()
        db.session.add(instance)
        db.session.commit()

        msg = Message("DutyRefunds confirm email",
                      sender=Config.MAIL_DEFAULT_SENDER,
                      recipients=[instance.email_confirm_obj[0].email])
        msg.body = f"Confirm email code:\n{instance.email_confirm_obj[0].key}"
        mail.send(msg)

        serializer.instance = instance
        return serializer.serialize(), 201

    def post_perms(self, *args, **kwargs):
        if User.query.filter_by(email=request.request_data['email']).first():
            raise APIException("User with this email already exist", 403)
        for field in ("id", "subs_on_marketing", "signature", "role"):
            request.request_data.pop(field, None)


class AccountView(GenericView, GetMixin, UpdateMixin, DeleteMixin):
    serializer_class = UserSerializer

    get = swag_from(Config.SWAGGER_FORMS + 'accountsview_get.yml')(GetMixin.get)
    delete = swag_from(Config.SWAGGER_FORMS + 'accountsview_delete.yml')(DeleteMixin.delete)

    @swag_from(Config.SWAGGER_FORMS + 'accountsview_put.yml')
    def put(self, *args, **kwargs):
        instance = self.get_object(*args, **kwargs)
        serializer = self.serializer_class(instance=instance, data=request.request_data)
        instance = serializer.update()
        db.session.add(instance)
        db.session.commit()

        if instance.email_confirm_obj:
            msg = Message("DutyRefunds confirm email",
                          sender=Config.MAIL_DEFAULT_SENDER,
                          recipients=[instance.email_confirm_obj[0].email])
            msg.body = f"Confirm email code:\n{instance.email_confirm_obj[0].key}"
            mail.send(msg)

        serializer.instance = instance
        return serializer.serialize(), 200

    def put_perms(self, *args, **kwargs):
        if request.user is None:
            raise APIException("Not authorize", 403)
        if kwargs['id'] != request.user.id:
            raise APIException("No Access", 403)

    def delete_perms(self, *args, **kwargs):
        if request.user is None:
            raise APIException("Not authorize", 403)
        if kwargs['id'] != request.user.id:
            raise APIException("No Access", 403)


class TokenView(GenericView):
    def get_object(self, *args, **kwargs):
        email = request.request_data['email']
        confirm_obj = EmailConfirm.query.filter_by(email=email).first()
        if confirm_obj is None:
            user = User.query.filter_by(email=email).one()
            confirm_obj = EmailConfirm(email=email, user=user)
        return confirm_obj

    @swag_from(Config.SWAGGER_FORMS + 'tokenview_get.yml')
    def get(self, *args, **kwargs):
        confirm_obj = self.get_object(*args, **kwargs)
        confirm_obj.update_key()

        db.session.add(confirm_obj)
        db.session.commit()

        msg = Message("DutyRefunds confirm email",
                      sender=Config.MAIL_DEFAULT_SENDER,
                      recipients=[confirm_obj.email])
        msg.body = f"Confirm email code:\n{confirm_obj.key}"
        mail.send(msg)

        return None, 200

    @swag_from(Config.SWAGGER_FORMS + 'tokenview_post.yml')
    def post(self, *args, **kwargs):
        confirm_obj = self.get_object(*args, **kwargs)
        if confirm_obj.key == request.request_data["key"]:
            confirm_obj.user.email = confirm_obj.email
            token = Authtoken(user=confirm_obj.user)

            db.session.add(confirm_obj.user)
            db.session.add(token)
            db.session.delete(confirm_obj)
            db.session.commit()

            return {"token": token.key, "user_id": token.user_id}, 200
        else:
            return "Wrong key", 400
