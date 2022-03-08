from api.models import db
from api.models import *

__all__ = ['main']


def main():
    db.create_all()

    couriers = [
        Courier(name="UPS", required_documents={
            "proof_of_refund": {
                "types": [
                    ".pdf", ".jpg"
                ],
                "required": True
            }
        }),
        Courier(name="DHL", required_documents={
            "proof_of_refund": {
                "types": [
                    ".pdf", ".jpg"
                ],
                "required": True
            }
        }),
        Courier(name="Fedex", required_documents={
            "proof_of_refund": {
                "types": [
                    ".pdf", ".jpg"
                ],
                "required": True
            },
            "duty_tax_invoice": {
                "types": [
                    ".pdf", ".jpg"
                ],
                "required": False
            },
            "supplementary_declaration_acceptance_advice": {
                "types": [
                    ".pdf", ".jpg"
                ],
                "required": False
            },
            "commercial_invoice": {
                "types": [
                    ".pdf", ".jpg"
                ],
                "required": False
            }
        }),
        Courier(name="Parcelforce", required_documents={
            "proof_of_refund": {
                "types": [
                    ".pdf", ".jpg"
                ],
                "required": True
            },
            "duty_tax_invoice": {
                "types": [
                    ".pdf", ".jpg"
                ],
                "required": True
            },
            "supplementary_declaration_acceptance_advice": {
                "types": [
                    ".pdf", ".jpg"
                ],
                "required": True
            },
            "commercial_invoice": {
                "types": [
                    ".pdf", ".jpg"
                ],
                "required": True
            }
        })
    ]

    for courier in couriers:
        db.session.add(courier)

    db.session.commit()


if __name__ == '__main__':
    main()
