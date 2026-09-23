---
title: "Stage 2: deny, resource hierarchy, time-bounded grants (genericity worker)"
date: 2026-09-23
axis: genericity. Every seam is sized from both ends: complete for its consumer, and no more specific than every producer can supply
status: design proposal for the Guide's merge
builds on: DESIGN.md (stage 1), decisions/0002-stage1-decision-architecture.md
---

# Stage 2: explicit deny, resource inheritance, validity windows

## 0. The design in one paragraph

Three new facts feed the decision: a grant's **effect**, the resource's **lineage** (itself plus its ancestors),
and the question's **instant**. Each fact has one owner, and each owner turns its fact into a filter that
runs *before* the combining rule. So the combining rule gets the smallest complete input it can have: the
**set of effects** of the grants that apply, `frozenset[Effect]`. The rule does not see roles, levels, or
times, because B1 says none of them affects precedence. Its one owner is `EntitlementModel.decide`, which
applies: *DENY if DENY ∈ effects; else ALLOW if ALLOW ∈ effects; else DENY.* The lineage is a **set**, not
a path, because matching needs membership only. A set also means "most specific wins" cannot be written
without reopening the hierarchy's owner. Deny is an `Effect` value on a grant. It is not a missing allow and
it has no separate grant channel. The hierarchy is a `child → parent` mapping, so the input cannot express
two parents. The model owns the hierarchy, together with the grants, so one immutable object still holds
everything a decision reads. `now` crosses the seam as a required, timezone-aware `datetime`. The core
normalizes it to UTC once, in the same way it normalizes identifiers.

## 1. Module skeleton

```
entitlements/                 Python 3.11+, stdlib only
├── __init__.py    public core re-exports (Decision, Effect, Grant, EntitlementModel, errors); no edges
├── model.py       CORE  errors, _identifier, Effect, Grant, Decision, _Grant, _Role, EntitlementModel
├── _time.py       CORE  _instant (the instant rule), _Window (the "in force at" clause)
├── _hierarchy.py  CORE  _Hierarchy (tree invariants, the "whose grants reach R" clause)
├── json_file.py   EDGE  load_model(path): owns the file format (gains effect, windows, parents)
├── cli.py         EDGE  main(argv): owns argv, the wall-clock default for --now, output, exit codes
└── __main__.py    EDGE  raise SystemExit(main())
```

Dependencies: `__main__ → cli → json_file → model → {_time, _hierarchy}`. `_time` and `_hierarchy` import
nothing from the package. They raise plain `ValueError`, and `model` translates it at its two boundaries,
as `_identifier` already does. The core now also imports `datetime`, which is a pure value library and not
I/O. It still never imports `json`, `argparse`, `os`, `sys`, `pathlib`, `io` or `threading`, and it never
calls `datetime.now()`. A fitness test enforces this.

**Why the split follows these two lines (superseding stage-1 §1 "one module", as that section foresaw).**
Stage 1 kept one module because every part changed for one reason. Stage 2 adds two change axes that vary
independently. Time policy covers what an instant is, how bounds compare, and how an unbounded window
behaves. Tree policy covers what a valid hierarchy is and which ancestors' grants reach a resource. A change
on either axis (for example recurring windows, or a DAG instead of a tree) reopens exactly one private
module and leaves the grant, role and combining rules alone. The grant, role and combining rules stay
together in `model.py`, because they change together whenever the decision rule changes. There is no split
into `errors.py`, `ids.py` or `grant.py`, because no axis separates them.

## 2. Public API: everything that crosses a seam

```python
# entitlements (re-exported from entitlements.model)
class Decision(enum.Enum):          # unchanged: the answer (A5)
    ALLOW = "allow"
    DENY = "deny"

class Effect(enum.Enum):            # NEW: what a grant states
    ALLOW = "allow"
    DENY = "deny"

@dataclass(frozen=True, slots=True)
class Grant:                        # NEW: a declaration, not a validated value (see §2.2)
    action: str
    resource: str
    _: KW_ONLY
    effect: Effect = Effect.ALLOW
    valid_from: datetime | None = None     # inclusive; None = open
    valid_to: datetime | None = None       # exclusive; None = open

class EntitlementModel:
    def __init__(
        self,
        *,
        roles: Mapping[str, Iterable[Grant | tuple[str, str]]],  # a 2-tuple is the stage-1 grant
        assignments: Mapping[str, Iterable[str]],
        parents: Mapping[str, str] = {},                          # resource -> its parent group
    ) -> None: ...                                                # raises InvalidModelError
    def decide(self, user: str, action: str, resource: str, *, now: datetime) -> Decision: ...
                                                                  # raises InvalidQuestionError

class EntitlementsError(Exception): ...
class InvalidModelError(EntitlementsError, ValueError): ...
class InvalidQuestionError(EntitlementsError, ValueError): ...

# entitlements.json_file
def load_model(path: str | os.PathLike[str]) -> EntitlementModel: ...

# entitlements.cli
def main(argv: Sequence[str] | None = None) -> int: ...     # 0 allow · 1 deny · 2 error (A8)
```

