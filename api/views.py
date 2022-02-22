from flask import send_from_directory
from flask_mail import Mail, Message
from flask_restful import request
from app.bases import *
from app import mail, Config
from api.models import Authtoken, User, EmailConfirm
from api.serializers import *
from api.models import db

__all__ = ['FileView', 'AccountsViewSet', 'AccountView', 'TokenView']


class FileView(GenericView):
    def get(self, *args, **kwargs):
        return send_from_directory(Config.UPLOAD_FOLDER, kwargs['path'])


class AccountsViewSet(GenericView, ViewSetMixin, CreateMixin):
    serializer_class = UserSerializer

    def post(self, *args, **kwargs):
        serializer = self.serializer_class(data=request.json)
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
        if User.query.filter_by(email=request.json['email']).all():
            raise APIException("User with this email already exist", 403)


class AccountView(GenericView, GetMixin, UpdateMixin, DeleteMixin):
    serializer_class = UserSerializer

    def put(self, *args, **kwargs):
        instance = self.get_object(*args, **kwargs)
        serializer = self.serializer_class(instance=instance, data=request.json)
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
    serializer_class = UserSerializer

    def get(self, *args, **kwargs):
        user = self.get_object(*args, **kwargs)
        if user.email_confirm_obj:
            confirm_obj = user.email_confirm_obj[0]
        else:
            confirm_obj = EmailConfirm(user=user, email=user.email)

            db.session.add(confirm_obj)
            db.session.commit()

        msg = Message("DutyRefunds confirm email",
                      sender=Config.MAIL_DEFAULT_SENDER,
                      recipients=[confirm_obj.email])
        msg.body = f"Confirm email code:\n{confirm_obj.key}"
        mail.send(msg)

        return None, 200

    def post(self, *args, **kwargs):
        user = self.get_object(*args, **kwargs)
        # TODO add email token time expire
        if user.email_confirm_obj[0].key == request.json["key"]:
            user.email = user.email_confirm_obj[0].email
            user.email_verified = True
            token = Authtoken(user=user)

            db.session.add(user)
            db.session.add(token)
            db.session.delete(user.email_confirm_obj[0])
            db.session.commit()
            return {"token": token.key, "user_id": user.id}, 200
        else:
            return "Wrong key", 400
