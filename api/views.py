from datetime import datetime, timedelta
import requests
from flask import send_from_directory
from flasgger import swag_from
from flask_restful import request
from sqlalchemy import func

from app.bases import *
from app import Config
from api.serializers import *
from api.models import db
from api.models import *
from api.mixins import *

__all__ = ['FileView', 'AccountView', 'TokenView', 'CaseCreateView',
           'CaseEditorView', 'CaseDocumentAdder', 'CaseViewSet',
           'AdminCaseSubmitView']


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

        if instance.email_confirm_obj.all():
            send_confirm_email(instance.email_confirm_obj[0])

        serializer.instance = instance
        return serializer.serialize(), 200


class TokenView(GenericView):
    def get_object(self):
        email = request.request_data['email']
        confirm_obj = EmailConfirm.query.filter_by(email=email).first()
        if confirm_obj is None:
            user = User.query.filter_by(email=email).one()
            confirm_obj = EmailConfirm(email=email, user=user)
        elif datetime.utcnow() - confirm_obj.created_at < timedelta(minutes=1) and \
                request.method == 'GET':
            raise APIException("Key was created less than minute ago.", 403)

        return confirm_obj

    @swag_from(Config.SWAGGER_FORMS + 'tokenview_get.yml')
    def get(self):
        confirm_obj = self.get_object()
        confirm_obj.update_key()

        db.session.add(confirm_obj)
        db.session.commit()

        send_confirm_email(confirm_obj)

        return {'result': "Ok"}, 200

    @swag_from(Config.SWAGGER_FORMS + 'tokenview_post.yml')
    def post(self):
        confirm_obj = self.get_object()
        if confirm_obj.key == request.request_data["key"]:
            user = confirm_obj.user
            user.email = confirm_obj.email
            if user.authtoken:
                token = user.authtoken[0]
                token.update_key()
            else:
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
            raise APIException(response["error"]["code"], 500)

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
            raise APIException(response["error"]["code"], 500)

        courier = Courier.query.filter_by(name=request.request_data['courier_name']).one()
        data = {
            'cost': request.request_data["cost"],
            'duty': response["Duty"],
            'vat': response["VAT"],
            'courier_id': courier.id,
            'description': request.request_data["description"],
        }
        result = CalculateResult(**data)
        db.session.add(result)
        db.session.commit()

        serializer = CalculateResultSerializer(instance=result)

        return serializer.serialize(), 200

    @swag_from(Config.SWAGGER_FORMS + 'CaseCreateView_post.yml')
    def post(self):
        if request.user is None:
            if EmailConfirm.query.filter_by(email=request.request_data["email"]).first():
                raise APIException("User with this email already exist", 403)
            if User.query.filter_by(email=request.request_data["email"]).first():
                raise APIException("User with this email already exist", 403)

            serializer = UserSerializer(data={
                "username": request.request_data["username"],
                "email": request.request_data["email"],
                "subs_on_marketing": bool(request.request_data.get("subs_on_marketing", False)),
                "bank_name": request.request_data["username"],
            })
            user = serializer.create()
            db.session.add(user)
        else:
            user = request.user
            if "subs_on_marketing" in request.request_data:
                user.subs_on_marketing = request.request_data["subs_on_marketing", False]
                db.session.add(user)

        result = CalculateResult.query.get(int(request.request_data['result_id']))
        if result is None:
            raise APIException("Calculate result is not found", 404)

        request.request_data = {
            "user": user,
            "result": result,
            "tracking_number": request.request_data["tracking_number"],
            "signature": request.request_data["signature"]
        }
        case = super(CaseCreateView, self).post()

        send_case(case[0]['id'])
        send_reminder.apply_async((case[0]['id'],), eta=datetime.utcnow() + timedelta(minutes=2),
                                  queue='sending')

        return case


class CaseEditorView(GenericView, GetMixin, UpdateMixin):
    serializer_class = CaseSerializer

    def get_queryset(self, *args, **kwargs):
        return request.user.cases

    get = swag_from(Config.SWAGGER_FORMS + 'CaseEditorView_get.yml')(GetMixin.get)

    def put(self, id):
        case = self.get_object(id=id)
        if case.status == Case.STATUS.PAID:
            raise APIException("This case already done", 403)

        req_docs = request.request_data.get('request_docs', False)
        if case.status == Case.STATUS.NEW:
            if req_docs and not case.result.courier.email:
                raise APIException(f"Cannot request documents with this courier", 403)
            if not req_docs:
                for document in case.documents:
                    if document.required and not document.files:
                        raise APIException(f"{document.category} is not added", 403)

        if not case.drl_document:
            content = list()
            for key, insert in case.result.courier.drl_content.items():
                content.append(insert.copy())
                if key == 'username':
                    content[-1]['content'] = request.user.username
                elif key == 'date':
                    content[-1]['content'] = datetime.utcnow().isoformat()[0:10]
                elif key == 'signature':
                    content[-1]['content'] = case.signature
                elif key == 'tracking_number':
                    content[-1]['content'] = case.tracking_number

            drl = generate_drl(case.result.courier.drl_pattern, content)
            case.drl_document = drl

        if case.status == Case.STATUS.NEW:
            if req_docs:
                case.status = Case.STATUS.WAITING
            else:
                case.status = Case.STATUS.SUBMISSION
                send_request_documents(case)
                send_case_submission(case)

        airtable_id = send_to_airtable(case)
        case.airtable_id = airtable_id

        db.session.add(case)
        db.session.commit()

        serializer = self.serializer_class(instance=case)
        return serializer.serialize(), 200

    def get_perms(self, id):
        if request.user is None:
            raise APIException("Not authorized", 403)
        self.get_object(id=id)

    put_perms = get_perms


