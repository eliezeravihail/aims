# Entitlements — hidden spec + oracle (never shown to an arm)

## Architectural axis under test

**Where is the allow/deny decision owned and composed?** Stage 1 makes "any role grants it" look like a
simple set membership. Stage 2 turns the decision into a *composition with precedence* (deny-overrides), a
*resolution over a hierarchy* (inheritance with specificity), and a *temporal predicate* (validity window) —
three different kinds of rule that must combine in **one** decision with a defined order.

## The correctness traps (what the judge checks) — one-owner is a PRECONDITION here (§5)

1. **Deny-as-absence cram.** Modeling deny as "the permission simply isn't granted" is **wrong**: an
   explicit deny must beat an allow that another role grants. Deny is a first-class grant effect, not the
   absence of an allow. `make-illegal-states-unrepresentable` (§4): a grant's effect is a sum type
   `Allow | Deny`, and the resolver's precedence (deny > allow > default-deny) has one owner. A stage-1
   design that answered by `any(role grants (A,R))` must **reopen** the decision core.

2. **Inheritance threaded through call sites.** Walking the resource hierarchy at each caller, or expanding
   grants eagerly, scatters the resolution rule. The correct shape resolves the **effective grants for
   (U, A, R, now)** in one place: collect grants along the resource path, apply specificity, apply
   deny-overrides, apply the time window — one resolver, one precedence order. (§5 one-owner-per-rule,
   §7 OCP: a new effect or a new precedence rule extends the resolver, not every call site.)

3. **Time check scattered / precedence undefined.** Expiry filtered in one place while deny is applied in
   another lets an expired deny leak, or an allow inside its window lose to an out-of-window deny. Precedence
   across all three (specificity, deny>allow, validity) must be a single defined order. (§1 interaction
   coverage: deny × inheritance × time.)

## Oracle answers (canonical)

- "Is deny at the same resource level as an allow, or does specificity apply first?" → "Resolve specificity
  first (most specific resource wins); at the same level, deny beats allow."
- "Default when nothing matches?" → "Deny."
- "Can a group grant and a resource grant both apply?" → "Yes; the more specific resource-level grant wins;
  a deny on the path still wins over an allow."
- "Is 'now' supplied or read from the clock?" → "Supplied to the decision."
- "Are roles themselves time-bounded?" → "Only grants carry windows; keep role assignment simple."

## Survival oracle (D2)

**Extends** if stage 1 already put the decision behind a resolver over a grant abstraction (a grant with an
effect and a target), so deny becomes a second effect, inheritance becomes how targets are matched, and the
window becomes a predicate on a grant — all inside the one resolver. **Reopens** if the decision was
`any(...)` over a flat permission set with no grant/effect type and no single decision owner, so all three
features force the core open and precedence has nowhere to live.
