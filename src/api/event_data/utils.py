from src.db.db_models import Donation
from src.enums import DonationType


def get_donation_type(d: Donation) -> DonationType:
    if d.amount >= 5000:
        return DonationType.BIG
    return DonationType.SMALL
