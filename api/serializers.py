from app.bases.rest.serializers import *
from app import Config
from api.models import *


__all__ = ['UserSerializer']


class UserSerializer(ModelSerializer):
    model = User
    fields = ["id", "username", "email", "subs_on_marketing",
              "role", "bank_name", "card_number", "bank_code",
              "timeline"]
    read_only_fields = ["id", "role"]

    def create(self):
        email = self.data.pop("email")
        instance = super(UserSerializer, self).create()

        email_confirm_instance = EmailConfirm(user=instance, email=email)

        return instance

    def update(self):
        email = self.data.pop("email", None)
        instance = super(UserSerializer, self).update()

        if email:
            if instance.email_confirm_obj:
                email_confirm_instance = user.email_confirm_obj[0]
                email_confirm_instance.update_key()
            else:
                email_confirm_instance = EmailConfirm(user=instance)

            email_confirm_instance.email = email

        return instance

