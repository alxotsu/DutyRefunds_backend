
__all__ = ['CALCULATORS']


def dhl_calc(duty: int, vat: int) -> int:
    return max(1100, int(0.025*(duty + vat)))


def dpd_calc(duty: int, vat: int) -> int:
    return 500


def fedex_calc(duty: int, vat: int) -> int:
    return max(1200, int(0.025*(duty + vat)))


def parcelforce_calc(duty: int, vat: int) -> int:
    return 800


def ups_calc(duty: int, vat: int) -> int:
    return max(1150, int(0.025*(duty + vat)))


def other_calc(duty: int, vat: int) -> int:
    return 0


CALCULATORS = {
    'DHL': dhl_calc,
    'DPD': dpd_calc,
    'Fedex': fedex_calc,
    'Parcelforce': parcelforce_calc,
    'UPS': ups_calc,
    'other': other_calc,
}
