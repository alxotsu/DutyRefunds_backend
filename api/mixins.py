from pathlib import Path
import io
from datetime import datetime
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfFileReader, PdfFileWriter
from app import Config
from app.bases import APIException

__all__ = ['DRLGeneratorMixin']


class DRLGeneratorMixin:
    @staticmethod
    def generate_drl(pattern_path, content):
        packet = io.BytesIO()
        can = Canvas(packet, pagesize=A4)
        for insert in content:
            if content["type"] == "string":
                can.drawString(content["x"], content["y"], content["content"])
            elif content["type"] == "image":
                can.drawImage(content["content"], content["x"], content["y"],
                              content["w"], content["h"])
            else:
                raise APIException("Unknown generator content type", 500)

        can.save()

        new_pdf = PdfFileReader(packet)

        pattern_pdf = PdfFileReader(Config.UPLOAD_FOLDER + pattern_path)
        output = PdfFileWriter()

        page = pattern_pdf.getPage(0)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)

        path = f"DLRs/DRL-{datetime.utcnow().isoformat().replace(':', '-')}.pdf"
        with Path(Config.UPLOAD_FOLDER + path).open(mode='wb') as output_file:
            output.write(output_file)

        return path

# For HMRC
# signature: 125, 30, 300, 200)
# 150, 735, "username"
# 100, 243, "date")
# 207, 562, "epu_number"
# 243, 549, "entry_number"
# 195, 537, "entry_date"
