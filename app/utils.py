from math import floor


def check_possible_payment(extra, new):
    total = extra + new
    upcoming_charges = floor(total)
    persisting_charges = total - upcoming_charges
    return upcoming_charges, round(persisting_charges, 2)
