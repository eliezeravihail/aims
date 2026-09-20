# Inventory Reservation Service — Architecture

**Date:** 2026-09-20

## Core entity: Inventory

A single class `Inventory` that encapsulates:
- A per-SKU **stock ledger**: total units added for each SKU
- A **reservation store**: each reservation ID → (SKU, qty) map
- A **derived state function**: `available(sku) = total_added(sku) - sum of reserved qty for that SKU`

## The availability invariant (R1)

**Rule:** For each SKU, available units never go negative and never exceed total added.

**Owner:** The Inventory class enforces this by construction:
- `add_stock(sku, qty)`: increments total_added for the SKU. Only positive quantities accepted.
- `reserve(sku, qty)`: checks precondition (qty <= available). Only if check passes, creates a new reservation record and generates a unique ID.
- `release(reservation_id)`: returns the reserved units to available by removing the reservation from the store.

**Defense:** The available value is computed (never stored), so it always reflects current state.

## Reservation IDs (R3)

- Opaque: generated as UUIDs, not reconstructible from external data
- Unique: each reservation gets a fresh UUID
- Independent of quantity or SKU: the ID does not encode data; it is a pure identity token

## Failure mode: InsufficientStock (R4)

If a caller reserves more than `available(sku)`, the operation:
- Raises `InsufficientStock` exception (per the public interface)
- Makes no state change (atomicity: precondition checked before any state mutation)

## Idempotency: Release (R2's complement)

If a caller releases an unknown or already-released reservation ID:
- No exception is raised
- State is unchanged (no-op)
- This is explicitly idempotent per the spec

## Public API (exact signatures from card)

```python
class InsufficientStock(Exception):
    pass

class Inventory:
    def __init__(self) -> None
    def add_stock(self, sku: str, qty: int) -> None
    def available(self, sku: str) -> int
    def reserve(self, sku: str, qty: int) -> str
    def release(self, reservation_id: str) -> None
```

## Design rationale

The design is minimal: one class, one set of owned rules (the availability invariant). No abstractions are introduced beyond what the four operations require. The reservation store is the single source of truth for active reservations; available is always derived, so it cannot drift from the true state.
