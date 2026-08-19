from decimal import Decimal, ROUND_HALF_UP


def round_half_up(contribution_amount, penalty_rate):
    return int((Decimal(contribution_amount) * Decimal(penalty_rate) / Decimal(100)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
