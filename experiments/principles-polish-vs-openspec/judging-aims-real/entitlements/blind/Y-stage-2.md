# Design Y — stage 2

---
title: "Entitlements decision service — architecture (stage 2: explicit deny, resource inheritance, validity windows)"
date: 2026-09-23
status: final — stage-2 panel merge, revised after one mandatory review round; supersedes the stage-1 text of this file (kept in decisions/0002 and git history)
---

# Entitlements decision service — stage 2

**Question answered:** may user U perform action A on resource R, at instant *now*? → `allow` | `deny`.

**Rule (B1):** **DENY** if any in-force **deny** grant from any of U's roles covers (A, R), either on R itself or
on one of R's ancestors. Otherwise **ALLOW** if any in-force **allow** grant does. Otherwise **DENY**.

**Substrate:** Python 3.11+, standard library only, single process, no persistence (`base-dependencies.md`).

**Assumptions:**
- A1–A6 and B1–B5 are in `goals.md`.
- A7–A9 carry over from stage 1 (§12).
- This stage adds A10–A17 (§12).

## 1. Shape

The stage-1 shape survives. It is one immutable `EntitlementModel` that:
- holds the whole entitlement model, which now includes the resource hierarchy;
- is built by one keyword-only constructor;
- answers through one public query, `decide`.

JSON loading and the CLI remain thin edges that end in that constructor and in `decide`. The reopen lands
where decisions/0002 said it would: in `decide` and in the role clause.

The central move is to **separate the clauses that can only produce *effects* from the one function that
turns effects into a `Decision`**:

```
decide(u, a, r, now=t)
  ├─ parse the whole question            _identifier ×3, _instant           (before any lookup)
  ├─ lineage = hierarchy.lineage(r)      R ∪ its ancestors, a set            (_Hierarchy owns "reach")
  ├─ effects = ⋃ role.effects(a, lineage, t) over U's roles                  (decide owns "any of U's roles")
  │              └─ {g.effect | g.applies(a, lineage, t)}                   (_Role → _Grant)
  │                                    └─ action == a ∧ resource ∈ lineage ∧ window.contains(t)
  └─ return _combine(effects)            the ONLY producer of a Decision     (deny overrides allow)
```

Three consequences carry the design:

- **Precedence has one owner, and that owner cannot see what must not matter.** `_combine` receives a
  `frozenset` of effects. It cannot see roles, hierarchy levels, time or declaration order. B1 says none of
  these affects precedence, and the input type enforces that. A "most specific wins" rule could not be
  written as a local edit, because it would need a wider input type and so would reopen the owners.
- **Deny is a first-class effect, not a missing allow.** `_Effect.DENY` is a value that a grant carries.
  `Decision.DENY` is an answer that has two different causes: an explicit deny, or no applicable grant at all.
  Each cause is a separate branch of `_combine`.
- **Clauses cannot decide.** `_Hierarchy`, `_Window`, `_Grant` and `_Role` return sets or `bool`, and never
  a `Decision`. As a result, no role can "deny by having nothing" and no level can short-circuit the decision
  (§11, decision 1b).

## 2. Module skeleton

```
entitlements/                 Python 3.11+, stdlib only, no runtime or test dependencies
├── __init__.py   public core re-exports (unchanged set); does NOT import the edges
├── model.py      CORE  errors · _identifier · _instant · _Effect · _Window · _Grant · _Role · _Hierarchy ·
│                       _parse_grant · _combine · Decision · EntitlementModel
├── json_file.py  EDGE  load_model(path) — owns the file format (gains: parents, effect, from/to as ISO text)
├── cli.py        EDGE  main(argv) — owns argv, the wall clock, output text, exit codes (gains: --now)
└── __main__.py   EDGE  raise SystemExit(main())       (unchanged)
tests/            stdlib unittest
```

Dependencies are unchanged, acyclic and point to the core: `__main__ → cli → json_file → model` and
`cli → model`.

The core's import allow-list grows by one module:
- **allowed:** `dataclasses`, `enum`, `types`, `collections.abc`, and now **`datetime`** (a pure value
  library, not I/O);
- **still forbidden:** `json`, `argparse`, `os`, `pathlib`, `sys`, `io`, `threading`, `time`;
- **never called:** the clock readers `datetime.now`, `.utcnow` and `.today` (B4). Checked as attribute
  access, so the `now` *parameter* of `decide` is not affected.

A fitness test enforces all of this (§10).

**Why the core stays one module** (this re-examines stage-1 §1 and keeps it).
- The new private types (effect, window, grant, hierarchy) change for the same reason as the old ones: a
  change in the entitlement rules.
- Each is used only by the constructor and `decide`.
- Splitting out `_time.py`/`_hierarchy.py` would make `_identifier`, the error types and the private types
  importable across a module seam, only to reach a pair of 30-line modules. The genericity draft proposed
  this split, flagged it as thin itself, and noted that folding it back changes no owner.
- The core grows from about 100 to about 230 lines.

**Falsifier:** split a concept into its own module the day it gains a rule family of its own. Examples: time
gaining recurring windows or calendars, or the hierarchy gaining multiple parents, typed groups, or a
separate supplier on its own schedule.

## 3. Public API — everything that crosses a seam

```python
# entitlements (re-exported from entitlements.model) — __all__ unchanged
class Decision(enum.Enum):                                   # unchanged (A5)
    ALLOW = "allow"
    DENY = "deny"

class EntitlementModel:
    def __init__(
        self,
        *,
        roles: Mapping[str, Iterable[tuple[str, str] | Mapping[str, object]]],
                                        # role -> its grants (§3.1: stage-1 pair, or a grant mapping)
        assignments: Mapping[str, Iterable[str]],            # user -> its roles   (unchanged)
        parents: Mapping[str, str] = _NO_PARENTS,            # NEW, optional: resource -> its one parent group
    ) -> None: ...                                           # raises InvalidModelError
    def decide(self, user: str, action: str, resource: str, *, now: datetime) -> Decision: ...
                                                             # raises InvalidQuestionError

class EntitlementsError(Exception): ...                      # unchanged
class InvalidModelError(EntitlementsError, ValueError): ...
class InvalidQuestionError(EntitlementsError, ValueError): ...

# entitlements.json_file
def load_model(path: str | os.PathLike[str]) -> EntitlementModel: ...   # unchanged signature

# entitlements.cli
def main(argv: Sequence[str] | None = None) -> int: ...      # unchanged signature; 0 allow · 1 deny · 2 error
```

`_NO_PARENTS = MappingProxyType({})` is a module constant, so there is no mutable default. **No new public
type is added.** Only stdlib types cross the seam (`str`, `tuple`, `Mapping`, `Iterable`, `os.PathLike`, and
now `datetime`), together with the package's own published `Decision` and errors.

