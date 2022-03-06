from datetime import datetime
import requests
from flask import send_from_directory
from flasgger import swag_from
from flask_mail import Mail, Message
from flask_restful import request
from app.bases import *
from app import mail, Config
from api.models import Authtoken, User, EmailConfirm
from api.serializers import *
from api.models import db
from api.models import *


__all__ = ['FileView', 'AccountView', 'TokenView', 'CaseCreateView',
           'CaseEditorView']


class FileView(GenericView):
    @swag_from(Config.SWAGGER_FORMS + 'fileview_get.yml')
    def get(self, path):
        return send_from_directory(Config.UPLOAD_FOLDER, path)


class AccountView(GenericView, GetMixin, CreateMixin, UpdateMixin, DeleteMixin):
    serializer_class = UserSerializer
    get = swag_from(Config.SWAGGER_FORMS + 'accountsview_get.yml')(GetMixin.get)
    delete = swag_from(Config.SWAGGER_FORMS + 'accountsview_delete.yml')(DeleteMixin.delete)

    @swag_from(Config.SWAGGER_FORMS + 'accountsview_put.yml')
    def put(self, *args, **kwargs):
        return self._change('update')

    @swag_from(Config.SWAGGER_FORMS + 'accountsview_post.yml')
    def post(self, *args, **kwargs):
        request.request_data["bank_name"] = request.request_data["username"]
        request.request_data["timeline"] = {"registration": datetime.utcnow().isoformat()}
        return self._change('create')

    def put_perms(self):
        if "email" in request.request_data:
            if User.query.filter_by(email=request.request_data['email']).first():
                raise APIException("User with this email already exist", 403)
        for field in ("timeline",):
            request.request_data.pop(field, None)

    def post_perms(self):
        if User.query.filter_by(email=request.request_data['email']).first():
            raise APIException("User with this email already exist", 403)
        for field in ("bank_name", "card_number",
                      "bank_code", "timeline"):
            request.request_data.pop(field, None)

    def get_object(self):
        if request.method == 'POST':
            return None
        if request.user:
            return request.user
        raise APIException("Not authorized", 403)

    def _change(self, method: str):
        instance = self.get_object()
        serializer = self.serializer_class(instance=instance, data=request.request_data)
        instance = getattr(serializer, method)()
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


class TokenView(GenericView):
    def get_object(self):
        email = request.request_data['email']
        confirm_obj = EmailConfirm.query.filter_by(email=email).first()
        if confirm_obj is None:
            user = User.query.filter_by(email=email).one()
            confirm_obj = EmailConfirm(email=email, user=user)
        return confirm_obj

    @swag_from(Config.SWAGGER_FORMS + 'tokenview_get.yml')
    def get(self):
        confirm_obj = self.get_object()
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
    def post(self):
        confirm_obj = self.get_object()
        if confirm_obj.key == request.request_data["key"]:
            user = confirm_obj.user
            user.email = confirm_obj.email
            token = Authtoken(user=user)

            db.session.add(token)
            for obj in user.email_confirm_obj:
                db.session.delete(obj)
            db.session.commit()

            return {"token": token.key, "user_id": token.user_id}, 200
        else:
            return "Wrong key", 400


class CaseCreateView(GenericView, GetMixin, CreateMixin):
    serializer_class = CaseSerializer

    @swag_from(Config.SWAGGER_FORMS + 'CaseCreateView_get.yml')
    def get(self):
        response = requests.post('https://www.api.simplyduty.com/api/duty/gethscode',
                                 headers={"x-api-key": Config.SIMPLE_DUTY_KEY},
                                 json={
                                     "FullDescription": request.request_data["description"],
                                     "OriginCountryCode": "IT",
                                     "DestinationCountryCode": "GB"
                                 }).json()
        if "error" in response:
            raise APIException(response.json()["error"]["code"], 500)

        response = requests.post('https://www.api.simplyduty.com/api/duty/calculate',
                                 headers={"x-api-key": Config.SIMPLE_DUTY_KEY},
                                 json={
                                     "OriginCountryCode": "IT",
                                     "DestinationCountryCode": "GB",
                                     "HSCode": response["HSCode"],
                                     "Quantity": 1,
                                     "Value": request.request_data["cost"],
                                     "Shipping": 0,
                                     "Insurance": 0,
                                     "OriginCurrencyCode": "GBP",
                                     "DestinationCurrencyCode": "GBP",
                                     "ContractInsuranceType": "cIF",
                                 }).json()
        if "error" in response:
            raise APIException(response.json()["error"]["code"], 500)

        courier = Courier.query.filter_by(name=request.request_data['courier_name']).one()
        response = {
            "duty": response["Duty"],
            "duty_rate": response["Duty"] / request.request_data["cost"],
            "vat": response["VAT"],
            "courier_fee": courier.calc_cost(response["Duty"], response["VAT"]),
            "duty_owned": response["Duty"] + response["VAT"],
            "service_fee": (response["Duty"] + response["VAT"])*0.15,
            "get_back": (response["Duty"] + response["VAT"])*0.85
        }
        return response, 200

    @swag_from(Config.SWAGGER_FORMS + 'CaseCreateView_post.yml')
    def post(self):
        response = self.get()[0]
        courier = Courier.query.filter_by(name=request.request_data['courier_name']).one()
        request.request_data = {
            "user_id": request.user.id,
            "courier": courier,
            "duty": response["duty_rate"],
            "vat": response["vat"],
            "refund": response["get_back"],
            "cost": request.request_data["cost"],
            "service_fee": response["service_fee"],
            "description": request.request_data["description"],
            "tracking_number": request.request_data["tracking_number"],
        }
        return super(CaseCreateView, self).post()

    def post_perms(self):
        if request.user is None:
            raise APIException("Not authorized", 403)


class CaseEditorView(GenericView, GetMixin, UpdateMixin):
    serializer_class = CaseSerializer

    get = swag_from(Config.SWAGGER_FORMS + 'CaseEditorView_get.yml')(GetMixin.get)
    put = swag_from(Config.SWAGGER_FORMS + 'CaseEditorView_put.yml')(UpdateMixin.put)

    def get_perms(self, id):
        if request.user is None:
            raise APIException("Not authorized", 403)
        case = self.get_object(id=id)
        if case.user_id != request.user.id:
            raise APIException("Not your case", 403)

    def put_perms(self, id):
        self.get_perms(id)
        case = self.get_object(id=id)
        if case.status != Case.STATUS.NEW:
            raise APIException("You can not edit this case", 403)

        for field in ("user_id", "courier", "duty", "vat",
                      "refund", "cost", "service_fee", "description",
                      "tracking_number", "timeline", "hmrc_payment",
                      "epu_number", "import_entry_number", "import_entry_date",
                      "custom_number", "status",):
            request.request_data.pop(field, None)

