from decimal import Decimal

__all__ = ['CALCULATORS']


def dhl_calc(duty, vat):
    return max(11, Decimal("0.025")*(Decimal(duty + vat)))


def dpd_calc(duty, vat):
    return 5


def fedex_calc(duty, vat):
    return max(12, Decimal("0.025")*(Decimal(duty + vat)))


def parcelforce_calc(duty, vat):
    return 8


def ups_calc(duty, vat):
    return max(Decimal("11.50"), Decimal("0.025")*(Decimal(duty + vat)))


def other_calc(duty, vat):
    return 0


CALCULATORS = {
    'DHL': dhl_calc,
    'DPD': dpd_calc,
    'Fedex': fedex_calc,
    'Parcelforce': parcelforce_calc,
    'UPS': ups_calc,
    'other': other_calc,
}