Host use:

```python
T = datetime(2026, 9, 23, 12, tzinfo=timezone.utc)
model = EntitlementModel(
    roles={
        "finance-reader": [("read", "finance")],                       # stage-1 pair: allow, always
        "freeze":         [{"action": "read", "resource": "doc-42", "effect": "deny",
                            "to": datetime(2026, 10, 1, tzinfo=timezone.utc)}],
    },
    assignments={"alice": ["finance-reader", "freeze"]},
    parents={"doc-42": "finance", "doc-43": "finance", "finance": "org-root"},
)
model.decide("alice", "read", "doc-43", now=T)   # ALLOW — inherited from finance
model.decide("alice", "read", "doc-42", now=T)   # DENY  — in-force deny on the leaf beats the inherited allow
model.decide("alice", "read", "doc-42", now=datetime(2026, 10, 1, tzinfo=timezone.utc))  # ALLOW — deny expired
```

### 3.1 Grant declarations — two spellings, one parser, one internal value

| Spelling | Meaning |
|---|---|
| `(action, resource)`: a 2-item sequence that is neither a `str` nor a `Mapping` (**the stage-1 in-code form, unchanged; in code only**, the file has one spelling, §6) | an allow with no window, always in force |
| `{"action": a, "resource": r}`, optionally with `"effect"`, `"from"`, `"to"` | exactly as written |

In the mapping form:
- **`effect`** is optional and defaults to allow (A10). Its value is `"allow"` or `"deny"`: exact,
  case-sensitive, and any `str` instance including a `StrEnum` member.
- **`from` / `to`** are each optional and must be an aware `datetime`. An absent key means an open bound.
  `None` is rejected (A12), so there is one spelling for "open".
- **Any other key is rejected.** Otherwise `"efect": "deny"` would load as an *allow*, and `"until"` would
  silently leave a window open.

Both spellings go through `_parse_grant` into one `_Grant`, so the pair is an entry point into the one
parser, not a second rule. `_parse_grant` checks `Mapping` **before** it checks for a pair. A two-key dict is a
length-2 iterable and would otherwise unpack into its *keys*. This is the same bare-string guard stage 1
applied to grants and assignments.

### 3.2 Seam calibration (additions to stage 1)

| Seam | Floor (what the consumer needs) | Ceiling (what every producer can supply) | Type |
|---|---|---|---|
| "now" in | the in-force clause needs one instant | host code holds `datetime`; the CLI has argv or the clock | `now: datetime`: **keyword-only, required, aware** |
| grant in | effect, action, resource, two optional bounds | host dicts/pairs; JSON objects | pair, or a `Mapping` with the **file's key names** |
| hierarchy in | at most one parent per resource | host dict; JSON object | `parents: Mapping[str, str]` (child → parent) |
| hierarchy → grant match (internal) | "is this grant's resource among those whose grants reach R?" | the tree yields R plus its ancestors | `frozenset[str]` (the **lineage**) |
| grants → precedence (internal) | "is there an applicable deny? an applicable allow?" | each grant knows its effect | `frozenset[_Effect]` |
| answer out | unchanged (A5) | — | `Decision` |

**Why `now` is a value, not a `Clock` port.** "Now" is part of the question (B4), not a dependency of the
model. A clock inside the core could be read twice in one decision, giving a torn instant, and every test
would need a fake. As a value, `now` is fixed once at the seam and carried unchanged to the one clause that
uses it.

**Why `now` is keyword-only.** As a fourth positional slot, a `datetime` would sit beside three strings, and
the call site would not say what it is. With a keyword, the call reads as the question:
`decide("alice", "read", "doc-42", now=t)`.

**Why a mapping and not a public `Grant` dataclass** (this was a decided split, §11 decision 5).
- A mapping uses the **same vocabulary as the file**, so `effect`/`from`/`to` and the `"allow"`/`"deny"`
  words each have one owner (the core), whichever edge they came through.
- A public `Grant` type would have to either validate itself (a second owner of the identifier, instant and
  window rules) or be a bag the constructor validates anyway.
- It would also push the file edge into translating `"deny"` into an enum, which is a second owner of the
  effect vocabulary.
- The cost is that a misspelled key is caught when the model is built, not by a type checker. The key is still
  caught, with its location.

**Why `parents` is child → parent, not group → members.** A `Mapping` holds one value per key, so "two parents"
**cannot be represented** and needs no guard. The only ways to name a child twice are already rejected by
existing owners:
- a repeated key in the file (A7, `json_file`);
- two in-code keys that normalize to the same string (constructor phase 1).

**Why lineage is a set, not an ordered path.** Matching needs only membership. B1 makes specificity
irrelevant. An ordered path would be more specific than any consumer needs, and it is exactly the shape that
invites the wrong rule.

**The one deliberate break at the question seam.** A stage-1 call `decide(u, a, r)` now raises Python's
`TypeError` for the missing required keyword. B4 requires this: the only way to avoid the break is for the
library to read the clock, which B4 forbids. Every stage-1 **answer** is preserved at every valid `now`
(§9.6). The in-code grant pair and every stage-1 JSON file are unchanged.

## 4. The core — `entitlements/model.py`

Every internal type is a frozen, slotted dataclass or an enum. Each is built only inside this module, and
each owns one rule.

### 4.1 `_identifier(value, what) -> str` — unchanged (A4)

This is stage-1 §3.1 verbatim:
- it accepts any `str` instance;
- it normalizes the value with `str.__str__`;
- it rejects an empty result;
- it raises plain `ValueError`.

It now also normalizes `effect` values and every resource named in `parents`.

### 4.2 `_instant(value, what) -> datetime` — NEW, the one owner of "a supplied instant" (B3)

This is the time sibling of `_identifier`. It is used at the only two places where datetimes enter: the
constructor (window bounds) and `decide` (`now`).

- **Accepts** a `datetime` instance whose `utcoffset()` is not `None`, which is Python's own definition of
  *aware*. It **rejects** naive values, `date`, `str`, numbers and `None` with a `ValueError` that names
  `what`, for example `now must be a timezone-aware datetime, got naive 2026-09-23 12:00:00`.
- **Normalizes** the value to an **exact `datetime` in UTC** (`tzinfo=timezone.utc`, `fold=0`). It builds
  this from the offset-adjusted fields using `datetime`'s own constructor. The caller's object is never
  stored or compared. There are two correctness reasons:
  1. *Comparison by instant is structural.* Python compares two aware datetimes **that share a `tzinfo`
     object** by wall-clock time. That ignores the offset and gives the wrong order across a DST fold in a
     `zoneinfo` zone. After normalization every comparison is UTC against UTC, so "the same instant in
     different offsets behaves identically" holds by construction. Two windows written in different offsets
     for the same instants are also **equal** values, which A6 needs.
  2. *Subclass neutrality.* A `datetime` subclass cannot bring its own comparison into the rule. This is the
     same reason stage 1 normalizes `str`.
