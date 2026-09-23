---
title: "Stage 2 — explicit deny, resource inheritance, time-bounded grants (encapsulation axis)"
date: 2026-09-23
axis: encapsulation — one enforced, unforgeable owner per rule; no seam leaks
builds on: DESIGN.md (stage 1), decisions/0002-stage1-decision-architecture.md
kind: add-feature / adaptation (behavior changes; stage-1 answers preserved where the features are absent)
---

# Stage 2 — design (encapsulation axis)

## 0. Summary

Stage 1 made `EntitlementModel.decide` the owner of the grant rule and said a deny/hierarchy stage would reopen
it and the role clause. This design reopens exactly those, and it keeps the public surface the same size.
**No new public type is added.** The three new concepts are an explicit **effect**, a validity **window** and
the resource **hierarchy**. All three are private values inside the one core module. The seam still speaks
only stdlib types: `str`, `tuple`, `Mapping`, `Iterable` and now `datetime`.

The central move is to split the decision into **clauses that can only produce effects** and **one function
that alone turns effects into a `Decision`**:

```
decide(u, a, r, now=t)
  └─ parse question ──► _Question(action, governing = hierarchy.governing(r), instant)
  └─ for each of U's roles: role.effects_for(q) ─► {grant.effect | grant.applies_to(q)}   (sets of _Effect)
  └─ _combine(union of those sets) ──► Decision          ← the ONLY producer of a Decision
```

- **`_combine`** owns the combining rule (deny overrides allow; no applicable grant → deny). It is a total
  function over four possible inputs: ∅, {ALLOW}, {DENY}, {ALLOW, DENY}.
- **`_Grant.applies_to`** owns "does this grant bear on this question". It is a conjunction of three clauses,
  each owned by one place. The action must match exactly (the grant). The grant's resource must be one of the
  resources governing R (`_Hierarchy.governing`). The grant must be in force at the instant (`_Window.contains`).
- **Clauses cannot decide.** `_Role`, `_Grant`, `_Window` and `_Hierarchy` never see `Decision`. They return
  `bool` or sets of `_Effect`. So no clause can short-circuit to an answer or order the precedence itself. That
  holds by construction, and an architecture fitness test pins it.
- **An explicit deny is not a missing allow.** `_Effect.DENY` is a value on a grant. `Decision.DENY` is an
  answer, and it may come from an explicit deny *or* from the absence of any applicable grant. The two types
  are kept apart on purpose (§9, decision 2).

## 1. Module skeleton

```
entitlements/                 Python 3.11+, stdlib only (unchanged)
├── __init__.py   public core re-exports (unchanged set); does NOT import the edges
├── model.py      CORE  errors, _identifier, _instant, _Effect, _Window, _Hierarchy, _Grant, _Role,
│                       _Question, _combine, Decision, EntitlementModel
├── json_file.py  EDGE  load_model(path) — owns the file format (grows: effect/from/to, parents, ISO text)
├── cli.py        EDGE  main(argv) — owns argv, the wall clock, output text, exit codes (grows: --now)
└── __main__.py   EDGE  unchanged
tests/            stdlib unittest
```

Dependencies are unchanged and acyclic: `__main__ → cli → json_file → model`, `cli → model`.
The core's import allow-list grows by exactly one module, **`datetime`**, which is needed for `datetime` and
`timezone.utc`. The core never imports `time`, and never calls `datetime.now`, `today`, `utcnow` or
`time.*` (B4). A fitness test enforces this.

**Why the core stays one module (kept from stage 1, re-examined).** Every new private type changes for the
same reason: the entitlement rules. The encapsulation axis gives a second reason. With one module, every new
concept is a `_private` name that no other module can import. A split into `_time.py` and `_hierarchy.py`
would make `model.py` reference classes that live in another module (§0 of the principles). The private
types would also become importable internal API. Falsifier: when windows gain a rule family of their own
(recurrence, calendars) or the hierarchy gains one (multiple parents, typed groups), that concept moves to its
own module behind a published protocol.

## 2. Public API — everything that crosses a seam

```python
# entitlements (re-exported from entitlements.model) — __all__ unchanged
class Decision(enum.Enum):          # unchanged
    ALLOW = "allow"
    DENY = "deny"

class EntitlementModel:
    def __init__(
        self,
        *,
        roles: Mapping[str, Iterable[tuple[str, str] | Mapping[str, object]]],
                                        # role -> its grants; a pair is the stage-1 form (see §2.1)
        assignments: Mapping[str, Iterable[str]],        # unchanged
        parents: Mapping[str, str] = {},                 # NEW, optional: resource -> its one parent group
    ) -> None: ...                                       # raises InvalidModelError
    def decide(self, user: str, action: str, resource: str, *, now: datetime) -> Decision: ...
                                                         # raises InvalidQuestionError

class EntitlementsError(Exception): ...                  # unchanged
class InvalidModelError(EntitlementsError, ValueError): ...
class InvalidQuestionError(EntitlementsError, ValueError): ...

# entitlements.json_file
def load_model(path: str | os.PathLike[str]) -> EntitlementModel: ...   # unchanged signature

# entitlements.cli
def main(argv: Sequence[str] | None = None) -> int: ...  # unchanged signature; new --now option
```

