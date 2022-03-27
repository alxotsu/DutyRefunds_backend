from pathlib import Path
import io
import os
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

# For HMRC
# signature: 125, 30, 300, 200)
# 150, 735, "username"
# 100, 243, "date")
# 207, 562, "epu_number"
# 243, 549, "entry_number"
# 195, 537, "entry_date"
