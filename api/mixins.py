from decimal import Decimal
from pathlib import Path
import io
import requests
from datetime import datetime, timedelta
from flask import request
from smtplib import SMTPRecipientsRefused
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from flask_mail import Message
from PyPDF2 import PdfFileReader, PdfFileWriter
from app import mail, Config, db, celery, app
from app.bases import APIException
from api.models import *

__all__ = ['generate_drl', 'send_to_airtable', 'send_confirm_email',
           'send_confirm_email_with_case', 'send_reminder']


def generate_drl(pattern_path, content):
    packet = io.BytesIO()
    can = Canvas(packet, pagesize=A4)
    for insert in content:
        if insert["type"] == "string":
            can.drawString(insert["x"], insert["y"], insert["content"])
        elif insert["type"] == "image":
            can.drawImage(Config.UPLOAD_FOLDER + insert["content"],
                          insert["x"], insert["y"], insert["w"], insert["h"])
        else:
            raise APIException("Unknown generator content type", 500)

    can.save()

    new_pdf = PdfFileReader(packet)

    pattern_pdf = PdfFileReader(Config.UPLOAD_FOLDER + pattern_path)
    output = PdfFileWriter()

    page = pattern_pdf.getPage(0)
    page.mergePage(new_pdf.getPage(0))
    output.addPage(page)

    path = Path(Config.UPLOAD_FOLDER + "DRLs")
    filename = f"DRL-{datetime.utcnow().isoformat().replace(':', '-')}.pdf"
    path.mkdir(parents=True, exist_ok=True)
    path = path / filename
    with path.open(mode='wb') as output_file:
        output.write(output_file)

    return f"DRLs/{filename}"


def send_to_airtable(case):
    case_docs = ''
    for doc in case.documents:
        for file in doc.files:
            case_docs += f"{request.host_url}upload/{file}\n"

    data = {
        "case_id": case.id,
        "tracking_number": case.tracking_number,
        "created_at": str(case.created_at),
        "courier": case.result.courier.name,
        "description": case.result.description,
        "cost_of_purchase": float(case.result.cost),
        "get_back": float((case.result.duty + case.result.vat) * Decimal("0.85")),
        "service_fee": float((case.result.duty + case.result.vat) * Decimal("0.15")),
        "status": case.str_status,
        "drl_document": f"{request.host_url}upload/{case.drl_document}",
        "user_bank_name": case.user.bank_name,
        "user_bank_code": case.user.bank_code,
        "user_bank_card": case.user.card_number,
        "documents_urls": case_docs,
        "hmrc_drl_document": f"{request.host_url}upload/{case.hmrc_document}" if case.hmrc_document else None,
        "hmrc_payment": float(case.hmrc_payment) if case.hmrc_payment else None,
        "epu_number": case.epu_number,
        "import_entry_number": case.import_entry_number,
        "import_entry_date": str(case.import_entry_date) if case.import_entry_date else None,
    }

    data = {
        "fields": data
    }

    if case.airtable_id:
        data['id'] = case.airtable_id

    data = {
        "records": [
            data
        ]
    }

    if case.airtable_id:
        resp = requests.patch(Config.AIRTABLE_URL, headers={"Authorization": f"Bearer {Config.AIRTABLE_API_KEY}"},
                              json=data)
    else:
        resp = requests.post(Config.AIRTABLE_URL, headers={"Authorization": f"Bearer {Config.AIRTABLE_API_KEY}"},
                             json=data)
    return resp.json()['records'][0]['id']


def send_confirm_email(confirm_obj):
    try:
        msg = Message("DutyRefunds confirm email",
                      sender=Config.MAIL_DEFAULT_SENDER,
                      recipients=[confirm_obj.email])
        msg.body = f"Confirm email code:\n{confirm_obj.key}"
        mail.send(msg)
    except SMTPRecipientsRefused as e:
        if confirm_obj.user.email is None:
            db.session.delete(confirm_obj.user)
            db.session.commit()
        raise e


def send_confirm_email_with_case(case_id):
    case = Case.query.get(case_id)
    result = case.result
    user = case.user
    confirm_obj = user.email_confirm_obj[0]

    text = f"Client’s name: {user.username}\nTracking number: {case.tracking_number}\n" \
           f"Courier: {result.courier.name}\nCost of purchase: {result.cost}\n" \
           f"Product description: {result.description}\nDuty amount: {result.duty}  " \
           f"Duty rate: {int(result.duty / result.cost * 100)}%\nVAT amount: {result.vat}  " \
           f"VAT rate: {int(result.vat / result.cost * 100)}%\n" \
           f"Courier fee: {result.calc_cost()}\n" \
           f"Refund amount: {result.duty + result.vat}\n" \
           f"Our fee: {(result.duty + result.vat) * Decimal('0.15')}\n" \
           f"Amount user will get back: {(result.duty + result.vat) * Decimal('0.85')}\n" \
           f"Confirmation code: {confirm_obj.key}\n" \
           f"https://dutyrefunds.co.uk/case/{case_id}?key={confirm_obj.key}&email={confirm_obj.email}"

    try:
        msg = Message("DutyRefunds confirm email",
                      sender=Config.MAIL_DEFAULT_SENDER,
                      recipients=[confirm_obj.email])
        msg.body = text
        mail.send(msg)
    except SMTPRecipientsRefused as e:
        if user.email is None:
            db.session.delete(user)
            db.session.commit()
        raise e


@celery.task
def send_reminder(case_id, counter=1):
    with app.app_context():
        case = Case.query.get(case_id)
        if case is None:
            return
        result = case.result
        user = case.user
        if user.email is None:
            return
        token = user.authtoken[0].key

        req_docs = ""
        for doc in case.documents:
            if not doc.files and doc.required:
                req_docs += f"\t-{doc.category.replace('_', ' ')};\n"
        if req_docs == "":
            return

        text = f"Client’s name: {user.username}\nTracking number: {case.tracking_number}\n" \
               f"Date of sending: {datetime.utcnow().isoformat()[0:10]}\n" \
               f"Required documents:\n{req_docs}" \
               f"Amount user will get back: {(result.duty + result.vat) * Decimal('0.85')}\n" \
               f"https://dutyrefunds.co.uk/case/{case_id}?token={token}"

        msg = Message(f"Document upload reminder {counter}",
                      sender=Config.MAIL_DEFAULT_SENDER,
                      recipients=[user.email])
        msg.body = text
        mail.send(msg)

        counter += 1
        if counter <= 3:
            send_reminder.apply_async((case_id, counter),
                                      eta=datetime.utcnow() + timedelta(minutes=1),
                                      queue='sending')

