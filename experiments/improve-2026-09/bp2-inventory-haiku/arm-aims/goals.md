# Inventory Reservation Service — Goals

**Date:** 2026-09-20

## Core scenarios

1. **Stock addition:** A SKU enters inventory with an initial quantity. Available units for that SKU equal the added quantity.
2. **Reservation:** A caller reserves a quantity of a SKU, receiving a unique reservation ID. The reserved quantity is held; available units decrease by the reserved amount.
3. **Release:** A caller releases a reservation by ID. The held units return to available. Releasing an already-released or unknown ID is a no-op (idempotent).
4. **Availability query:** A caller queries how many units of a SKU are available now (not reserved). For unknown SKUs, the answer is 0.

## Product intent

The service is a single-module in-memory inventory manager. It models the core operation: reserve stock for fulfillment, release on cancellation, query current availability.

## Out of scope

- Persistence (not required by the card)
- Concurrent/multi-threaded safety (in-memory, assumed single-threaded use in stage 1)
- SKU lifecycle management or validation
- Reservation expiration or time-based rules
