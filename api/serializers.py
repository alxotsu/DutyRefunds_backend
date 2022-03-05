from app.bases.rest.serializers import *
from app.bases.exceptions import APIException
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


class DocumentSerializer(ModelSerializer):
    """
    Only for update and serialize
    """
    model = Document
    fields = ["category", "files"]

    def __init__(self, category, courier, allowed_files, *args, **kwargs):
        super(DocumentSerializer, self).__init__(*args, **kwargs)
        if not self.many:
            self.files = FileSerializer(f'documents/{courier}/', category,
                                        many=True, allowed_files=allowed_files)


class CourierSerializer(ModelSerializer):
    model = Courier
    fields = ["id", "name", "required_documents"]

    def create(self):
        instance = self.model.query.get(self.data["id"])
        if instance is None:
            raise APIException("Unknown Courier ID.", 404)
        return instance

    def update(self):
        return self.instance


class CaseSerializer(ModelSerializer):
    model = Case
    fields = ["id", "user", "courier", "duty", "vat",
              "refund", "cost", "service_fee", "description",
              "tracking_number", "signature", "timeline", "hmrc_payment",
              "epu_number", "import_entry_number", "import_entry_date",
              "custom_number", "status", "documents"]
    read_only_fields = ["id", "documents", "courier"]
    write_only_fields = []

    signature = FileSerializer("signatures/", "sig")
    documents = DocumentSerializer(many=True)
    courier = CourierSerializer()

    def create(self):
        courier = Courier.query.filter_by(name=self.data["courier_name"]).one()
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