class CaseDocumentAdder(GenericView, UpdateMixin):
    serializer_class = DocumentSerializer

    def put_perms(self, case_id, category):
        if request.user is None:
            raise APIException("Not authorized", 403)

        if request.user.role == User.ROLE.ADMIN:
            case = Case.query.filter(Case.status > Case.STATUS.NEW,
                                     Case.status < Case.STATUS.PAID,
                                     Case.id == case_id).first()
        else:
            case = request.user.cases.filter_by(id=case_id).first()
        if case is None:
            raise APIException(f"Case #{case_id} is not found", 404)
        if case.status >= Case.STATUS.SUBMITTED:
            raise APIException("You can not add documents now", 403)
        self._object = case.documents.filter_by(category=category).first()
        if self._object is None:
            raise APIException(f"{category} is not found", 404)


class CaseViewSet(GenericView, ViewSetMixin):
    serializer_class = CaseShortSerializer

    def get_queryset(self, *args, **kwargs):
        cases = request.user.cases
        if "date" in request.request_data:
            date_1 = datetime.strptime(request.request_data["date"], "%Y-%m-%d")
            if "date2" in request.request_data:
                date_2 = datetime.strptime(request.request_data["date2"], "%Y-%m-%d")
            else:
                date_2 = datetime.strptime(request.request_data["date"], "%Y-%m-%d")
            date_2 += timedelta(days=1)
            cases = cases.filter(Case.created_at >= date_1, Case.created_at < date_2)
        if "status" in request.request_data:
            cases = cases.filter_by(status=int(request.request_data["status"]))
        if "search" in request.request_data:
            regex = f"%{request.request_data['search'].lower()}%"
            track_cases = cases.filter(func.lower(Case.tracking_number).like(regex))
            desc_cases = cases.join(Case.result).filter(func.lower(CalculateResult.description).like(regex))
            courier_cases = cases.join(Case.result).join(CalculateResult.courier).filter(func.lower(Courier.name).like(regex))

            cases = track_cases.union_all(desc_cases).union_all(courier_cases).order_by(Case.id)

        return cases

    def get_perms(self):
        if request.user is None:
            raise APIException("Not authorized", 403)


class AdminCaseSubmitView(GenericView, UpdateMixin):
    def get_queryset(self, *args, **kwargs):
        return Case.query.filter(Case.status > Case.STATUS.NEW,
                                 Case.status < Case.STATUS.PAID)

    serializer_class = CaseShortSerializer

    def put(self, id, step):
        instance = self.get_object(id=id)

        if step == 'submit':
            if instance.status not in (Case.STATUS.WAITING, Case.STATUS.SUBMISSION):
                raise APIException("Case is not on submission", 403)

            if instance.status == Case.STATUS.WAITING:
                for document in instance.documents:
                    if document.required and not document.files:
                        raise APIException(f"{document.category} is not added", 403)
                instance.status = Case.STATUS.SUBMISSION

            instance.epu_number = request.request_data["epu_number"]
            instance.import_entry_number = request.request_data["import_entry_number"]
            instance.import_entry_date = request.request_data["import_entry_date"]

            content = (
                {"type": "image", "x": 125, "y": 30, "w": 300, "h": 200, "content": instance.signature},
                {"type": "string", "x": 150, "y": 735, "content": instance.user.username},
                {"type": "string", "x": 100, "y": 243, "content": datetime.utcnow().isoformat()[0:10]},
                {"type": "string", "x": 207, "y": 562, "content": str(request.request_data["epu_number"])},
                {"type": "string", "x": 243, "y": 549, "content": str(request.request_data["import_entry_number"])},
                {"type": "string", "x": 195, "y": 537, "content": request.request_data["import_entry_date"]},
            )
            drl = generate_drl('docpatterns/DRL_HMRC.pdf', content)

            instance.hmrc_document = drl

        elif step == 'hmrc':
            if instance.status != Case.STATUS.SUBMITTED:
                raise APIException("Case is not submitted", 403)
            instance.hmrc_payment = request.request_data["hmrc_payment"]
            send_to_hmrc(instance)

        elif step == 'done':
            if instance.status != Case.STATUS.HMRC_AGREED:
                raise APIException("HMRC for the Case is not agreed", 403)

        else:
            raise APIException("Unexpected 'step' value", 400)

        instance.status += 1
        db.session.add(instance)
        db.session.commit()

        send_to_airtable(instance)

        return {'result': "Ok"}, 200

    def put_perms(self, *args, **kwargs):
        if request.user is None:
            raise APIException("Not authorized", 403)
        if request.user.role != User.ROLE.ADMIN:
            raise APIException("Only for staff", 403)