- An `OverflowError` during conversion, for example `datetime.min` with a positive offset, becomes
  `ValueError("… is out of the representable range")` (A16). It never escapes as a crash.
- It raises plain `ValueError`. Each boundary translates that once, into `InvalidModelError` in the
  constructor or `InvalidQuestionError` in `decide`.

### 4.3 `_Effect` — NEW (concept fit)

```python
class _Effect(enum.Enum):
    ALLOW = "allow"
    DENY = "deny"
```

- It is a grant's stated effect. Its by-value lookup `_Effect(value)` is the sole owner of the effect
  vocabulary.
- **It is not `Decision`.** The two share member names but not meaning. An effect is a fact that some grant
  states. A `Decision` is the answer, and `Decision.DENY` is often the absence of any fact.
- Reusing `Decision` as the effect would be the value-correct cram that design-principles §4 names, "an
  explicit deny modelled as a missing allow", one level up. It would also make it impossible to state that
  only `_combine` produces a `Decision`.

### 4.4 `_Window` — NEW, the owner of "in force at an instant" (B3, B5)

```python
@dataclass(frozen=True, slots=True)
class _Window:
    start: datetime | None      # inclusive; None = open; always an _instant result (UTC)
    end: datetime | None        # exclusive; None = open
    def __post_init__(self) -> None: ...     # both present and start >= end -> ValueError
    def contains(self, instant: datetime) -> bool:
        # (self.start is None or self.start <= instant) and (self.end is None or instant < self.end)

_ALWAYS = _Window(None, None)   # the window of a grant declared without bounds
```

- **It owns both halves of the window rule.** The invariant `from < to` lives in `__post_init__`, so an empty
  or inverted window **cannot be represented** on any path that builds one. Half-open membership lives in
  `contains`, and "in force" is written nowhere else. The check runs on the normalized values, so an offset
  cannot disguise an inverted window.
- **A grant with no window gets `_ALWAYS`, never `None`.** A window open at both ends is the genuine interval
  (−∞, +∞), and "no window" means exactly that under B3. It is not a stand-in. Every grant has a window, so no
  code branches on "has a window?".
- B5 (a window applies to allow and deny alike) holds **by construction**: the window is a field of every
  `_Grant`, and `applies` has one path for both effects.

### 4.5 `_Grant` — NEW, replaces stage-1 `_Permission`

```python
@dataclass(frozen=True, slots=True)
class _Grant:
    effect: _Effect
    action: str
    resource: str
    window: _Window
    def applies(self, action: str, lineage: frozenset[str], instant: datetime) -> bool:
        # self.action == action and self.resource in lineage and self.window.contains(instant)
```

- **Value equality over all four fields is grant identity (A6).** Exact duplicates collapse in the role's
  `frozenset`. The same `(effect, A, R)` with two windows gives two grants, and each applies in its own window.
  An allow and a deny for the same `(A, R)` are two grants, and both survive.
- **`applies` owns the scope conjunction and nothing else.** It owns the action clause itself: exact string
  equality with no implication (A4), which `_Permission` equality owned in stage 1. It delegates *reach* to the
  lineage that `_Hierarchy` produced and *in force* to `_Window.contains`. It returns `bool`, and deny and allow
  grants answer it identically. What an effect *means* is decided only in `_combine`.
- **Why `_Permission` is removed** (this supersedes stage-1 §3.2). Stage 1 kept `_Permission` because its
  equality *was* the match rule. With inheritance, a grant on `finance` matches a question about `doc-42`, so
  matching is "action equal ∧ resource ∈ lineage", not pair equality. A `_Permission` kept inside `_Grant`
  would own nothing (a lazy class). The exact-string guarantee it gave still holds, because every field is an
  `_identifier` result.

### 4.6 `_Role` — the role clause, reshaped

```python
@dataclass(frozen=True, slots=True)
class _Role:
    grants: frozenset[_Grant]
    def effects(self, action: str, lineage: frozenset[str], instant: datetime) -> frozenset[_Effect]:
        # frozenset(g.effect for g in self.grants if g.applies(action, lineage, instant))
```

- It owns "what this role says about this question": the effects of its own grants that apply. This
  supersedes stage 1's `grants(permission) -> bool`, because a role can now say two things at once (allow and
  deny), which a `bool` cannot carry.