(The `{}` default is shown for brevity. The implementation uses an immutable empty mapping, e.g. a module
constant `MappingProxyType({})`, so no mutable default exists.)

### 2.1 Grant declarations at the seam

A grant is declared in one of two forms. Both are parsed by one function, `_parse_grant`, into one internal
value, `_Grant`.

| Form | Meaning |
|---|---|
| `(action, resource)`, a 2-item non-`str` sequence (**stage-1 form, unchanged**) | allow, no window, always in force |
| `{"action": a, "resource": r}`, optionally with `"effect": "allow"｜"deny"`, `"from": datetime`, `"to": datetime` | as written. Absent `effect` means allow. An absent bound is open. Any other key is rejected. |

- The pair *is* the mapping `{"action": a, "resource": r}`. There is one parse path, and the pair is one entry
  point into it, not a second rule.
- `effect` goes through `_identifier(…, "effect")` and then `_Effect(value)`. The enum's by-value lookup is the
  only owner of the effect vocabulary: exact and case-sensitive, like every identifier (A4), so `"Deny"` is
  rejected. A `StrEnum` member whose value is `"deny"` is accepted, because the identifier rule normalizes it.
- `from`/`to` must be `datetime` instances in code. The core does **not** parse text. Turning text into a
  datetime is a format concern that each edge owns (§4, §5).

### 2.2 Seam calibration (additions to stage-1 §2.1)

