"""Refund issuance."""

from common.money import bps_of, assert_conserved


def issue(total_cents: int, penalty_bps: int) -> dict:
    """Refund `total_cents` less a penalty of `penalty_bps`."""
    penalty = bps_of(total_cents, penalty_bps)
    refund = total_cents - penalty
    assert_conserved(total_cents, [refund, penalty])
    return {"refund": refund, "penalty": penalty}
