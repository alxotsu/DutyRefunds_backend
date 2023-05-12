from decimal import Decimal
from app.bases.rest.serializers import *
from api.models import *


__all__ = ['UserSerializer', 'CaseSerializer', 'CalculateResultSerializer',
           'DocumentSerializer', 'CaseShortSerializer']


class UserSerializer(ModelSerializer):
    model = User
    fields = ["id", "username", "email", "subs_on_marketing",
              "role", "bank_name", "card_number", "bank_code", "registration_time"]
    read_only_fields = ["id", "role", "registration_time"]

    def create(self):
        email = self.data.pop("email")
        instance = super(UserSerializer, self).create()

        EmailConfirm(user=instance, email=email).create()

        return instance

    def update(self):
        email = self.data.pop("email", None)
        instance = super(UserSerializer, self).update()

        if email:
            if instance.email_confirm_obj.all():
                email_confirm_instance = instance.email_confirm_obj[0]
                email_confirm_instance.update_key()
            else:
                email_confirm_instance = EmailConfirm(user=instance)

            email_confirm_instance.email = email

        return instance


class CalculateResultSerializer(ModelSerializer):
    model = CalculateResult
    fields = ['id', 'cost', 'duty', 'vat', 'courier_id', 'description']
    read_only_fields = ['id']

    def serialize(self):
        return {
            "id": self.instance.id,
            "duty": float(self.instance.duty),
            "duty_rate": float(self.instance.duty / self.instance.cost),
            "vat": float(self.instance.vat),
            "courier_fee": float(self.instance.calc_cost()),
            "duty_owned": float(self.instance.duty + self.instance.vat),
            "service_fee": float((self.instance.duty + self.instance.vat) * Decimal("0.15")),
            "get_back": float((self.instance.duty + self.instance.vat) * Decimal("0.85")),
            "description": self.instance.description,
            "courier_name": self.instance.courier.name,
        }

    def create(self):
        return self.data


class DocumentSerializer(ModelSerializer):
    """
    Only for update and serialize
    """
    model = Document
    fields = ["category", "required", "allowed_types", "files"]
    read_only_fields = ["category", "required", "allowed_types"]

    def update(self):
        courier = self.instance.case.result.courier.name
        category = self.instance.category
        allowed_files = self.instance.allowed_types
        self.files = FileSerializer(f'documents/{courier}/{category}/', 'file',
                                    many=True, allowed_files=allowed_files)
        return super(DocumentSerializer, self).update()


class CaseSerializer(ModelSerializer):
    model = Case
    fields = ["id", "user", "user_id", "result", "tracking_number",
              "signature", "drl_document", "hmrc_document", "created_at",
              "hmrc_payment", "custom_number", "status", "documents"]
    read_only_fields = ["id", "user_id", "drl_document", "hmrc_document",
                        "created_at", "hmrc_payment", "status", "documents"]
    write_only_fields = ["user", "signature"]

    signature = FileSerializer("signatures/", "signature", allowed_files=('.jpg', '.png'))
    drl_document = FileSerializer("signatures/", "signature", allowed_files=('.pdf',))
    hmrc_document = FileSerializer("signatures/", "signature", allowed_files=('.pdf',))
    documents = DocumentSerializer(many=True)
    result = CalculateResultSerializer()

    def create(self):
        instance = super(CaseSerializer, self).create()
        for category, params in instance.result.courier.required_documents.items():
            document = Document(category=category,
                                required=params["required"],
                                allowed_types=params["types"])
            instance.documents.append(document)
        return instance


class CaseShortSerializer(CaseSerializer):
    fields = ["id", "user_id", "tracking_number", "created_at", "status"]
    read_only_fields = ["id", "documents", "created_at"]
