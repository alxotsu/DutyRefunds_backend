from api.models import db
from api.models import *

__all__ = ['main']


def main():
    db.create_all()

    couriers = [
        Courier(name="UPS", drl_pattern='docpatterns/DRL_other.pdf',
                required_documents={
                    "proof_of_refund": {"types": [".pdf", ".jpg"], "required": True},
                },
                drl_content={
                    "username": {"type": "string", "x": 150, "y": 735},
                    "date": {"type": "string", "x": 125, "y": 735},
                    "signature": {"type": "image", "x": 125, "y": 735, "w": 300, "h": 200},
                }),

        Courier(name="DHL", drl_pattern='docpatterns/DRL_other.pdf',
                required_documents={
                    "proof_of_refund": {"types": [".pdf", ".jpg"], "required": True},
                },
                drl_content={
                    "username": {"type": "string", "x": 150, "y": 735},
                    "date": {"type": "string", "x": 125, "y": 735},
                    "signature": {"type": "image", "x": 125, "y": 735, "w": 300, "h": 200},
                }),

        Courier(name="Fedex", drl_pattern='docpatterns/DRL_other.pdf',
                required_documents={
                    "proof_of_refund": {"types": [".pdf", ".jpg"], "required": True},
                    "duty_tax_invoice": {"types": [".pdf", ".jpg"], "required": False},
                    "supplementary_declaration_acceptance_advice": {"types": [".pdf", ".jpg"], "required": False},
                    "commercial_invoice": {"types": [".pdf", ".jpg"], "required": False},
                },
                drl_content={
                    "username": {"type": "string", "x": 150, "y": 735},
                    "date": {"type": "string", "x": 125, "y": 735},
                    "signature": {"type": "image", "x": 125, "y": 735, "w": 300, "h": 200},
                }),
        Courier(name="Parcelforce", drl_pattern='docpatterns/DRL_Parcelforce.pdf',
                required_documents={
                    "proof_of_refund": {"types": [".pdf", ".jpg"], "required": True},
                    "duty_tax_invoice": {"types": [".pdf", ".jpg"], "required": False},
                    "supplementary_declaration_acceptance_advice": {"types": [".pdf", ".jpg"], "required": False},
                    "commercial_invoice": {"types": [".pdf", ".jpg"], "required": False},
                },
                drl_content={
                    "username": {"type": "string", "x": 150, "y": 735},
                    "date": {"type": "string", "x": 125, "y": 735},
                    "signature": {"type": "image", "x": 125, "y": 735, "w": 300, "h": 200},
                    "traking_number": {"type": "string", "x": 125, "y": 735},
                }),
    ]

    for courier in couriers:
        db.session.add(courier)

    db.session.commit()


if __name__ == '__main__':
    main()