(The `{}` default is never mutated or aliased, because the constructor copies every input. It can be
written as `MappingProxyType({})` if a linter objects.)

Host use:

```python
model = EntitlementModel(
    roles={
        "finance-reader": [Grant("read", "finance")],
        "contractor":     [("read", "doc-43"),
                           Grant("read", "doc-42", effect=Effect.DENY,
                                 valid_to=datetime(2027, 1, 1, tzinfo=UTC))],
    },
    assignments={"alice": ["finance-reader", "contractor"]},
    parents={"doc-42": "finance", "doc-43": "finance", "finance": "org-root"},
)
model.decide("alice", "read", "doc-42", now=datetime.now(UTC))   # DENY until 2027, ALLOW after
```

### 2.1 Calibration of each seam (floor = what the consumer needs; ceiling = what every producer can supply)

| Seam | Floor | Ceiling | Chosen type | Rejected, and why |
|---|---|---|---|---|
| Question in | 3 ids + the instant the decision is relative to (B4) | host code holds `str`s and a `datetime`; argv holds strings, which the CLI turns into a `datetime` | `decide(user, action, resource, *, now: datetime)`, where `now` must be aware | `now: float` epoch: loses the offset check B3 requires. `now=None` → clock: B4 forbids the core reading the clock. A `Clock` port: speculative, because no producer needs to vary the clock and the shell already supplies it |
| Answer out | allow/deny (A5) | the rule yields one of two facts | `Decision`, unchanged | adding a reason or the deciding grant: A5, and no consumer |
| Grant declaration in | effect, action, resource, two optional bounds (A6: the grant as a whole value) | host constructs values; JSON has objects with optional keys | `Grant` (keyword-only optional fields) **or** the stage-1 `(action, resource)` tuple | Mapping-per-grant: stringly-keyed in code, and a typo in a key is caught only at runtime. Variable-arity tuple: positional connascence over five fields. `Grant.allow()`/`.deny()` factories without `Effect`: a producer holding the effect as *data* (a JSON field, a DB column) would have to branch to pick a factory |
| Effect in | exactly two values | JSON string; host constant | public `Effect` enum | reusing `Decision`: value-correct but concept-wrong. A grant's DENY is an explicit statement, while the answer DENY is often "no grant applied". A `deny: bool`: makes allow the negation of deny, and the flag reads backwards at call sites |
| Window in | two optional instants | host `datetime`s; JSON ISO strings | two optional fields on `Grant` | public `Window` type: it would have one consumer (the `Grant` constructor) and a name nobody needs |
| Hierarchy in | each resource's at most one parent (B2) | host dict; JSON object | `parents: Mapping[str, str]` (child → parent) | `groups: Mapping[str, Iterable[str]]` (group → members): two parents become representable and need a check. With child → parent, the tree's "≤1 parent" is the mapping's own key uniqueness |
| Hierarchy → grant match (internal) | "is this grant's resource among those whose grants reach R" | the tree can always produce R plus its ancestors | `frozenset[str]` (the **lineage**) | an ordered path `tuple[str, ...]`: more specific than the consumer needs, and it invites "most specific wins", which B1 says is wrong |
| Grants → combining rule (internal) | "is there an applicable deny? an applicable allow?" | every grant can report its effect | `frozenset[Effect]` | passing `(role, depth, effect, window)` records: role, depth and time are not inputs to the rule, so they do not cross |
| File → model | the CLI needs a model from a path | filesystem + JSON | `load_model(path)`, unchanged | — |

The last two rows are where this axis pays off. The combining rule's input type holds nothing the rule is
not allowed to use. Getting the precedence wrong (by level, by role, or by order) would require widening a
type, which means reopening its owner. It cannot slip in as a local edit.

### 2.2 `Grant`: a published declaration, parsed by the one parse owner

`Grant` is the constructor's input language, the counterpart of the stage-1 tuple. It is **not** validated
on construction. The model constructor parses every grant, whichever way it was spelled, through the same
phase-1 path that stage 1 used for tuples, so identifier, instant and window rules keep one entry point
each. The alternative was a self-validating `Grant.__post_init__`, which would have made two parse sites:
tuples in the model, `Grant`s in `Grant`. It was rejected. `Grant` never crosses the seam *outward*: the
model does not return it or store it (it stores `_Grant`), so its public shape is not a representation leak.

**Why keep the 2-tuple.** Present force: stage-1 host code and tests declare grants as `(action, resource)`.
Add-feature §4 requires those calls to keep behaving exactly as before. The tuple is the stage-1 grant: an
allow with no window. Both spellings reach one internal `_Grant`, so this adds an input spelling and no
second rule.

