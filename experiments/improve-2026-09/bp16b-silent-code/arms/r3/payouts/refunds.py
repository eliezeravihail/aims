"""Refund issuance."""

from common.money import bps_of


def issue(total_cents: int, penalty_bps: int) -> dict:
    penalty = bps_of(total_cents, penalty_bps)
    return {"refund": total_cents - penalty, "penalty": penalty}
