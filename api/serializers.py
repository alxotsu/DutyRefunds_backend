from app.bases.rest.serializers import *
from api.models import *


__all__ = ['UserSerializer']


class UserSerializer(ModelSerializer):
    model = User
    fields = ["id", "username", "email", "email_verified",
              "subs_on_marketing", "signature", "role"]
    write_only_fields = ["email_verified", "role"]
    read_only_fields = ["id"]

    signature = FileSerializer("signature")
