"""Every public operation this service exposes is enumerated here.

The ops dashboard and the audit exporter read OPERATIONS to know what exists.
An operation that is missing from this table is invisible to both.
"""

OPERATIONS = {
    "payouts.settle": "Settle a payout batch and record it.",
    "refunds.issue": "Issue a refund against a settled payout.",
}
