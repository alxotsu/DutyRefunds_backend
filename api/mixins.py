from decimal import Decimal
from pathlib import Path
import io
import requests
from datetime import datetime

from flask import request
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfFileReader, PdfFileWriter
from app import Config
from app.bases import APIException

__all__ = ['DRLGeneratorMixin', 'AirtableRequestSenderMixin']


class DRLGeneratorMixin:
    """
        For HMRC
        125, 30, 300, 200 "signature"
        150, 735, "username"
        100, 243, "date"
        207, 562, "epu_number"
        243, 549, "entry_number"
        195, 537, "entry_date"
    """

    @staticmethod
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


class AirtableRequestSenderMixin:
    @staticmethod
    def sent_to_airtable(case):
        case_docs = ''
        for doc in case.documents:
            for file in doc.files:
                case_docs += f"{request.host_url}upload/{file}\n"

        data = {
            "case_id": case.id,
            "tracking_number": case.tracking_number,
            "created_at": str(case.created_at),
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
            "hmrc_payment": case.hmrc_payment,
            "epu_number": case.epu_number,
            "import_entry_number": case.import_entry_number,
            "import_entry_date": case.import_entry_date,
            "custom_number": case.custom_number
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