| Seam | Floor (consumer's need) | Ceiling (every producer can supply) | Type |
|---|---|---|---|
| "now" in | the in-force clause needs one instant | host code holds `datetime`; CLI has argv or the clock | `now: datetime`, keyword-only, **required**, must be aware |
| window bounds in | the in-force clause needs two optional instants | host `datetime`; JSON ISO text (converted at the edge) | `"from"`/`"to"`: aware `datetime`, key absent = open |
| effect in | grant needs allow or deny | host strings or `StrEnum`; JSON strings | `"effect": str`, optional, default allow |
| hierarchy in | "one parent per resource" | host dict; JSON object | `parents: Mapping[str, str]` (child → parent) |
| answer out | unchanged: A5 | — | `Decision` |

**Why `now` is a `datetime` and not a `Clock` port.** "Now" is part of the question (B4: supplied on every
question), not a dependency of the model. A clock object would put a way to read time *inside* the core. The
core could then call it twice in one decision (a torn instant), and every test would need a fake. As a plain
value, one instant is fixed at the seam and carried unchanged to the one clause that uses it.

**Why `now` is keyword-only.** In a positional fourth slot, a `datetime` sits next to three strings,
and a swapped argument would be a silent wrong answer. The keyword makes the call site read as the question:
`decide("alice", "read", "doc-42", now=t)`.

**Supersession (stated, not silent).** Stage 1's `decide(user, action, resource)` signature is replaced. A
three-argument call now raises `TypeError` (missing required keyword), which B4 requires. Every stage-1 *answer*
is preserved for any valid `now` (§7.6).

**Why no public `Grant`/`Window`/`Effect` type.** This follows the stage-1 reasoning. A published value type at
the model seam would need its own validation, which would create a second owner of the identifier, awareness
and window rules. Otherwise it would be a dumb bag that the constructor validates anyway. A mapping of stdlib
values is complete for every producer: host code, and JSON after ISO conversion. It keeps every rule inside
the one constructor.

## 3. The internal model — `entitlements/model.py`

Every internal type is a frozen, slotted dataclass or an enum. Each is built only inside this module, and
each owns one rule.

### 3.1 `_identifier(value, what) -> str` — unchanged (A4)

It now also validates `effect` strings and every resource named in `parents`.

### 3.2 `_instant(value, what) -> datetime` — NEW, the one owner of "a supplied instant"

This parallels `_identifier`. It is used at both entries of raw values: the constructor, for window bounds, and
`decide`, for `now`.

- **Accepts** `datetime` instances only. It rejects `date`, `str`, numbers and `None`, with a `ValueError`
  that names `what`.
- **Rejects naive values (B3):** `tzinfo is None` or `utcoffset() is None` → `"now must be timezone-aware, got
  2026-09-23T10:00:00"`.
- **Normalizes** to an exact `datetime` in UTC (`fold=0`), built from the fields of `value.astimezone(utc)`.
  The package stores and compares only that result, never the caller's object. Two reasons, both about
  correctness:
  1. *Comparison by instant is structural.* Python compares two aware datetimes **that share a tzinfo object**
     by wall time and ignores `fold` and offset. For a `zoneinfo` zone across a DST fold, that gives the wrong
     instant order. After normalization, every comparison is UTC against UTC, so `10:00+02:00` and `08:00Z`
     are the same value. This makes "same instant in different offsets behaves identically" true, and it
     makes the two windows `_Window` values that are equal (A6).
  2. *Subclass neutrality*, like `str.__str__` in stage 1. A `datetime` subclass cannot bring overridden
     comparison into the rule.
- `OverflowError` during normalization (for example `datetime.min` with a positive offset) is turned into
  `ValueError("… is out of range")`.
- It raises plain `ValueError`. Each boundary translates that once into `InvalidModelError` or
  `InvalidQuestionError`.

### 3.3 `_Effect` — NEW (concept fit: an explicit deny is a first-class value)

```python
class _Effect(enum.Enum):
    ALLOW = "allow"
    DENY = "deny"
```

This is a grant's effect. It is not `Decision` (§9, decision 2). Its by-value lookup owns the effect
vocabulary.

### 3.4 `_Window` — NEW, the owner of "is a grant in force at an instant"

```python
@dataclass(frozen=True, slots=True)
class _Window:
    start: datetime | None      # inclusive; None = open. Always a UTC-normalized _instant result
    end: datetime | None        # exclusive; None = open
    def __post_init__(self): ...                  # start >= end (both present) -> ValueError (B3)
    def contains(self, instant: datetime) -> bool:
        # (start is None or start <= instant) and (end is None or instant < end)

_ALWAYS = _Window(None, None)   # a grant declared with no window
```

- **Owns both halves of the window rule.** The invariant (`from < to`) lives in `__post_init__`, so no
  `_Window` that breaks it can exist, whatever private path builds it. The half-open membership lives in
  `contains`. "In force" is written nowhere else.
- **A grant with no window gets `_ALWAYS`, not `None`.** A window open at both ends is the real window
  (−∞, +∞), not a stand-in, so it fits the concept. It removes an `Optional` branch from `_Grant`: every grant
  has a window, and one expression covers stage-1 grants and windowed grants alike.
- B5 (windows apply to allow and deny alike) holds **by construction**. The window is a field of `_Grant`, and
  `_Grant.applies_to` has one path for both effects (§3.6).

### 3.5 `_Hierarchy` — NEW, the owner of the tree and of "which resources govern R"

```python
@dataclass(frozen=True, slots=True)
class _Hierarchy:
    _governing: Mapping[str, frozenset[str]]     # every resource named in `parents` -> itself + all ancestors
    @classmethod
    def of(cls, parents: Mapping[str, str]) -> "_Hierarchy": ...   # raises ValueError listing every cycle
    def governing(self, resource: str) -> frozenset[str]:
        # self._governing.get(resource, frozenset({resource}))
```

- **`governing(R)` owns the coverage rule (B2).** It returns the set of resources whose grants reach R: R
  itself plus every ancestor. It follows from that:
  - Inheritance flows down only. `governing("finance")` contains no child.
  - A resource the hierarchy does not mention is its own root, so only its exact grants apply.
  - A group can be asked about directly: it is just a resource with its own governing set.
- **`of(parents)` owns the tree invariants.** It computes each named resource's governing set by walking up
  parents. The same walk detects every cycle, including a self-parent, which is a cycle of length 1. If any
  cycle exists, it raises one `ValueError` whose message lists each cycle once (`"cycle: a → b → a"`,
  `"cycle: x → x"`). No `_Hierarchy` with a cycle can exist, so no query-time walk can loop.
- **"At most one parent" is not checked. The seam makes a second parent impossible to express.** A `Mapping`
  holds one value per key. The only ways to name a child twice are already rejected by existing owners: in the
  JSON file, a repeated key (A7, `json_file`); in code, two keys that are identical once normalized (stage-1
  constructor phase 1 step 4). No new guard is added.
- **Why the governing sets are computed at build.** They are a property of the hierarchy alone: a closure of
  model facts, not a decision. They do not depend on grants, users or time. Computing them at build is what
  makes cycle rejection and query-time termination one fact. This is not the "precomputed effective
  permissions" stage 1 rejected: no grant, effect or window is folded into it.

### 3.6 `_Grant` — REPLACES stage-1 `_Permission`

```python
@dataclass(frozen=True, slots=True)
class _Grant:
    effect: _Effect
    action: str
    resource: str
    window: _Window
    def applies_to(self, q: "_Question") -> bool:
        # self.action == q.action and self.resource in q.governing and self.window.contains(q.instant)
```

- **Value equality over all four fields is grant identity for A6.** Exact duplicates collapse in the role's
  `frozenset`. The same `(effect, A, R)` with two windows gives two grants, and each applies in its own window.
  An allow and a deny for the same `(A, R)` are two grants, and both survive.
- **`applies_to` owns the conjunction and nothing else.** It holds the action-exactness clause itself (A4:
  string equality, no implication; this is what `_Permission` equality owned in stage 1). It delegates coverage
  to the set that `_Hierarchy.governing` produced, and in-force to `_Window.contains`. It returns `bool`. It
  cannot say allow or deny.
- **Why `_Permission` is removed (supersedes stage-1 §3.2).** In stage 1, `_Permission` equality *was* the
  match rule. With a hierarchy, a grant on `finance` matches a question about `doc-42`, so equality between
  permissions is no longer the match rule. A `_Permission` kept only as an `(action, resource)` pair inside
  `_Grant` would own nothing. Its identity role moves into `_Grant` equality, and its matching role into
  `applies_to`.

### 3.7 `_Role` — the role clause, reshaped

```python
@dataclass(frozen=True, slots=True)
class _Role:
    grants: frozenset[_Grant]
    def effects_for(self, q: "_Question") -> frozenset[_Effect]:
        # frozenset(g.effect for g in self.grants if g.applies_to(q))
```

It owns "what this role says about this question": the effects of the grants that apply. It supersedes
`grants(permission) -> bool`, because a role can now say two things at once, allow and deny. A `bool` cannot
carry that, and a per-role `Decision` would be wrong (§9, decision 1b). The stage-1 reasons for `_Role` still
hold: the rule is phrased over roles, users map to resolved role objects, and A3 holds structurally.

### 3.8 `_Question` — NEW, the validated question

```python
@dataclass(frozen=True, slots=True)
class _Question:
    action: str                 # _identifier result
    governing: frozenset[str]   # _Hierarchy.governing(resource) — computed once per question
    instant: datetime           # _instant result
```

It is built only inside `decide`, after all four parts are parsed. It is the only thing that reaches roles and
grants. So "validate the whole question before any lookup" is a structural fact: no lookup can take unparsed
values. It also carries the governing set, computed once, so no grant touches the hierarchy.

### 3.9 `_combine(effects) -> Decision` — NEW, the sole owner of the combining rule

```python
def _combine(effects: frozenset[_Effect]) -> Decision:
    # DENY if _Effect.DENY in effects; else ALLOW if _Effect.ALLOW in effects; else DENY
```

- It is the only code in the package that produces `Decision.ALLOW` or `Decision.DENY` (fitness test, §8).
- It is **order-free and total**. The input is a set, so role order, grant order and path depth cannot affect
  the result. There are exactly four inputs, and each is tested.
- Its last branch is the stage-1 default: no applicable grant means deny. That branch is the *absence* case.
  The first branch is the *explicit* case. Both give `Decision.DENY` for different reasons, and each reason is
  named once.

### 3.10 `EntitlementModel`

Representation: `__slots__ = ("_roles_of", "_hierarchy")`.

- `_roles_of: Mapping[str, frozenset[_Role]]` is unchanged in shape.
- `_hierarchy: _Hierarchy` is new.

Immutability rules are unchanged: `__setattr__`/`__delattr__` raise, and inputs are copied.

**Constructor. The stage-1 two-phase contract is kept, and the new inputs slot into it.**

*Phase 1 — parse (stops at the first error):*
1. Each argument must be a `Mapping`. This now includes `parents`.
2. `roles`: each grant goes through `_parse_grant`, in the pair or mapping form (§2.1).
   - Identifiers go through `_identifier`.
   - `effect` goes through `_Effect`.
   - Bounds go through `_instant`, then `_Window(...)`, which rejects `from >= to`.
   - An unknown mapping key is rejected.
   - Errors carry their location: `role 'editor', grant #2: to must be timezone-aware, got 2026-10-01T00:00:00`.
3. `assignments`: unchanged.
4. `parents`: each key and value goes through `_identifier(…, "resource")`, into a local dict child → parent.
5. Normalized-duplicate keys are rejected in every mapping, `parents` included (a second parent via a
   `str` subclass is caught here).

*Phase 2 — consistency (reports every violation in one `InvalidModelError`):*
6. Resolve assigned role names (unchanged, A3). Collect every `(user, undefined role)` pair.
7. Build `_Hierarchy.of(parents)`. Collect its cycle report if it raised.
8. If either step found problems, raise one `InvalidModelError` that lists all of them. Otherwise freeze and
   store.

Why cycles belong in phase 2: a cycle is well-formed but inconsistent, like a dangling role, and several can
occur at once. The stage-1 rule, "malformed → first problem; inconsistent → all problems", absorbs the new
case unchanged.

**`decide(user, action, resource, *, now) -> Decision`:**

1. Parse the question in order: user, action, resource (`_identifier`), then now (`_instant`). The first bad
   part raises `InvalidQuestionError` naming that part. This happens before any lookup, so an unknown user
   asked with a naive `now` raises.
2. `q = _Question(action, self._hierarchy.governing(resource), now)`.
3. `effects` = the union of `role.effects_for(q)` over `self._roles_of.get(user, ∅)`. `decide` owns only the
   quantifier "from **any** of U's roles". It gathers without deciding.
4. `return _combine(effects)`.

It is a pure query. It reads only `self`, which is immutable, so there is no torn read between the hierarchy
and the grants (§6).

## 4. Where each rule lives

| Rule | Sole owner | Enforced how | Reached via |
|---|---|---|---|
| **Combining: deny overrides allow; no applicable grant → deny (B1)** | `_combine` | only producer of `Decision` values (fitness test); input is a set, so order-free | `decide` step 4 |
| a deny/allow from **any** of U's roles counts (quantifier) | `decide` step 3 | union of effect sets; roles return effects, not decisions | host/CLI → `decide` |
| what one role says about a question | `_Role.effects_for` | returns `frozenset[_Effect]` | `decide` |
| a grant bears on a question iff action exact ∧ resource governs ∧ in force | `_Grant.applies_to` | one path for both effects (B5 by construction) | `_Role` |
| action exactness, no action hierarchy (A4) | `_Grant.applies_to` (string equality) | — | — |
| **coverage: grants on R and on every ancestor reach R; down only; unmentioned = own root (B2)** | `_Hierarchy.governing` | closure computed at build | `decide` step 2 → `_Question` |
| **tree is acyclic, no self-parent (B2)** | `_Hierarchy.of` | a cyclic `_Hierarchy` cannot be constructed | constructor phase 2 |
| at most one parent (B2) | the `Mapping` seam type | two parents are unrepresentable; repeats rejected by existing A7 owners | — |
| **in force: `[from, to)`, open bounds (B3)** | `_Window.contains` | — | `_Grant.applies_to` |
| `from < to` (B3) | `_Window.__post_init__` | an invalid `_Window` cannot be constructed | `_parse_grant` |
| **supplied instants are aware, compared by instant (B3, B4)** | `_instant` | normalized to exact UTC `datetime` | constructor bounds; `decide` now |
| no window = always in force | `_ALWAYS` in `_parse_grant` | — | — |
| effect vocabulary, exact | `_Effect` (by-value lookup) | — | `_parse_grant` |
| absent effect = allow; pair form = allow always | `_parse_grant` | one parse path for both forms | constructor |
| grant identity / set semantics over (effect, A, R, window) (A6) | `_Grant` + `_Window` value equality (UTC-normalized) | `frozenset` | constructor |
| identifier rule (A4) | `_identifier` | unchanged | — |
| undefined role rejected (A3) | constructor phase 2 | unchanged | — |
| malformed → first; inconsistent → all | constructor | unchanged; cycles join phase 2 | — |
| question validated before lookup (A2) | `decide` step 1 | `_Question` is the only way in | — |
| model immutable, whole-swap, no torn read (A1) | `EntitlementModel` | hierarchy and grants in one immutable object | host rebinds |
| the library never reads the clock (B4) | *absence*, enforced by fitness test | — | — |
| wall-clock default for `now` | `cli` | — | — |
| ISO-8601 text ⇄ datetime | `json_file` (bounds), `cli` (`--now`) | each parses text only; awareness stays with `_instant` | — |
| file shape, repeated keys (A7) | `json_file` | unchanged; now covers `parents`, `effect`, `from`, `to` | — |

Each rule's owner states only its own rule. Changing precedence (for example, to "allow overrides") reopens
only `_combine`. Changing coverage (multiple parents) reopens only `_Hierarchy` and the `parents` seam. Changing
validity (recurring windows) reopens only `_Window` and its parse step.

## 5. JSON file format changes (`json_file.py`)

```json
{
  "roles": {
    "staff":   [ {"action": "read", "resource": "org-root"} ],
    "finance": [ {"action": "write", "resource": "finance"},
                 {"effect": "deny", "action": "write", "resource": "doc-42",
                  "from": "2026-10-01T00:00:00Z", "to": "2026-11-01T00:00:00+00:00"} ],
    "auditor": []
  },
  "assignments": { "alice": ["staff", "finance"], "bob": [] },
  "parents":     { "doc-42": "finance", "doc-43": "finance", "finance": "org-root" }
}
```

- Top level: `roles` and `assignments` are required, `parents` is optional, and any other key is rejected. A
  stage-1 file, with exactly two keys, loads unchanged.
- A grant object requires `action` and `resource`. It may add `effect`, `from` and `to`. Any other key is
  rejected, so a typo such as `"until"` cannot silently widen a window.
- `effect`, if present, must be a JSON string. Its *value* is checked by the core.
- `from`/`to`, if present, must be JSON strings in ISO-8601 form, parsed with `datetime.fromisoformat`.
  Unparseable text becomes `InvalidModelError` with its location. **A naive result is passed through
  unchanged**, and the core rejects it. The edge does not decide awareness, so it cannot disagree with in-code
  construction. `null` is not accepted: an open bound is written by leaving the key out, so there is one
  spelling for it.
- `parents` must be an object whose values are strings. A repeated child key is rejected under A7, which is
  what "two parents" looks like in a file. An array value such as `"doc-42": ["finance", "hr"]` is a shape
  error.
- After converting only the text times, the edge passes each grant to the constructor as the in-code mapping
  form (§2.1). The edge adds no defaults. "Absent effect = allow" stays in `_parse_grant`.

## 6. CLI changes (`cli.py`)

`python -m entitlements --model PATH [--now ISO8601] USER ACTION RESOURCE`

- `--now` is parsed with `datetime.fromisoformat`. Unparseable text is an argparse usage error: exit 2.
- When `--now` is absent, the CLI passes `datetime.now(timezone.utc)`. The CLI is the imperative shell (B4),
  and this is the only clock read in the package.
- A naive `--now` is passed through unchanged. The core raises `InvalidQuestionError`, and the CLI prints one
  line on stderr and exits 2. The CLI does not decide awareness.
- Output and exit codes are unchanged (A8).

## 7. Adversarial cases traced through the design

The fixture uses the hierarchy `doc-42 → finance`, `doc-43 → finance`, `finance → org-root`. So
`governing(doc-42) = {doc-42, finance, org-root}` and `governing(finance) = {finance, org-root}`. Unlisted
`memo-7` has `governing(memo-7) = {memo-7}`. "E" is the union of effects that `decide` passes to `_combine`.

### 7.1 Deny
| Case | Trace | E | Result |
|---|---|---|---|
| role X allows, role Y denies same (A,R) | X gives {ALLOW}, Y gives {DENY} | {ALLOW, DENY} | DENY |
| one role both allows and denies (A,R) | two distinct `_Grant`s (effect differs) both survive A6, both apply | {ALLOW, DENY} | DENY |
| deny (write,R); ask (read,R) with an allow (read,R) | deny fails the action clause | {ALLOW} | ALLOW |
| deny (read,R1); ask (read,R2) with an allow (read,R2) | R1 ∉ governing(R2) | {ALLOW} | ALLOW |
| user holding only deny grants, one applies | — | {DENY} | DENY |
| user holding only deny grants, none apply | — | ∅ | DENY (absence branch) |

### 7.2 Hierarchy
| Case | Trace | E | Result |
|---|---|---|---|
| allow (read, org-root); ask doc-42 (depth 2) | org-root ∈ governing(doc-42) | {ALLOW} | ALLOW |
| allow finance + deny doc-42; ask doc-42 | both ∈ governing(doc-42) | {ALLOW, DENY} | DENY |
| same model; ask sibling doc-43 | doc-42 ∉ governing(doc-43) = {doc-43, finance, org-root} | {ALLOW} | ALLOW |
| deny org-root + allow doc-42; ask doc-42 | both apply; no specificity ordering exists anywhere | {ALLOW, DENY} | **DENY** (a "most specific wins" design would say ALLOW) |
| deny doc-42 + allow finance; ask finance | doc-42 ∉ governing(finance) (down only) | {ALLOW} | ALLOW |
| grant on finance; ask unlisted memo-7 | governing = {memo-7} | ∅ | DENY; an exact grant on memo-7 alone would allow |
| ask a group (finance) directly with a grant on finance | finance ∈ its own governing set | {ALLOW} | ALLOW |
| `parents={"a": "b", "b": "a"}` | `_Hierarchy.of` → cycle | — | `InvalidModelError` "cycle: a → b → a" |
| `parents={"x": "x"}` | cycle of length 1 | — | `InvalidModelError` |
| two parents in a file (`"doc-42"` repeated) | A7 `object_pairs_hook` | — | `InvalidModelError` (repeated key) |
| two parents in code | a `Mapping` cannot hold them; normalized-duplicate `str`-subclass keys → phase 1 step 5 | — | `InvalidModelError` |
| cycle + undefined role in one model | both collected in phase 2 | — | one error listing both |

### 7.3 Time (window `[t0, t1)`)
| Case | Trace | Result |
|---|---|---|
| now = t0 | `start <= instant` | in force |
| now = t1 | `instant < end` fails | not in force |
| now < t0 | — | not in force |
| only `from`, or only `to`, or neither (`_ALWAYS`) | `None` side skipped | open-ended |
| `from >= to` (including equal) | `_Window.__post_init__` | `InvalidModelError` with location |
| naive bound in model (code or file) | `_instant` | `InvalidModelError` |
| naive `now` | `_instant` in `decide` step 1 | `InvalidQuestionError`, even for an unknown user |
| `now` = `12:00+02:00` vs `10:00Z` at a window edge | both normalized to `10:00Z` | identical answers |
| window bounds written in different offsets for the same instants | normalized, so equal `_Window` values | collapse under A6 |
| an expired deny and a permanent allow | deny fails `contains` | {ALLOW} → ALLOW |
| a not-yet-valid allow only | fails `contains` | ∅ → DENY |

### 7.4 Interactions
| Case | Trace | Result |
|---|---|---|
| deny on finance windowed `[t0,t1)` + permanent allow on doc-42; ask doc-42 at t (t0 ≤ t < t1) | {ALLOW, DENY} | DENY |
| same, at t < t0 or t ≥ t1 | {ALLOW} | ALLOW |
| same (allow, A, R) with windows `[t0,t1)` and `[t2,t3)` | two grants; each applies in its window | ALLOW inside either, DENY in the gap |
| adjacent windows `[t0,t1)` and `[t1,t2)` at t1 | the second applies | ALLOW |
| exact duplicate grant (all four fields) | `frozenset` | same answers as once |
| deny from a role the user does not hold | not in `_roles_of[user]` | no effect |
| two roles with identical grant sets | collapse to one `_Role` (as in stage 1); the union of effects is unchanged | no observable effect |

### 7.5 Crossing each new axis with each existing rule (§1 trace, beyond the listed cases)
- **Unknown user × deny, hierarchy or time:** no roles, so E = ∅ and the answer is DENY. The absence branch is
  unchanged.
- **Malformed question × new input:** a bad `now` is checked after user, action and resource, in order. A
  model's validity never depends on `now`.
- **A3 × hierarchy:** the hierarchy has no cross-references to validate. Grants and questions may name
  resources absent from `parents`. `parents` may name resources that no grant names.
- **A4 exactness × hierarchy:** `parents` keys are compared exactly. `Finance` is not `finance`, so a grant on
  `Finance` does not reach `doc-42`.
- **A6 × effect:** allow and deny for the same `(A, R, window)` stay two grants. Collapsing them would lose the
  deny.
- **Role collapse × deny:** equal roles collapse, and the union of effects is the same.
- **Time × assignments:** not time-bounded (B5). The instant reaches only `_Window`.
- **Time × hierarchy:** the hierarchy is not time-bounded (assumption A11). The instant never reaches
  `_Hierarchy`.

### 7.6 Stage-1 preservation
With no deny, no `parents` and no window, the following hold:
- Every grant is `(ALLOW, a, r, _ALWAYS)`.
- `governing(r) = {r}`, so `self.resource in q.governing` is the same as `self.resource == r`, which is
  stage-1 `_Permission` equality.
- `_ALWAYS.contains(t)` is true for every `t`.

So E is {ALLOW} exactly when some role holds `(a, r)`, and ∅ otherwise. `_combine` then gives ALLOW or DENY,
which is the stage-1 expression. Every row of stage-1 §3.4 and every case of §8 answers identically for any
aware `now`. The stage-1 JSON example file loads and answers identically. The only stage-1-visible change is
the signature: `now` is required.

### 7.7 Model immutability and replacement
The hierarchy and the grants are fields of the same immutable object. A question reads `self` only, so it
cannot pair one model's hierarchy with another's grants. Replacement is still: build a new model, then rebind
the reference. A failed build (a cycle, a bad window) raises before any rebind.

## 8. Test plan (test-first, behavior through public seams, stdlib `unittest`)

The characterization suite comes first. **Every stage-1 test is kept and passes unchanged in meaning.** The
only mechanical edit is adding `now=T` (one fixed aware instant) to each `decide` call. A parametrized
wrapper also runs the whole stage-1 grant-rule suite at several `now` values (a far past value, `T`, a far
future value, and a non-UTC offset) and asserts identical answers.

- **Combining rule (`_combine`, via `decide` with minimal models):** the four effect sets ∅, {A}, {D}, {A,D} →
  DENY, ALLOW, DENY, DENY. The same checks run with the allow and deny coming from two roles, one role, and two
  levels of the path. Role declaration order is permuted, and the answer does not change.
- **Deny:** every §7.1 row.
- **Hierarchy:** every §7.2 row, plus:
  - depth 3;
  - a leaf asked with no grants anywhere → DENY;
  - a parent-only root (org-root) asked directly;
  - a cycle report listing two independent cycles at once;
  - a resource hanging off a cycle, where only the cycle is reported;
  - case-exact `parents` keys;
  - a `str`-subclass second parent → `InvalidModelError`;
  - `parents` that is not a mapping, and non-string parent values → `InvalidModelError`.
- **Time:** every §7.3 row, plus:
  - `now` of type `date`, `str`, `None` or `int` → `InvalidQuestionError`, never `TypeError` or DENY;
  - a `datetime` subclass is accepted and behaves like the base value;
  - a tzinfo whose `utcoffset` returns `None` is rejected;
  - overflow at `datetime.min`/`datetime.max` with an offset → error, not a crash;
  - a DST-fold instant in a `zoneinfo` zone at a window edge answers by instant;
  - calling `decide` without `now` → `TypeError` (the signature contract).
- **Interactions:** every §7.4 row.
- **Grant declaration:**
  - the pair form and `{"action", "resource"}` give identical decisions;
  - an explicit `"effect": "allow"` equals an absent effect;
  - `"Deny"`, `""` and `5` as effect → `InvalidModelError`;
  - an unknown key in the mapping → error;
  - a bare-`str` grant is still rejected;
  - a malformed window *and* a cycle in one model → the window (parse) error is reported, not the cycle.
- **Immutability:**
  - mutating the caller's `parents` or grant mappings after construction changes nothing;
  - the public surface is still exactly `{decide}`;
  - `__all__` is unchanged.
- **Replacement/concurrency:** the stage-1 stress test is extended. Two models differ in *both* hierarchy and
  grants, chosen so that a torn mix gives an answer neither model gives.
- **File edge:**
  - the §5 example answers as traced;
  - a stage-1 file loads and answers identically;
  - bad ISO text, `null` bound, non-string effect, unknown grant key (`"until"`), non-object `parents`, array
    parent, repeated `parents` key → `InvalidModelError` with the path;
  - a naive ISO bound is rejected *by the core* (the message matches the in-code error);
  - the same model built in code and from the file answers identically over a grid of questions × `now`
    values.
- **CLI:**
  - `--now` inside and outside a window flips the answer and exit code;
  - bad `--now` text → usage error, 2;
  - naive `--now` → stderr, 2, no traceback;
  - without `--now`, a model whose window contains the real present allows. The test uses a wide window
    around the test run, so it needs no clock fake.
- **Architecture fitness (AST over `model.py`):**
  - imports are within {dataclasses, enum, types, collections.abc, datetime};
  - no call to `now`, `today`, `utcnow`, `time.*`;
  - **`Decision.ALLOW`/`Decision.DENY` are referenced only inside `_combine`**. This is the unforgeable single
    owner of the combining rule, pinned as a test;
  - `import entitlements` does not load `json`.

## 9. Key decisions and alternatives rejected

1. **Where precedence lives: one pure function over the set of applicable effects.** Rejected alternatives:
   - **(a)** `decide` loops and returns early on the first deny or allow. Precedence then depends on loop
     structure, and an early `return ALLOW` is one edit away. The rule would be spread over control flow.
   - **(b)** Each role returns a `Decision`, and those decisions are combined. This is **wrong, not just
     inelegant.** A role with no applicable grant would report `DENY`, which cannot be told apart from an
     explicit deny, so "X allows, Y has nothing" would come out DENY. That is the "deny as a missing allow"
     concept error, one level up. It is why clauses return effects and never decisions.
   - **(c)** Walk the path and let the most specific grant win. This contradicts B1 (the org-root deny case).
   - **(d)** Precompute effective effects per (user, resource) at build. Time makes this impossible without a
     per-instant table, and it would fold three owners into the constructor.
2. **Deny as a first-class `_Effect` on the grant, separate from `Decision`.** Rejected alternatives:
   - Parallel `allows`/`denies` sets per role. That gives two applicability paths, one of which could forget
     the window or the hierarchy (B5 would then hold only by discipline).
   - Reusing `Decision` as the effect. The absence-deny and the explicit deny would share one value, and the
     fitness test "only `_combine` produces a Decision" would become impossible.
3. **The hierarchy is owned by `_Hierarchy`, and coverage is its `governing` set.** Rejected alternatives:
   - Walking parents at query time. That needs cycle safety at query time, or trusts a check made somewhere
     else.
   - Expanding grants down to descendants at build. This destroys grant identity (A6 over four fields) and
     mixes coverage into parsing.
   - Checking "one parent" with a guard. The `Mapping` seam makes a second parent unrepresentable.
4. **"Now" crosses as a required, keyword-only, aware `datetime`, normalized once by `_instant`.** Rejected
   alternatives: a `Clock` port (it reads time inside the core and risks two instants per decision), an
   optional `now` (B4), and assuming UTC for naive values (B3).
5. **No new public types; the stage-1 pair form is kept as one entry into the single grant parser.** Rejected
   alternatives: a public `Grant` dataclass or `TypedDict` (a second validation owner or a dumb bag), and
   dropping the pair form (it would break every stage-1 host model for no gain).
6. **`_Permission` is superseded by `_Grant`, and `_Role.grants` by `_Role.effects_for`.** Both are recorded
   as supersessions of stage-1 §3.2–3.3 and not left as dead code.
7. **The core stays one module** (§1), with a stated falsifier.

## 10. Assumptions added (A10–A15; B1–B5 are given)

- **A10 — grant declaration.** The stage-1 pair means allow with no window. The mapping form's absent
  `effect` means allow. The effect vocabulary is exact `"allow"`/`"deny"`, and case matters (A4 spirit).
- **A11 — the hierarchy is not time-bounded.** It is declared as a `parents` map (child → parent) and is
  optional. It needs no cross-reference to grants or questions.
- **A12 — JSON times are ISO-8601 strings** (`fromisoformat`, `Z` accepted). An open bound is an absent key,
  and `null` is rejected.
- **A13 — CLI `--now`** takes ISO-8601 with an offset. It defaults to the wall clock in UTC. A naive `--now` is
  an error, not local time.
- **A14 — the `decide` signature gains a required keyword `now`.** A stage-1 three-argument call raises
  `TypeError`. The answers are preserved.
- **A15 — instants outside the representable UTC range** after normalization are rejected as malformed.
- **Cycle reporting:** every cycle is reported once, in phase 2, together with undefined roles. Resources that
  merely hang off a cycle are not reported separately.

## 11. Deliberately not built

- Public `Grant`/`Window`/`Effect`/`GrantSpec` types.
- A `Clock` interface.
- Precomputed effective permissions.
- Most-specific-wins resolution.
- Priorities.
- Explanations (A5).
- Time-bounded assignments or hierarchy.
- Multiple parents or a DAG.
- Action hierarchy, wildcards, role inheritance, conditions.
- `null` window bounds.
- Naive-to-UTC defaulting.
- Resource registry or validation of hierarchy against grants.
- Holder/service, caching, logging.

Each lacks a present force.

## 12. Subtractive pass (each added element and its present force)

| Element | Present force | Kept? |
|---|---|---|
| `_Effect` | concept fit: an explicit deny is a value, not an absence (package, §4 of the principles); makes `Decision` producible by `_combine` alone | kept |
| `_Window` | owns the in-force clause and the `from < to` invariant (B3) | kept |
| `_ALWAYS` | removes an `Optional` branch; stage-1 grants take the same path | kept (a constant, not a type) |
| `_instant` | the awareness + by-instant rule at two entries (model, question); the same-tzinfo comparison pitfall | kept |
| `_Hierarchy` | tree invariants + coverage (B2); a cycle-free structure by construction | kept |
| `_Grant` | A6 identity over four fields; one applicability path for both effects (B5) | kept (replaces `_Permission`) |
| `_Question` | makes validate-before-lookup structural; carries the governing set computed once; avoids a three-value clump through two layers | kept (lightest of the set; falsifier: if it gains no second field consumer, fold it) |
| `_combine` | the combining rule's single owner; the fitness test anchors to it | kept |
| a `_Lineage`/`_Path` type wrapping the governing set | only membership was left in it, so it owned no rule | **removed** — `frozenset[str]` |
| a separate `_effect()` parser | `_Effect(value)` lookup already owns the vocabulary | **removed** |
| a guard for "two parents" | unrepresentable at the `Mapping` seam; repeats caught by existing A7 owners | **removed** |
| `_Permission` | no longer the match rule, so it would own nothing | **removed** (superseded) |
| a public grant `TypedDict` | no consumer needs it; a docstring suffices | **not added** |
| splitting the core into modules | no divergent change axis yet; it would expose private types across modules | **not done** |