**Why `effect` defaults to `ALLOW`.** An unmarked grant has meant "allow" since stage 1, and stage-1 JSON
files have no `effect` key. The default keeps both valid. Deny is still first-class, because it is a value
of the same field and not the absence of anything.

### 2.3 The one deliberate break at the question seam

`decide` gains a **required** keyword `now` (B4). A stage-1 call `decide(u, a, r)` now raises Python's
`TypeError` for a missing argument. That is a signature error, which Python reports itself, and it is
distinct from a malformed *value*, which is always `InvalidQuestionError`. B4 forbids the only alternative
that avoids the break, which is defaulting to the clock inside the library. The *answer* for any stage-1
model is unchanged at every `now` (§6.5). This is flagged to the Guide as a risk (§11).

## 3. The internal model

```python
# _time.py
def _instant(value: object, what: str) -> datetime:
    """Accept an aware datetime; return an exact datetime in UTC. Otherwise raise ValueError naming `what`."""
@dataclass(frozen=True, slots=True)
class _Window:
    start: datetime | None        # UTC, inclusive
    end: datetime | None          # UTC, exclusive; invariant: start < end when both present
    @staticmethod
    def between(start: datetime | None, end: datetime | None) -> "_Window": ...  # raises ValueError if start >= end
    def contains(self, now: datetime) -> bool:
        # (start is None or start <= now) and (end is None or now < end)

# _hierarchy.py
class _Hierarchy:                  # __slots__ = ("_lineage_of",); MappingProxyType[str, frozenset[str]]
    def __init__(self, parents: Mapping[str, str]) -> None: ...   # raises ValueError listing every cycle
    def lineage(self, resource: str) -> frozenset[str]:            # resource ∪ its ancestors; unlisted → {resource}

# model.py
@dataclass(frozen=True, slots=True)
class _Grant:
    effect: Effect
    action: str
    resource: str
    window: _Window
    def applies(self, action: str, lineage: frozenset[str], now: datetime) -> bool:
        # self.action == action and self.resource in lineage and self.window.contains(now)

@dataclass(frozen=True, slots=True)
class _Role:
    grants: frozenset[_Grant]
    def effects(self, action: str, lineage: frozenset[str], now: datetime) -> frozenset[Effect]:
        # frozenset(g.effect for g in self.grants if g.applies(action, lineage, now))

class EntitlementModel:            # __slots__ = ("_roles_of", "_hierarchy")
    _roles_of: Mapping[str, frozenset[_Role]]
    _hierarchy: _Hierarchy
```

### 3.1 `_instant`: the instant rule (B3, B4), a sibling of `_identifier`

- Accepts any `datetime` instance whose `utcoffset()` is not `None`, which is Python's own definition of
  aware. It rejects a naive `datetime`, a `date`, a `str`, a number and `None`.
- Normalizes to an **exact `datetime` in UTC**, built by `datetime`'s own constructor from the
  offset-adjusted fields. Every comparison and hash in the package is therefore exact UTC against exact UTC.
  Two consequences hold by construction: "the same instant in different offsets behaves identically", and
  A6 set semantics treat `[t+02:00, …)` and `[t−00:00, …)` as one window. The reason matches stage 1's
  reason for normalizing `str`: a `datetime` subclass cannot change comparison.
- A value that overflows when converted to UTC (for example `datetime.min` with a positive offset) is
  rejected with a message that names the field. It never surfaces as an `OverflowError`.
- Raises plain `ValueError`. `model` translates it to `InvalidModelError` (in a grant) or
  `InvalidQuestionError` (for `now`).

### 3.2 `_Window`: the "in force at this instant" clause

The only owner of half-open containment and of the `start < end` invariant. `between(None, None)` is the
**always** window. It is not a stand-in. It is the window with both bounds absent, which B3 already allows,
and "no window" means exactly that. So `_Grant.window` is never `None`, and no code branches on "has a
window?". A window is a value: equal bounds mean equal windows.

### 3.3 `_Hierarchy`: the tree and "whose grants reach R"

- **Invariants, all established in `__init__`.** Each resource has at most one parent, which the input type
  guarantees, since a mapping key cannot repeat, and which the parse enforces for normalized-key
  collisions. There is no cycle, and a self-parent counts as a cycle of length 1. The constructor walks up
  from every child. It collects **every** distinct cycle, as a rotated canonical tuple so that each cycle is
  reported once, and raises one `ValueError` that lists them all. Otherwise it stores
  `lineage_of[child] = {child} ∪ lineage_of[parent]`, memoized during the same walk.
