from datetime import datetime
from decimal import Decimal
from app.bases.rest.serializers import *
from app.bases.exceptions import APIException
from app import Config
from api.models import *


__all__ = ['UserSerializer', 'CaseSerializer', 'CalculateResultSerializer',
           'DocumentSerializer']


class UserSerializer(ModelSerializer):
    model = User
    fields = ["id", "username", "email", "subs_on_marketing",
              "role", "bank_name", "card_number", "bank_code", "registration_time"]
    read_only_fields = ["id", "role", "registration_time"]

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
        courier = self.instance.case.courier.name
        category = self.instance.category
        allowed_files = self.instance.allowed_types
        self.files = FileSerializer(f'documents/{courier}/{category}/', 'files',
                                    many=True, allowed_files=allowed_files)
        return super(DocumentSerializer, self).update()


class CourierSerializer(ModelSerializer):
    model = Courier
    fields = ["id", "name"]

    def create(self):
        return self.data

    def update(self):
        return self.instance


class CaseSerializer(ModelSerializer):
    model = Case
    fields = ["id", "user_id", "courier", "result", "tracking_number",
              "signature", "created_at", "hmrc_payment", "epu_number",
              "import_entry_number", "import_entry_date", "custom_number",
              "status", "documents"]
    read_only_fields = ["id", "documents", "created_at"]

    signature = FileSerializer("signatures/", "signature", allowed_files=('.jpg',))
    documents = DocumentSerializer(many=True)
    courier = CourierSerializer()
    result = CalculateResultSerializer()

    def create(self):
        instance = super(CaseSerializer, self).create()
        for category, params in instance.courier.required_documents.items():
            document = Document(category=category,
                                required=params["required"],
                                allowed_types=params["types"])
            instance.documents.append(document)
        return instance
