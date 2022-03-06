from datetime import datetime
from app.bases.rest.serializers import *
from app.bases.exceptions import APIException
from app import Config
from api.models import *


__all__ = ['UserSerializer', 'CaseSerializer']


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


class DocumentSerializer(ModelSerializer):
    """
    Only for update and serialize
    """
    model = Document
    fields = ["category", "files", "required"]

    def __init__(self, category=None, courier=None, allowed_files=None, *args, **kwargs):
        super(DocumentSerializer, self).__init__(*args, **kwargs)
        if not self.many:
            self.files = FileSerializer(f'documents/{courier}/', category,
                                        many=True, allowed_files=allowed_files)


class CourierSerializer(ModelSerializer):
    model = Courier
    fields = ["id", "name"]

    def create(self):
        instance = self.model.query.get(self.data["id"])
        if instance is None:
            raise APIException("Unknown Courier ID.", 404)
        return instance

    def update(self):
        return self.instance


class CaseSerializer(ModelSerializer):
    model = Case
    fields = ["id", "user_id", "courier", "duty", "vat",
              "refund", "cost", "service_fee", "description",
              "tracking_number", "signature", "timeline", "hmrc_payment",
              "epu_number", "import_entry_number", "import_entry_date",
              "custom_number", "status", "documents"]
    read_only_fields = ["id", "documents", "courier"]

    signature = FileSerializer("signatures/", "signature", allowed_files=('.jpg',))
    documents = DocumentSerializer(many=True)
    courier = CourierSerializer()

    def create(self):
        courier = self.data["courier"]
        instance = super(CaseSerializer, self).create()
        instance.courier = courier
        for category, params in courier.required_documents.items():
            document = Document(category=category,
                                required=params["required"],
                                allowed_types=params["types"])
            instance.documents.append(document)
        instance.timeline = {
            "created": datetime.utcnow().isoformat()
        }
        return instance