- **`lineage(r)`** returns the stored set, or `frozenset({r})` for a resource the hierarchy does not list.
  That covers B2's "unlisted resource is its own root" rule, and it covers a group that appears only as a
  parent, such as `org-root`.
- **Inheritance flows down only**, and this holds structurally: a lineage contains only the resource and its
  ancestors, never its descendants.
- A parent group needs no other declaration. Resources are opaque, and an unknown resource is valid (A2).
  So nothing like A3's "undefined role" check applies here.
- Precomputing lineages does not blur an owner, unlike precomputing user permissions, which stage 1
  rejected. The walk is required anyway to detect cycles, and its result never leaves `_Hierarchy`.

### 3.4 `_Grant`, `_Role`, and what replaced `_Permission`

`_Grant` is a grant as a whole value (A6: effect, action, resource, window). `_Grant.applies` owns **the
grant-scope clause**: the action matches exactly, the grant's resource is in the question's lineage, and
the window contains `now`. It composes the other two clause owners and does not restate them.

`_Permission` is **removed** (superseding stage-1 §3.2). Its only rule was that "two permissions are equal
iff action and resource are equal", and that rule was the matching rule. With inheritance, matching is
"action equal **and** resource ∈ lineage". It is no longer equality between two pairs, so `_Permission`
would survive only as an inert pair of fields inside `_Grant`. The exact-string comparison it guaranteed
still holds, because every field of `_Grant` is a normalized exact `str`.