- It must not return a per-role `Decision` (§11, decision 1b). `decide` never reads `grants`
  (Tell-Don't-Ask).
- The stage-1 reasons for `_Role` still hold: the rule is phrased over "any of U's roles", users map to
  resolved role objects, and A3 holds structurally.
- An empty role yields `∅`. It never blocks or grants anything.
- Two roles with identical grants are equal values and collapse in a user's `frozenset[_Role]`, as in stage 1.
  The union of effects is unchanged, so this cannot be observed.

### 4.7 `_Hierarchy` — NEW, owner of the tree invariants and of "reach" (B2)

```python
@dataclass(frozen=True, slots=True)
class _Hierarchy:
    parent_of: Mapping[str, str]                  # child -> its one parent; validated, frozen copy
    def __post_init__(self) -> None: ...          # copy into a MappingProxyType, then reject cycles -> ValueError
    def lineage(self, resource: str) -> frozenset[str]:
        # walk up parent_of from resource with a loop, collecting each resource met; stop at a root
```

**`lineage(R)` owns reach.** It returns R together with every ancestor of R: the set of resources whose
grants reach R. This one method covers each of the following:
- **Inheritance flows down only.** `lineage("finance")` contains no child of `finance`, so a deny on `doc-42`
  cannot affect a question about `finance`.
- **An unlisted resource is its own root.** Its lineage is `{R}`, so only its exact grants apply. This is also
  true of a group that appears only as a parent, such as `org-root`.
- **A group can be asked about directly.** It is simply a resource with its own lineage.

The fallback lives here and not in `decide`, so the whole reach rule has one home.

**`__post_init__` owns the tree invariants, on every construction path** (the same device as
`_Window`). There is no separate factory, so the dataclass-generated `__init__` is the only way in and it
always runs the check. It first replaces `parent_of` with a `MappingProxyType` over a private copy (via
`object.__setattr__`, the frozen-dataclass idiom), so the map that was checked is the map that is kept. It
then walks up from each child **with a loop, not recursion**, keeping the current path in order plus a
position index, and marking every resource it finishes as done. Each resource is finished once, so the check
is O(n) in time and memory, and a chain of any depth cannot hit Python's recursion limit.
- A walk that meets a resource on its own current path has found a **cycle**: the path from that resource
  onward. A self-parent is a cycle of length 1 and needs no separate check.
- Every distinct cycle is collected once. It is written in canonical rotation, starting at its smallest
  member: `a → b → a`, `x → x`.
- A walk that meets a resource that is already done stops there. So a resource that merely hangs off a cycle
  is not reported, because the cycle is the fault.
- If any cycle exists, `__post_init__` raises one plain `ValueError` whose message is the report, for example
  `hierarchy cycles: a → b → a, x → x`. No `_Hierarchy` with a cycle can exist, so `lineage`'s loop always
  reaches a root and terminates.

**At most one parent** is guaranteed by the seam type (§3.2). There is no code for it.

**Why the validated parent map is stored and lineage is computed per question.** Precomputing every child's
lineage costs O(n²) memory and build time on a chain (a 10 000-deep chain holds about 50M set elements);
storing the map costs O(n), and a question pays O(depth) for one walk up, which is no more than the tree
already implies. No performance requirement is stated, so the representation that is linear at build and
holds exactly the supplied facts wins. The walk needs no cycle guard of its own, because acyclicity is an
invariant of the value it walks.

The hierarchy has no cross-reference to validate. Grants and questions may name resources absent from
`parents`, and `parents` may name resources that no grant names (A14).

### 4.8 `_combine(effects) -> Decision` — NEW, the sole owner of the combining rule (B1)

```python
def _combine(effects: frozenset[_Effect]) -> Decision:
    # if _Effect.DENY in effects:  return Decision.DENY     # explicit deny overrides any allow
    # if _Effect.ALLOW in effects: return Decision.ALLOW
    # return Decision.DENY                                  # nothing applies: the stage-1 default
```

- It is the **only code in the package that produces a `Decision` value**. An AST fitness test pins this
  (§10).
- It is **total and order-free**. The input is a set, so role order, grant order and path depth cannot affect
  the result. It has exactly four inputs (∅, {ALLOW}, {DENY}, {ALLOW, DENY}), and each is tested.
- The two DENY lines are two different reasons, each named once: the first is the *explicit* case and the last
  is the *absence* case.

**Why a function and not an inline expression in `decide`.** `decide` then stays at one altitude (parse,
gather, combine). More importantly, "only `_combine` produces a `Decision`" is a checkable property. A
precedence change cannot slip into the gathering code as an early `return`.

### 4.9 `_parse_grant(raw, where) -> _Grant` — the one grant parser

It is private and sits beside `_identifier`. It is called only by the constructor.

1. If `raw` is a `Mapping`:
   - keys ⊆ `{action, resource, effect, from, to}`;
   - `action` and `resource` must be present;
   - an unknown key is rejected, naming it and the allowed keys.
2. Else, if `raw` is a non-`str` sequence of exactly two items, it is treated as
   `{"action": raw[0], "resource": raw[1]}`.
3. Anything else is rejected, including a bare `str`, a 1-tuple, a 3-tuple or a number. The message names the
   two accepted spellings.
4. Then build the grant from these values:
   - `action` and `resource` through `_identifier`;
   - `effect` (default `"allow"`) through `_identifier(…, "effect")` and then `_Effect(value)`. Anything but
     exactly `allow`/`deny` is rejected, listing both;
   - `from`/`to` (each optional) through `_instant`, then `_Window(start, end)`, or `_ALWAYS` when both are
     absent;
   - `_Grant(effect, action, resource, window)`.

### 4.10 `EntitlementModel` — immutable, consistent by construction

Representation is `__slots__ = ("_roles_of", "_hierarchy")`:
- `_roles_of: Mapping[str, frozenset[_Role]]` is unchanged in shape: a `MappingProxyType` over resolved role
  objects;
- `_hierarchy: _Hierarchy` is new.

Both are set once, in the one constructor. Immutability is as in stage 1: `__setattr__`/`__delattr__` raise
after `__init__`, and inputs are copied and never aliased.

**Constructor. The stage-1 two-phase contract is kept, and the new inputs slot into it.**

*Phase 1 — parse (stops at the first error; malformed input cannot be trusted past its first fault):*
1. `roles`, `assignments` and `parents` must each be a `Mapping`.
2. `roles`: each key goes through `_identifier(…, "role")`. Each value must be a non-`str` iterable, consumed
   once. Each item goes through `_parse_grant`. The results collect into a `frozenset[_Grant]` (A6) and become
   a `_Role`.
3. `assignments`: unchanged.
4. `parents`: each key goes through `_identifier(…, "resource")` and each value through
   `_identifier(…, "parent")`.
5. In each of the three mappings, two keys that normalize to the same string are rejected. For `parents`, this
   is also the in-code form of "two parents".

*Phase 2 — consistency (reports every violation at once; each is independent of the others):*
6. Resolve assignments to `frozenset[_Role]` and collect every `(user, undefined role)` pair (A3).
7. Build `_Hierarchy(parents)` and, if it raises `ValueError`, collect its message (the cycle report). The
   inputs are already normalized by phase 1, so the only `ValueError` it can raise is a cycle.
8. If either list is non-empty, raise **one** `InvalidModelError` that lists both, for example
   `undefined roles: alice → Editor; hierarchy cycles: a → b → a, x → x`. Otherwise freeze and store.

The stage-1 rule absorbs the new case unchanged: *malformed input reports the first problem; well-formed but
inconsistent input reports all the problems.* Every phase-1 failure carries its location, for example
`role 'freeze', grant #1: from must be before to, got [2026-10-01T00:00:00+00:00, 2026-09-01T00:00:00+00:00)`.
`ValueError` is translated with `raise … from`.

Post-condition: either a model satisfying every invariant exists, or none does. Every invariant is covered:
- no dangling role;
- no cycle;
- no empty window;
- no naive instant;
- no unknown effect.

**`decide(user, action, resource, *, now) -> Decision` — the only public member.**

1. **Parse the whole question first.** Call `_identifier` on user, action and resource, then `_instant` on
   `now`, in that order. The first bad part raises `InvalidQuestionError`, naming the part. Nothing is looked
   up before all four are valid, so `decide("nobody", "read", "x", now=naive)` raises and does not return
   DENY.
2. `lineage = self._hierarchy.lineage(resource)`, computed once per question.
3. `effects = ⋃ role.effects(action, lineage, now) for role in self._roles_of.get(user, ∅)`. `decide` owns
   only the quantifier "from **any** of U's roles", and it gathers without deciding.
4. `return _combine(effects)`.

It is a pure query: it reads only the immutable `self` and changes nothing (CQS). It is safe from any number
of threads.

**Why nothing else is public** (as in stage 1). There is no `lineage`, `roles_of`, `explain` or iteration.
Each would expose the representation and invite a second implementation of the rule outside the model. A5
rules out explanations.

### 4.11 Errors — one type per distinct handling (unchanged set)

| Type | Raised by | Handling it exists for |
|---|---|---|
| `EntitlementsError` | (base) | the CLI's single catch → exit 2 |
| `InvalidModelError` | constructor, `load_model` | the supplier fixes the model; a host keeps its current one |
| `InvalidQuestionError` | `decide` | the caller of this query has a bug |

These stage-2 failures need no new public type, because each has the same handling as an existing error:
- a cycle, an empty window, a naive bound and an unknown effect are all rejected model input, so they are
  `InvalidModelError`;
- a naive or non-`datetime` `now` is a malformed question, so it is `InvalidQuestionError`.

A cycle travels from `_Hierarchy` to the phase-2 report as a plain `ValueError` message, the same translation
pattern as `_identifier` and `_instant`. The report only needs text, so no private exception type carries
structured data.

## 5. Where each rule lives

| Rule | Sole owner | Enforced how | Reached via |
|---|---|---|---|
| **Combining: deny overrides allow; no applicable grant → deny** (B1) | `_combine` | only producer of `Decision` (fitness test); input is a set, so order-free | `decide` step 4 |
| a grant from **any** of U's roles counts; a deny from role Y beats an allow from role X | `decide` step 3 | union of effect sets; roles return effects, not decisions | host → `decide`; CLI → `load_model` → `decide` |
| what one role says about a question | `_Role.effects` | returns `frozenset[_Effect]` | `decide` |
| a grant applies iff action exact ∧ resource ∈ lineage(R) ∧ in force | `_Grant.applies` | one path for both effects (B5 by construction) | `_Role.effects` |
| action exactness, no action hierarchy (A4) | `_Grant.applies` | exact `str` equality | — |
| **reach: R's and its ancestors' grants reach R; down only; unlisted = own root** (B2) | `_Hierarchy.lineage` | iterative walk up the validated parent map, per question | `decide` step 2 |
| **tree is acyclic, no self-parent** (B2) | `_Hierarchy.__post_init__` | a cyclic `_Hierarchy` cannot be built on any path | constructor phase 2 |
| at most one parent (B2) | the `parents: Mapping[str, str]` seam type | unrepresentable; repeats caught by A7 (file) and phase-1 step 5 (code) | — |
| **in force: `from ≤ now < to`, absent bound open** (B3, B5) | `_Window.contains` | — | `_Grant.applies` |
| window non-empty (`from < to`) (B3) | `_Window.__post_init__` | an invalid `_Window` cannot be built | `_parse_grant` |
| **instant: aware only, compared by instant, UTC-normalized** (B3) | `_instant` | exact UTC `datetime` stored and compared | constructor (bounds), `decide` (`now`) |
| no window = always in force | `_ALWAYS` in `_parse_grant` | — | — |
| effect vocabulary exact; absent = allow; pair = allow always (A10) | `_Effect` lookup + `_parse_grant` | one parser for both spellings | constructor |
| grant keys (required/allowed) | `_parse_grant` | — | constructor; `load_model` reaches it through the constructor |
| identifier: non-empty `str`, exact characters (A4) | `_identifier` | unchanged | constructor, `decide` |
| grant identity / set semantics over (effect, A, R, window) (A6) | `_Grant` + `_Window` value equality | `frozenset` | constructor |
| undefined role rejected (A3) | constructor phase 2 | resolution to `_Role` | unchanged |
| parse → first error; consistency → all errors | constructor | cycles join phase 2 | `json_file` shape checks follow the parse half |
| question validated before any lookup (A2) | `decide` step 1 | — | — |
| model immutable; whole-swap; no torn read between hierarchy and grants (A1) | `EntitlementModel` | both held by one immutable object | host rebinds |
| the library never reads the clock (B4) | *absence*, enforced by fitness test | — | — |
| wall-clock default for `now` (A15) | `cli` | read once per invocation | — |
| ISO-8601 text → `datetime` (A13) | `json_file` (bounds), `cli` (`--now`) | syntax only; awareness stays with `_instant` | — |
| file syntax, shape, repeated keys (A7) | `json_file` | unchanged; now also `parents` | — |
| argv, output text, exit codes (A8) | `cli` | unchanged | — |

Each owner states only its own rule, and each foreseeable change reopens exactly one owner:

| Change | Reopens |
|---|---|
| precedence ("allow overrides") | `_combine` |
| reach (multiple parents) | `_Hierarchy` and the `parents` seam |
| validity (recurring windows) | `_Window` and its parse step |
| most-specific-wins | an ordered lineage and a wider `_combine` input, which is visible, not a local edit |

## 6. Edge — `entitlements/json_file.py` (sole owner of the file format)

```json
{
  "roles": {
    "finance-reader": [ {"action": "read", "resource": "finance"} ],
    "freeze": [ {"action": "read", "resource": "doc-42", "effect": "deny",
                 "from": "2026-09-01T00:00:00Z", "to": "2026-10-01T02:00:00+02:00"} ],
    "auditor": []
  },
  "assignments": { "alice": ["finance-reader", "freeze"], "bob": [] },
  "parents":     { "doc-42": "finance", "doc-43": "finance", "finance": "org-root" }
}
```

`load_model(path)`:
1. It reads the file as UTF-8 and parses it with the A7 duplicate-key hook. Both steps are unchanged.
2. **Top level:** `roles` and `assignments` are required, `parents` is optional, and any other key is rejected.
   A stage-1 file, which has exactly two keys, loads unchanged.
3. **Walking shape only.**
   - `roles` must be an object of arrays of objects. **The file has exactly one grant spelling, the object**;
     the in-code pair (§3.1) is not valid here, as in stage 1. A pair-shaped grant such as
     `["read", "doc-42"]` is rejected by this walking-shape check with its path, before the core sees it.
   - `assignments` must be an object of arrays.
   - `parents` must be an object. Its values are passed to the core, which checks them. An array value such as
     `"doc-42": ["finance", "hr"]` fails the core's `_identifier` with a clear message.
4. **Time text:** in each grant object, a `from`/`to` value that is a JSON string is converted with
   `datetime.fromisoformat` (which accepts `Z` in 3.11). Unparseable text becomes `InvalidModelError` with the
   path and location.
   - A **naive** result is passed through unchanged, and the core rejects it (`_instant`).
   - A non-string value (a number or `null`) is also passed through, and the core rejects it.

   So the loader cannot disagree with in-code construction about what a valid instant is.
5. It calls `EntitlementModel(roles=…, assignments=…, parents=…)`. A core `InvalidModelError` propagates with
   `add_note(f"while loading {path}")`.

**This supersedes one stage-1 loader duty.** Stage 1's loader checked that a grant object has *exactly*
`action` and `resource`. Now the core accepts grant mappings too (§3.1), and in-code mappings carry the same
typo risk, so that check moves into `_parse_grant`. Two copies of the key list would be duplicated knowledge.
The loader knows only which grant keys hold time (`from`, `to`), because JSON has no datetime type. That is
the one thing the file format adds. The stage-1 file tests (missing or extra grant field → `InvalidModelError`
with the path) still pass. The error now comes from the core, with the path note.

## 7. Edge — `entitlements/cli.py` (the imperative shell)

`python -m entitlements --model PATH [--now ISO-8601] USER ACTION RESOURCE`

- `--now` uses argparse's `type=datetime.fromisoformat`. Unparseable text is a usage error with exit 2, and
  needs no code of our own.
- When `--now` is absent, the CLI passes `datetime.now(timezone.utc)`, read **once** (A15). This is the only
  clock read in the package, and it sits in the imperative shell (B4).
- A naive `--now` is passed through. The core raises `InvalidQuestionError`, and the CLI prints one line on
  stderr and exits 2. The CLI never guesses a zone.
- `load_model(args.model).decide(args.user, args.action, args.resource, now=now)`. Output and exit codes are
  unchanged (A8). The CLI decides nothing.

## 8. Replacement and concurrency (A1)

The mechanism is unchanged, and it now covers more of the model.
- The hierarchy and the grants are fields of **one** immutable object, built by one constructor. A question
  reads only `self` for its whole duration, so it cannot pair one model's hierarchy with another model's
  grants.
- Replacement still means building a new model and rebinding one reference.
- A failed rebuild (a cycle, an empty window, a naive bound) raises before any rebind.

**Rejected: a hierarchy supplied separately from the grants.** It would make torn reads possible, and A1's
whole-model swap would then cover only half the state.

## 9. Cases traced through the design

Fixture hierarchy: `doc-42 → finance`, `doc-43 → finance`, `finance → org-root`. Its lineages are:
- L(doc-42) = {doc-42, finance, org-root}
- L(finance) = {finance, org-root}
- L(memo-7) = {memo-7} for an unlisted resource

E is the union of effects that `decide` passes to `_combine`.

### 9.1 Deny
| Case | Trace | E | Result |
|---|---|---|---|
| role X allows (A,R), role Y denies (A,R) | X gives {ALLOW}, Y gives {DENY} | {ALLOW, DENY} | DENY |
| one role both allows and denies (A,R) | two distinct `_Grant`s (the effect differs) | {ALLOW, DENY} | DENY |
| deny (write,R) + allow (read,R); ask read | the deny fails the action clause | {ALLOW} | ALLOW |
| deny (read,R1) + allow (read,R2); ask R2 | R1 ∉ L(R2) = {R2} | {ALLOW} | ALLOW |
| user holds only deny grants; one applies / none applies | — | {DENY} / ∅ | DENY (explicit) / DENY (absence) |
| role X allows, role Y has nothing relevant | Y gives ∅ (not a "deny") | {ALLOW} | ALLOW |

### 9.2 Hierarchy
| Case | Trace | E | Result |
|---|---|---|---|
| allow (read, org-root); ask doc-42 (depth 2) | org-root ∈ L(doc-42) | {ALLOW} | ALLOW |
| allow finance + deny doc-42; ask doc-42 | both ∈ L(doc-42) | {ALLOW, DENY} | DENY |
| same model; ask sibling doc-43 | doc-42 ∉ L(doc-43) | {ALLOW} | ALLOW |
| **deny org-root + allow doc-42; ask doc-42** | both apply; no level reaches `_combine` | {ALLOW, DENY} | **DENY** (a most-specific-wins design says ALLOW) |
| deny doc-42 + allow finance; ask finance | doc-42 ∉ L(finance) (down only) | {ALLOW} | ALLOW |
| grant on finance; ask unlisted memo-7 | L = {memo-7} | ∅ | DENY; an exact grant on memo-7 would allow |
| allow (read, finance); ask finance directly | finance ∈ L(finance) | {ALLOW} | ALLOW |
| parent-only root org-root asked directly | L = {org-root} | as its exact grants | — |
| `{a: b, b: a}` / `{x: x}` / `{a: b, b: c, c: a, d: a}` | `_Hierarchy.__post_init__` | — | `InvalidModelError` "a → b → a" / "x → x" / "a → b → c → a" (d not listed) |
| two parents in a file / in code | A7 repeated key / unrepresentable, and a `str`-subclass collision is rejected at phase-1 step 5 | — | `InvalidModelError` |
| a cycle and an undefined role | both in phase 2 | — | one error listing both |

### 9.3 Time (window [t0, t1))
| Case | Trace | Result |
|---|---|---|
| now = t0 / now = t1 / now < t0 | `t0 ≤ t0 ∧ t0 < t1` / `t1 < t1` false / `t0 ≤ now` false | in force / not / not |
| only `from`; only `to`; neither (`_ALWAYS`) | the absent side's conjunct is true | open-ended |
| `from == to`; `from > to` | `_Window.__post_init__` | `InvalidModelError` |
| naive `from`/`to` (code or file) | `_instant` | `InvalidModelError` with location |
| naive, `date`, `str`, `None` or `int` as `now` | `_instant` in step 1, before any lookup | `InvalidQuestionError`, even for an unknown user |
| `now` = `12:00+02:00` vs `10:00Z` at a window edge | both normalize to 10:00 UTC | identical answers |
| an expired deny (now ≥ its `to`) + a permanent allow | the deny fails `contains` | {ALLOW} → ALLOW |
| a not-yet-valid allow only (now < its `from`) | fails `contains` | ∅ → DENY |

### 9.4 Interactions (each new axis crossed with each rule)
| Case | Result |
|---|---|
| deny (read, finance) in [t0,t1) + permanent allow (read, doc-42); ask doc-42 at t0 ≤ t < t1 / at t < t0 or t ≥ t1 | DENY / ALLOW |
| same (allow, A, R) with windows [t0,t1) and [t2,t3) | ALLOW inside either window, DENY in the gap |
| adjacent windows [t0,t1) and [t1,t2), at t1 | ALLOW (the second window applies) |
| exact duplicate grant, including the same instants written in different offsets | one `frozenset` element, so the same answers as once |
| an allow and a deny with the same (A, R, window) | two grants, so DENY; collapsing them would lose the deny (A6 is over whole grants) |
| deny (write, org-root); ask (read, doc-42) with allow (read, finance) | ALLOW (the deny fails on the action) |
| `Finance` vs `finance` in `parents` | distinct groups (A4), no inheritance across them |
| `StrEnum` members as `parents` keys or values, or as the effect | behave as their plain strings |
| unknown user × any new feature | no roles, E = ∅, DENY: the stage-1 path |
| deny from a role the user does not hold | no effect |

### 9.5 The combining rule, exhaustively
| effects | ∅ | {ALLOW} | {DENY} | {ALLOW, DENY} |
|---|---|---|---|---|
| `_combine` | DENY | ALLOW | DENY | DENY |

### 9.6 Stage-1 preservation — a proof, not a sample

Take a model with no deny, no `parents` and no window.
- Every grant is `_Grant(ALLOW, a, r, _ALWAYS)`.
- L(R) = {R} for every R, so `resource ∈ L(R)` ⇔ `resource == R`, which is stage-1 `_Permission` equality.
- `_ALWAYS.contains(t)` is true for every aware `t`.

So E = {ALLOW} exactly when some role of U holds (A, R), and E = ∅ otherwise. `_combine` then returns ALLOW or
DENY respectively, which is stage 1's `any(role.grants(p))`.

Every row of the stage-1 case table and every stage-1 test therefore answers identically at **every** aware
`now`. The in-code pair form and every stage-1 JSON file are accepted unchanged. The only visible change is
the required `now=` keyword (§3.2).

## 10. Test plan (test-first; behavior through the constructor, `decide`, `load_model`, `main` only; stdlib `unittest`)

- **Characterization first.** The whole stage-1 suite is written and green against stage 1 before any change.
  It is then kept, with `now=T` as its only edit.
  - A parametrized wrapper runs the stage-1 grant-rule suite at several `now` values (far past, `T`, far
    future, and a non-UTC offset) and asserts identical answers.
  - The pair form and `{"action", "resource"}` give identical decisions over a question grid.
  - An explicit `"effect": "allow"` equals an absent effect.
- **Combining rule:**
  - the four rows of §9.5, each realized three ways: both effects from one role, from two roles, and from two
    levels of the path;
  - reversed role and grant declaration order gives the same answers.
- **Deny:** every row of §9.1.
- **Hierarchy:**
  - every row of §9.2;
  - depth 3, and a deny at each level of a depth-3 path × an allow at each level → DENY for all 9 pairs
    (this pins "no most-specific-wins" in general);
  - a leaf with no grants anywhere → DENY;
  - omitting `parents` equals passing `{}`;
  - a non-mapping `parents`, or non-string parent values → `InvalidModelError`;
  - a malformed parent id and a cycle in one model → the parse error is reported (parse before consistency);
  - **deep chain:** a 10 000-deep chain (ten times the default recursion limit) builds without
    `RecursionError`, and its leaf inherits an allow and a deny granted on the root; a 10 000-member cycle is
    rejected as one cycle.
- **Time:**
  - every row of §9.3;
  - boundaries at t0−1µs, t0, t1−1µs and t1;
  - a `datetime` subclass as `now` behaves like its plain value;
  - a `tzinfo` whose `utcoffset` returns `None` is rejected;
  - `datetime.min`/`max` with an offset → a clean error, not a crash;
  - a DST-fold instant in `zoneinfo("Europe/Berlin")` at a window edge answers by instant;
  - calling `decide` without `now` → `TypeError` (the signature contract).
- **Interactions:** every row of §9.4.
- **Grant declarations:**
  - an absent effect → allow;
  - `"Deny"`, `""` or `5` as the effect → an error listing the allowed values;
  - an unknown key (`"efect"`, `"until"`) → an error;
  - a missing `action` or `resource` → an error;
  - a `None` bound → an error;
  - a bare `str`, 1-tuple or 3-tuple → an error naming both spellings;
  - a two-key dict is parsed as a mapping, never unpacked as a pair;
  - a malformed window and a cycle in one model → the window error is reported.
- **Immutability and surface:**
  - mutating the caller's `parents`, grant mappings or lists after construction changes nothing;
  - setting or deleting attributes → `AttributeError`;
  - the public surface of `EntitlementModel` is exactly `{decide}`;
  - `__all__` is unchanged;
  - `Decision` has exactly two members.
- **Replacement and concurrency.** The stage-1 threaded stress test is extended: it rebinds between two models
  that differ in *both* hierarchy and grants. The models are chosen so that one model's hierarchy combined with
  the other model's grants gives an answer neither model gives. This is a regression guard; the guarantee
  itself is structural.
- **File edge:**
  - the §6 example answers as traced;
  - every stage-1 fixture file loads and answers identically;
  - each of these is rejected with the path: bad ISO text, a `null` bound, a numeric bound, an unknown grant
    key, a non-object `parents`, an array parent value, a repeated `parents` key, and a pair-shaped grant
    `["read", "doc-42"]` (the file's one grant spelling is the object);
  - a naive ISO bound is rejected by the core, with the same message as in code plus the path note;
  - the same model built in code and from the file answers identically over a question × `now` grid.
- **CLI:**
  - `--now` inside and outside a window flips `deny`/1 ↔ `allow`/0;
  - a naive `--now` → stderr, exit 2, no traceback;
  - garbage `--now` → usage error, exit 2;
  - without `--now`, a model whose deny window spans the present by ±1 day → `deny`/1. This exercises the
    wall-clock default without a clock fake;
  - `python -m entitlements` via subprocess.
- **Architecture fitness** (an AST scan of `model.py`):
  - every `Import`/`ImportFrom` names a module on the allow-list (§2); this is what excludes `time`;
  - no `ast.Attribute` node has `attr` in `{now, utcnow, today}` (this catches `datetime.now(…)`,
    `datetime.datetime.today()`, `date.today()` under any alias). The `now` parameter and its uses are
    `ast.arg`/`ast.Name` nodes, so correct code passes;
  - **no `ast.Attribute` of the form `Decision.ALLOW` / `Decision.DENY` (an `ast.Name` `Decision` with that
    `attr`) occurs outside the body of `_combine`, and no `Decision(…)` call occurs anywhere** (a by-value
    lookup would be a second producer). The enum's own class body defines its members as `ast.Name`
    assignment targets, not attribute references, so it is not matched;
  - `import entitlements` does not load `json`.

## 11. Key decisions and the alternatives rejected

1. **Precedence is one pure function over the set of applicable effects.** The alternatives were rejected for
   these reasons:
   - **(a) `decide` loops and returns early on the first deny or allow.** Precedence would then live in the
     control flow, and an early `return ALLOW` would be one edit away.
   - **(b) Each role returns a `Decision`, and those are combined.** This is *wrong*, not merely inelegant. A
     role with no applicable grant would report DENY, which cannot be told apart from an explicit deny, so
     "X allows, Y has nothing" would come out DENY. This is why clauses return effects.
   - **(c) Walk the path and let the most specific grant win.** This contradicts B1, as the org-root deny case
     shows.
   - **(d) Precompute effective effects per user and resource at build time.** Time makes this impossible
     without a per-instant table, and it would fold three owners into the constructor.
2. **Deny is a first-class `_Effect` on the grant, distinct from `Decision`.** The alternatives were rejected
   for these reasons:
   - *Parallel `allows`/`denies` collections:* there would be two applicability paths, and either could forget
     the window or the hierarchy.
   - *Reusing `Decision`:* the absence-deny and the explicit deny would share one value.
   - *A `deny: bool`:* allow would become the negation of deny.
3. **The hierarchy is a child → parent map owned by `_Hierarchy`, reach is a lineage set, and both live
   inside the model.** The alternatives were rejected for these reasons:
   - *Group → member lists:* two parents would become representable and need a guard.
   - *Precomputing every lineage at build time:* O(n²) on a chain, for no stated need (§4.7). Walking the
     parents per question is chosen instead; it needs no cycle safety of its own, because `_Hierarchy`
     cannot hold a cycle.
   - *Expanding grants down to descendants at build time:* this destroys grant identity (A6) and mixes reach
     into parsing.
   - *An ordered path:* B1 makes the order meaningless.
   - *A separately supplied hierarchy:* this allows torn reads.
4. **"Now" is a required, keyword-only, aware `datetime`, normalized once by `_instant`.** The alternatives
   were rejected for these reasons:
   - *A `Clock` port:* the core would read time and risk two instants per decision.
   - *An optional `now` with a clock default:* B4 forbids it.
   - *Treating naive values as UTC:* B3 forbids it.
   - *An epoch float:* awareness could not be checked.
   - *Keeping the caller's offset:* set semantics and subclass safety would then depend on the caller's
     objects, and comparisons that share a `tzinfo` are wrong across a DST fold.
5. **The grant seam uses the stage-1 pair plus a mapping with the file's key names, and adds no new public
   type** (a decided conflict, see decisions/0003).
   - *A public `Grant` dataclass:* it would be either a second validation owner or a bag the constructor
     validates anyway, and the file edge would have to translate `"deny"` into an enum.
   - *A mapping only, dropping the pair:* it breaks every stage-1 host model for no gain.
6. **`_Permission` is removed; `_Role.grants(p)` becomes `_Role.effects(a, lineage, t)`.** Both are recorded
   as supersessions of stage 1, not left as dead code.
7. **The core stays one module** (§2), with a stated falsifier.
8. **`_Question` is not built.** It would be a validated-question value carrying (action, lineage, instant).
   Validation before lookup is already the fixed first step of `decide`. The three values have distinct types
   and make two hops, and nothing else consumes them together. Fold-in falsifier: a fourth question attribute,
   or a second consumer.

## 12. Assumptions (A1–A6 and B1–B5 are in `goals.md`)

**Carried from stage 1:**
- **A7 — a repeated key in the model file is rejected**, at every level. This now includes `parents`, where a
  repeated key is how "two parents" would appear. Two in-code keys that normalize to the same string are
  rejected for the same reason.
- **A8 — CLI exit codes:** 0 allow, 1 deny, 2 error.
- **A9 — whitespace is significant** in identifiers.

**Added by this stage:**
- **A10 — defaults and effect vocabulary.** A grant declared without an effect is an allow, and the stage-1
  pair is an allow with no window. This keeps every stage-1 declaration valid and meaning what it meant. The
  effect vocabulary is exactly `allow`/`deny`, and it is case-sensitive.
- **A11 — wire names are `effect`, `from`, `to` and `parents`.** These are the product's own words: "[from,
  to)" and "belong to a group". The in-code mapping uses the same names.
- **A12 — an open bound is written by omitting the key.** `null`/`None` is rejected, so there is one spelling
  per meaning. This could be relaxed in `_parse_grant` alone.
- **A13 — times in text are ISO 8601, as `datetime.fromisoformat` (3.11) accepts them, including `Z`.** This
  applies to both the file and `--now`. A naive timestamp is an error. It is never assumed to be local time or
  UTC.
- **A14 — a parent group needs no declaration of its own.** Resources stay opaque (A4). A name that appears
  only as a parent is a root. The hierarchy is not validated against grants, and it is not time-bounded.
- **A15 — the CLI's default `now` is the wall clock in UTC, read once per invocation.**
- **A16 — an instant that cannot be represented in UTC** (overflow at `datetime.min`/`max`) is rejected as
  malformed.
- **A17 — `decide` gains a required, keyword-only `now`.** A stage-1 three-argument call raises `TypeError`.
  Every stage-1 answer is preserved.
- **Cycle reporting:** each cycle is reported once, in canonical rotation, together with any undefined-role
  pairs. Resources that merely hang off a cycle are not listed.

## 13. Superseded from stage 1 (decisions/0002, the stage-1 text of this file)

1. `_Permission` is removed. `_Grant` owns grant identity (A6 over effect, action, resource and window), and
   `_Grant.applies` owns matching.
2. `_Role.grants(permission) -> bool` becomes `_Role.effects(action, lineage, instant) -> frozenset[_Effect]`.
3. "Deny is the absence of any grant; there is no deny machinery" (stage-1 §3.4) is superseded. An explicit
   deny is now a first-class effect, and the absence of any applicable grant is still the default deny.
4. The grant rule's single owner, `decide`, is split into three owners along the stage-2 rule's own structure:
   - `decide` owns the quantifier over roles;
   - `_combine` owns precedence;
   - `_Grant.applies` owns scope.
5. `decide` gains the required keyword `now`.
6. Grant-key validation moves from `json_file` into the core (`_parse_grant`).
7. The stage-1 non-goals "explicit deny rules, hierarchies" are now built.

Everything else in stage 1 stands, including:
- strings at the seam and `_identifier` normalization;
- one immutable model built by one constructor, with two-phase errors;
- whole-swap replacement with no holder;
- the JSON and CLI edges;
- the error set.

## 14. Deliberately not built

Each item lacks a present force:
- public `Grant`, `Effect`, `Window`, `Lineage` or `Question` types, and `_Question`;
- a `Clock` port, and a library-side default for `now`;
- ordered paths, depth or specificity precedence, and priorities;
- per-role verdicts;
- a separate deny table;
- group → member lists, multiple parents or a DAG;
- time-bounded roles, assignments or hierarchy, and recurring windows;
- an action hierarchy, wildcards, role inheritance and conditions;
- `null` window bounds, and naive-to-UTC defaulting;
- a resource registry, or validating the hierarchy against grants;
- precomputed effective permissions, caching, a holder or reload service, logging and explanations (A5);
- a `_time.py`/`_hierarchy.py` split;
- any third-party dependency (`dateutil`, `pytz`, test libraries).