`_Role` keeps its stage-1 place (concept fit: the rule is still phrased as "from any of U's roles"). Its
clause is now: **the effects a role contributes are exactly those of its own declared grants that apply.**
It returns effects, not grants, because effects are all its consumer needs (§2.1 floor). `decide` never
reads `grants` (Tell-Don't-Ask).

### 3.5 `EntitlementModel`: construction (two phases, as in stage 1)

*Phase 1: parse (stop at the first error; `InvalidModelError` gives the location).*

1. `roles`, `assignments` and `parents` must each be a `Mapping`.
2. `roles`: keys go through `_identifier(…, "role")`. Each value must be a non-`str` iterable. Each grant is
   either a `Grant` instance or a 2-item non-`str` sequence, which becomes
   `Grant(action, resource)`. Anything else, including a bare string, is rejected. For each grant:
   `_identifier` on action and resource, `isinstance(effect, Effect)`, `_instant` on each bound that is
   present, then `_Window.between`. A window with start ≥ end is rejected here, because it is a fault
   local to one grant. The results collect into `frozenset[_Grant]` (A6), which becomes `_Role`.
3. `assignments`: unchanged from stage 1.
4. `parents`: keys go through `_identifier(…, "resource")` and values through
   `_identifier(…, "parent group")`.
5. In any of the three mappings, two keys that normalize to the same string are rejected (A7 in code). For
   `parents` this is also the "two parents" rule, since two parents can only arrive as two keys.

*Phase 2: consistency (every violation is reported in one `InvalidModelError`).*

6. Resolve assignments against roles and collect every `(user, undefined role)` pair.
7. Build `_Hierarchy(parents)` and collect its cycle list if it raises.
8. If either list is non-empty, raise one `InvalidModelError` that lists both, for example
   `undefined roles: alice → Editor; hierarchy cycles: a → b → a, c → c`. Otherwise freeze.

The stage-1 reporting rule still holds: malformed input reports the first problem, and well-formed but
inconsistent input reports every problem. Grants, assignments and hierarchy are stored in one immutable
object. That is why a torn read between the hierarchy and the grants cannot happen (§7).

### 3.6 `decide(user, action, resource, *, now)`: the one owner of the combining rule

1. **Parse the whole question first**: `_identifier` on user, action and resource, then `_instant` on
   `now`, and report the first bad part as `InvalidQuestionError` naming it. A malformed `now` for an
   unknown user raises. It does not return DENY.
2. **Gather**: `lineage = self._hierarchy.lineage(resource)`;
   `effects = ⋃ role.effects(action, lineage, now) for role in self._roles_of.get(user, ∅)`.
3. **Combine: the deny-overrides rule, entirely here:**
   `DENY if Effect.DENY in effects else (ALLOW if Effect.ALLOW in effects else DENY)`.

Step 3 is the only place in the package where `Effect` meets `Decision`. Step 2 is the only place where a
user's roles are combined, and the union makes "a deny from role Y overrides an allow from role X" work
with no cross-role code. Step 3 has no branch for levels or time, because by then both have already been
reduced to set membership.

## 4. Where each rule lives

| Rule | Sole owner | Reached via |
|---|---|---|
| **Combining: deny overrides allow; with neither, deny** (B1, rule 1) | `decide` step 3 | host → `decide`; CLI → `load_model` → `decide` |
| A user's grants are those of all their roles, and a deny from any role counts (rule 1) | `decide` step 2 (union over `_roles_of[u]`) | only `decide` |
| A role contributes exactly its declared grants that apply | `_Role.effects` | only `decide` |
| **Grant scope**: a grant applies iff action equal ∧ its resource ∈ lineage(R) ∧ in force at now | `_Grant.applies` | only `_Role.effects` |
| **Coverage by inheritance**: grants on R and on every ancestor of R reach R; never a descendant's (rule 2, B2) | `_Hierarchy.lineage` | only `decide` step 2 |
| An unlisted resource is its own root (B2) | `_Hierarchy.lineage` fallback | — |
| Tree invariants: ≤1 parent, acyclic, self-parent rejected (B2) | `parents` type (child → parent) + `_Hierarchy.__init__` | constructor phase 1 step 5, phase 2 step 7 |
| **In force**: `from ≤ now < to`, open bounds, no window = always (rule 3, B3, B5) | `_Window.contains` | only `_Grant.applies` |
| A window needs `from < to` (B3) | `_Window.between` | constructor phase 1 |
| Instant: aware only, compared by instant, UTC-normalized (B3) | `_instant` | constructor (bounds) and `decide` (`now`), the only two places datetimes enter |
| `now` is supplied, never read from the clock (B4) | the `decide` signature (required); the wall-clock default lives only in `cli` | — |
| Identifier: non-empty `str`, exact characters (A4) | `_identifier` | unchanged |
| Grants as whole values; duplicates idempotent (A6) | `_Grant` value equality + `frozenset` | constructor |
| Undefined role rejected (A3) | constructor phase 2 | — |
| Parse: first error; consistency: all errors | constructor | `json_file` shape checks follow the parse half |
| Model immutable, whole-swap replacement, no torn read (A1) | `EntitlementModel` holding roles + hierarchy | host rebinds |
| File syntax, shape, optional keys, ISO datetime syntax, duplicate keys (A7) | `json_file` | — |
| argv, `--now` default and parsing, output, exit codes (A8) | `cli` | — |

## 5. JSON file format (owned by `json_file`)

```json
{
  "roles": {
    "finance-reader": [ {"action": "read", "resource": "finance"} ],
    "contractor": [
      {"action": "read", "resource": "doc-43"},
      {"action": "read", "resource": "doc-42", "effect": "deny",
       "valid_from": "2026-10-01T00:00:00Z", "valid_to": "2027-01-01T00:00:00+02:00"}
    ]
  },
  "assignments": { "alice": ["finance-reader", "contractor"] },
  "parents": { "doc-42": "finance", "doc-43": "finance", "finance": "org-root" }
}
```

Changes, all additive, so every stage-1 file loads and answers as before:

- **Top level**: exactly `roles` and `assignments`, plus an optional `parents`. Any other key is still
  rejected. `parents` must be an object. Its leaf values are checked by the core.
- **Grant object**: `action` and `resource` are required. `effect`, `valid_from` and `valid_to` are
  optional. Any other key is rejected. A missing `effect` means allow.
- **`effect`** must be the string `"allow"` or `"deny"`. The edge converts it with `Effect(value)`, and any
  other value gets an `InvalidModelError` that names the grant. The spelling of the file's vocabulary
  belongs to the file owner.
- **Bounds** must be strings parsed by `datetime.fromisoformat` (3.11 accepts `Z`). An absent key means an
  open bound. `null` is rejected as a shape error (A12). The edge owns only the *syntax*. A string that
  parses to a **naive** datetime reaches the core, which rejects it (`_instant`). So the core and the loader
  cannot disagree about what a valid instant is, which is the same split stage 1 made for identifiers.
- **Two parents** in the file can only be written as a repeated key in `parents`, which the existing A7
  duplicate-key hook already rejects. No new check is needed.
- The edge builds `Grant(...)` values and calls the constructor, so it uses the same seam as host code.

## 6. CLI changes (owned by `cli`)

`python -m entitlements --model PATH [--now ISO-8601] USER ACTION RESOURCE`

- `--now` is optional. Its argparse `type=` converter calls `datetime.fromisoformat`. A syntax error is a
  usage error: argparse exits 2, as stage 1 already did for bad argv.
- When `--now` is absent, the shell supplies `datetime.now(timezone.utc)`. This is the **only** clock read
  in the package, and it sits in the imperative shell (B4).
- A naive `--now` is not given a local time zone. It is passed through, and the core raises
  `InvalidQuestionError` (B3 applies to the question), which prints on stderr and exits 2.
- Output text and exit codes are unchanged (A8).

## 7. Adversarial cases traced through the design

Notation: L(R) = `_Hierarchy.lineage(R)`, E = the effects gathered in step 2.

**Deny**

| Case | Trace | Result |
|---|---|---|
| role X allows (A,R), role Y denies (A,R) | E = {ALLOW} ∪ {DENY}; step 3 finds DENY | DENY |
| same role allows and denies (A,R) | two distinct `_Grant`s (they differ in effect); E = {ALLOW, DENY} | DENY |
| deny (write,R), allow (read,R); ask (read,R) | the deny grant fails `action ==`; E = {ALLOW} | ALLOW |
| deny (A,R1), allow (A,R2); ask (A,R2) | R1 ∉ L(R2) = {R2}; E = {ALLOW} | ALLOW |
| user holds only deny grants; ask a denied (A,R) / any other | E = {DENY} / ∅ | DENY / DENY |

**Hierarchy** (parents: doc-42→finance, doc-43→finance, finance→org-root)

| Case | Trace | Result |
|---|---|---|
| allow (A, org-root); ask (A, doc-42) | L(doc-42) = {doc-42, finance, org-root} ∋ org-root | ALLOW |
| allow finance + deny doc-42; ask doc-42 / doc-43 | E = {ALLOW, DENY} / L(doc-43) ∌ doc-42 → E = {ALLOW} | DENY / ALLOW |
| deny org-root + allow doc-42; ask doc-42 | E = {DENY, ALLOW}. Level is not in the combining rule's input, so "most specific" cannot win | DENY |
| deny doc-42; ask (A, finance) | L(finance) = {finance, org-root} ∌ doc-42 | unaffected |
| unlisted doc-99; grant on finance | L(doc-99) = {doc-99}; only exact grants | DENY (unless it has an exact grant) |
| ask about group `finance` directly | L(finance) as above | normal decision |
| `{a: b, b: a}` / `{a: a}` | phase 2 step 7: cycle list `a → b → a` / `a → a` | InvalidModelError |
| two parents | JSON: repeated key, A7 rejects. Code: a `Mapping` cannot hold it; distinct subclass keys that normalize to the same string are rejected by phase 1 step 5 | InvalidModelError |

**Time** (t0 < t1, window [t0, t1))

| Case | Trace | Result |
|---|---|---|
| now = t0 / t1 / < t0 | `start ≤ now` true, `now < end` true / `now < end` false / `start ≤ now` false | in force / not / not |
| open bounds | the absent side of the conjunction is skipped | in force on that side forever |
| from ≥ to | `_Window.between` raises in phase 1 | InvalidModelError |
| naive bound / naive `now` | `_instant` → model / question error | InvalidModelError / InvalidQuestionError |
| same instant, +02:00 vs Z | both normalize to the same UTC value; identical comparisons and equal `_Grant`s | identical |
| expired deny + permanent allow | deny's `contains` false → E = {ALLOW} | ALLOW |
| not-yet-valid allow only | E = ∅ | DENY |

**Interactions**

| Case | Trace | Result |
|---|---|---|
| deny (A, finance) in [t0,t1) + permanent allow (A, doc-42); now in window / outside | E = {DENY, ALLOW} / {ALLOW} | DENY / ALLOW |
| same (effect,A,R) with windows W1 and W2 | two `_Grant`s (the windows differ); applies whenever now ∈ W1 ∪ W2 | in each window |
| exact duplicate grants (including the same instant in another offset) | one `frozenset` element | idempotent |
| malformed `now` + unknown user | step 1 before lookup | InvalidQuestionError |
| deny (write, org-root); ask (read, doc-42) with allow (read, finance) | the deny fails on action | ALLOW |
| `Finance` vs `finance` in `parents` | exact ids, so distinct groups | no inheritance across them |

**Stage-1 preservation (the proof, not a sample).** Take a model with only tuple or plain `Grant` grants
(all ALLOW, always-window) and no `parents`. For every R, L(R) = {R}. For every aware now, `contains(now)`
is true. So `_Grant.applies(a, {R}, now)` ⇔ `action == a ∧ resource == R`, which is exactly stage 1's
`_Permission` equality. E ⊆ {ALLOW}, so step 3 gives ALLOW ⇔ E ≠ ∅ ⇔ some role holds `(a, R)`, which is
stage 1's `any(role.grants(p))`. Every row of stage-1 §3.4 and every stage-1 §8 case therefore answers the
same, at any `now`. The test suite pins this with the stage-1 cases unchanged except for the added `now`.

**Replacement and torn reads.** Grants and hierarchy are fields of one immutable `EntitlementModel`, and a
query reads only `self`. Replacing the hierarchy means supplying a whole new model (A1), so a query cannot
combine one model's hierarchy with another's grants. Stage-1 §6 is otherwise unchanged.

## 8. Test plan (test-first; behavior through `EntitlementModel`, `load_model`, `main` only; stdlib `unittest`)

Every case in §7 is a named test. In addition:

- **Stage-1 characterization, written first and kept green unchanged except for `now`**: every stage-1 §8
  grant-rule, exactness, malformed-question, subclass, construction, file and CLI test, run at three
  `now` values (past, present, far future, with mixed offsets). Tuple-declared and `Grant`-declared
  stage-1 models give identical answers over a question grid.
- **Combining rule**: the full 2×2 table of (an applicable allow present?, an applicable deny present?) →
  (DENY, ALLOW, DENY, DENY). Order-independence: roles and grants declared in reversed order give the
  same answers.
- **Hierarchy**: depth 1, 2 and 3 inheritance. Deny at every level of a depth-3 path × allow at every
  level → DENY for all 9 pairs (this pins "no most-specific-wins" in general, not just one case).
  Downward-only: a grant on a leaf never reaches its parent or a sibling. Unlisted resource. Group
  askable. A parent-only group (never a key). Cycles of length 1, 2 and 3 reported together in one error.
  A cycle *and* an undefined role in one error. A malformed parent id beats a cycle (parse before
  consistency). Normalized-key collision in `parents`. A non-mapping `parents`. Omitting `parents` equals
  passing `{}`.
- **Time**: boundaries at t0−1µs, t0, t1−1µs and t1. Open-start and open-end. Both open. from == to and
  from > to rejected. Naive bounds, a `date`, a string or a number as a bound → InvalidModelError naming
  the role and the grant number. Naive `now`, a `date`, a string, `None` → InvalidQuestionError. A
  `datetime` subclass as `now` behaves like its plain value. A bound that overflows on conversion to UTC is
  rejected cleanly. Same instant in `+05:30`, `Z` and `zoneinfo("America/New_York")` → identical answers.
  Two grants differing only in the offset of equal instants are one grant, which you can see because the
  set-semantics grid answers the same as with one declared.
- **Effect/Grant seam**: `effect="deny"` (a string, not `Effect`) → InvalidModelError. A bare string or a
  3-tuple as a grant → InvalidModelError. A `Grant` with an empty action → InvalidModelError at model
  build, not at `Grant(...)`. `Decision` and `Effect` each have exactly two members.
- **Immutability/surface**: `EntitlementModel` still exposes exactly `{decide}`. `__all__` equals the §2
  core set. Mutating the caller's `parents` or grant lists after construction changes nothing.
- **Replacement**: a threaded rebinding stress test between two models whose hierarchies differ, chosen so
  that a mix of model A's hierarchy with model B's grants would give an answer neither model gives
  (a regression guard, since the guarantee itself is structural).
- **File edge**: the §5 example answers every §7 case. Every stage-1 fixture file loads unchanged.
  Rejected, each with the path: unknown top-level key, unknown grant key, `effect: "Deny"`, `effect: 1`,
  a non-string bound, a non-ISO bound, `null` bound, repeated key in `parents`, `parents` not an object. A
  naive ISO bound → the core's error with the path note. The same model built in code and from file gives
  identical decisions at several `now` values.
- **CLI**: `--now` given → a deterministic answer on each side of a window. `--now` naive → stderr, exit 2.
  `--now` unparseable → usage, exit 2. `--now` absent → runs against the wall clock (asserted with a model
  whose answer does not depend on time, plus one whose window is open-ended in the past). Exit codes and
  output text unchanged.
- **Architecture fitness**: `ast` scan of `model.py`, `_time.py` and `_hierarchy.py`: none imports I/O
  modules. No core module references `datetime.now`, `time.time` or `date.today`. `_time` and `_hierarchy`
  import nothing from the package. `import entitlements` does not load `json`.

## 9. Assumptions added (A10–A14; A1–A9 unchanged, B1–B5 from the package)

- **A10: a grant declared without an effect is an allow**, both in code and in the file. This keeps every
  stage-1 declaration valid and meaning what it meant.
- **A11: a parent group needs no declaration of its own.** Any resource id may be a parent. Resources are
  opaque, and unknown ones are valid (A2).
- **A12: an open bound is written by omitting the key.** A `null` bound in the file is a shape error.
  There is one spelling per meaning, consistent with the stage-1 exact-keys stance. This is easy to relax
  in `json_file` alone if hand-editors ask for it.
- **A13: file datetimes are ISO 8601 strings** as accepted by `datetime.fromisoformat` in Python 3.11
  (including `Z`). The CLI's `--now` uses the same syntax.
- **A14: `now` at the library seam is keyword-only and required.** This breaks stage-1 *call sites* (not
  answers), as B4 dictates (§2.3).

## 10. Deliberately not built

- A `Clock` or time-source port. B4 puts the clock in the shell, and no producer varies it.
- A public `Window`, `Lineage` or `Question` type. Each would have one consumer and no rule of its own at
  the seam.
- A separate `denies=` argument or deny table. That would give two grant channels, with the window and
  hierarchy rules applied twice, which is two owners.
- An ordered ancestor path, depth-weighted precedence, or "most specific wins". B1 says they are wrong
  here, and the set-typed lineage keeps them out.
- Group membership lists (group → members), multiple parents or DAGs. B2 says the hierarchy is a tree.
- Time-bounded roles or assignments (B5). Windows on the hierarchy itself. Recurring windows.
- Declaring groups separately. Checking that granted resources exist.
- Explanations or "which grant decided" (A5). Precomputed per-user effective permissions. Caching. A
  holder or reload service. Wildcards. Action hierarchy. Role inheritance. Conditions.
- Accepting `"allow"`/`"deny"` strings as `effect` in code. There is one spelling, the enum. The file's
  strings are converted by the file owner.

## 11. Key decisions and rejected alternatives

1. **Precedence lives in `decide`, over `frozenset[Effect]`.** The three dimensions are each reduced
   upstream by their own owner: roles by union, levels by lineage membership, and time by window
   containment. So the combining rule's input is the smallest complete type. *Rejected:* a resolver object
   or strategy. It would have one implementation and no known axis to vary, so it would be speculative. A
   precedence method on `Effect`: that makes the grant vocabulary own the answer vocabulary. Per-role
   decisions combined afterwards: "deny from Y overrides allow from X" would then need a second, cross-role
   combine, which is two owners.
2. **Deny is an `Effect` value on the grant** (concept fit: an explicit deny is not a missing allow).
   *Rejected:* reusing `Decision` (concept-wrong), `deny: bool`, a separate deny table (two owners), and
   negative permissions.
3. **The hierarchy is `child → parent`, owned by `_Hierarchy` and held inside the model.** *Rejected:*
   group → members (two parents become representable). A hierarchy object supplied separately from the
   model (torn reads become possible, and A1's whole-swap would cover only half the state). Walking on
   every query (it would also need the cycle guard at query time).
4. **Lineage is a set.** *Rejected:* an ordered path. It is more specific than any consumer needs, and it
   is exactly the shape that invites the wrong rule.
5. **`now` is a required, aware `datetime`, normalized once by `_instant`.** *Rejected:* an optional `now`
   that falls back to the clock (B4). An epoch float (it cannot enforce "aware"). Keeping the caller's
   offset (then comparison would stay correct, but set semantics and subclass safety would depend on the
   caller's objects).
6. **`Grant` is a published declaration; the tuple is kept as the stage-1 spelling.** *Rejected:* a
   Mapping per grant, variable-arity tuples, a self-validating `Grant` (a second parse site), and dropping
   the tuple (it breaks stage-1 hosts for no gain).
7. **Superseded from stage 1 (DESIGN.md, decision 0002):** §1 "the core is one module" → split along the
   two new axes. §3.2 `_Permission` → removed; `_Grant` + lineage now own matching. §3.3
   `_Role.grants(p)` → `_Role.effects(action, lineage, now)`. §3.4 "Deny is the absence of any grant; there
   is no deny machinery" → an explicit deny is a first-class effect, and absence is still the default deny.
   `decide` gains `now`. §10's "explicit deny rules, hierarchies" → built. Everything else in stage 1
   stands.

## 12. Subtractive pass: each addition and the present force behind it

| Added | Present force | Verdict |
|---|---|---|
| `Effect` (public) | the host must state the effect *as data* (the JSON field); concept distinct from `Decision` | keep |
| `Grant` (public) | 5 named facts with 3 optional ones; the tuple cannot carry them | keep |
| 2-tuple still accepted | stage-1 host code (add-feature §4) | keep |
| `parents` argument | rule 2 needs the tree; the type makes two parents unrepresentable | keep |
| `now` keyword | B4 | keep |
| `_instant` | one entry rule for all datetimes (the model and the question), UTC normalization for A6 and subclass safety | keep |
| `_Window` | the owner of the in-force clause and the `start < end` invariant; removes the "no window" branch | keep |
| `_Hierarchy` | the owner of the tree invariants and of lineage, including the unlisted fallback, which would otherwise sit in `decide` | keep |
| `_Grant` | A6: a grant is a whole value; the owner of the scope clause | keep |
| `_Role` (kept) | concept fit with a rule phrased over roles; the stage-1 recorded decision | keep |
| `_Permission` | none left (matching is no longer pair equality) | **removed** |
| `_time.py`, `_hierarchy.py` modules | two independent change axes (time policy, tree policy) | keep; *thin, flagged for the Guide*: folding both back into `model.py` changes no owner |
| `_Query(action, lineage, now)` value | considered for the three parameters passed decide → role → grant. They are distinct types, the chain has two hops, and nothing else consumes them together | **not added** |
| a separate `_combine()` function | the rule is one expression, and `decide` is its named owner | **not added** |
| a `Window` or `Lineage` public type, a `Clock` port | no consumer and no varying producer | **not added** |
