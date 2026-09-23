---
title: "Stage 2 — deny, resource inheritance, time-bounded grants (clean-code worker)"
date: 2026-09-23
axis: clean-code (fewest moving parts, no smells, lean dependencies)
builds on: DESIGN.md (stage 1), decisions/0002
result: met
---

# Stage 2 design — clean-code axis

## 0. Summary

The stage-1 shape survives unchanged: one immutable `EntitlementModel`, one keyword-only constructor, one
public query, strings (and now aware datetimes) at the seam, JSON and CLI as thin edges. The reopen lands where
0002 said it would, and **nowhere else**:

- `decide` keeps ownership of the decision and now states the **combining rule** in three lines
  (deny if any applicable deny; else allow if any applicable allow; else deny).
- The role clause (`_Role`) changes from "is p one of my grants" to "which effects do my applicable grants
  carry".
- Three clauses each get one owner: **reach** (`_Hierarchy.lineage`), **in force** (`_Window.contains`),
  **match** (`_Grant.applies`, which composes the other two with an exact action test).
- The deny effect is first-class: `_Effect.DENY` is a value that a grant carries. It is not the absence of an
  allow.

The key simplification: B1 makes deny win **anywhere on the path**, so specificity never decides anything.
The ancestor path is therefore a **set** (the lineage), not an ordered walk. There is no "nearest grant",
no depth comparison and no ordering code. The rule is order-free, so the representation is order-free too.

Net change in moving parts: **+4 private types** (`_Effect`, `_Window`, `_Grant`, `_Hierarchy`) and **+1 private
function** (`_instant`). **−1 private type** (`_Permission`, superseded; §9). The public surface grows by one
parameter on `decide` and one optional parameter on the constructor. The core gains **one stdlib import
(`datetime`)**. There are zero new dependencies, including for tests.

## 1. Module skeleton

```
entitlements/                 Python 3.11+, stdlib only, no runtime or test dependencies
├── __init__.py   re-exports Decision, EntitlementModel, the three errors (unchanged set)
├── model.py      CORE  _identifier, _instant, _Effect, _Window, _Grant, _Role, _Hierarchy,
│                       Decision, EntitlementModel, errors
├── json_file.py  EDGE  load_model(path): file read, JSON, A7, top-level keys, ISO-8601 → datetime
├── cli.py        EDGE  main(argv): argv, --now (default: wall clock), output, exit codes
└── __main__.py   EDGE  unchanged
tests/            stdlib unittest
```

Dependencies are unchanged: `__main__ → cli → json_file → model`, `cli → model`. The core's allowed imports
become `dataclasses`, `enum`, `types`, `collections.abc` and **`datetime`**. `datetime` is used for
`isinstance`, `timezone.utc` and comparison. The core never calls a clock (B4). A fitness test guards this (§10).

**Why the core stays one module.** Every new part (effect, window, grant, hierarchy) changes for the same reason
as the old ones: a change in the entitlement rules. Every part is private, and each is used only by the
constructor and `decide`. Splitting out `hierarchy.py` or `time.py` would make those modules import `_identifier`
and the error types across a module seam. A private name would cross modules (§0 of the principles), and a
future rule change would touch several files (shotgun surgery). The core grows from about 100 to about 220 lines.
That is still one reader's sitting and has one reason to change. **Falsifier:** split the day a part gains its own
change source, for example a hierarchy supplied by a separate system on its own schedule.

## 2. Public API (everything that crosses a seam)

```python
# entitlements (re-exported from entitlements.model)
class Decision(enum.Enum):          # unchanged — A5
    ALLOW = "allow"
    DENY = "deny"

GrantDecl = Mapping[str, object]
#   {"action": str, "resource": str,            required
#    "effect": "allow" | "deny",                optional, default "allow"
#    "from": datetime, "to": datetime}          optional each; tz-aware; window [from, to)

class EntitlementModel:
    def __init__(
        self,
        *,
        roles: Mapping[str, Iterable[GrantDecl]],        # role -> its grants
        assignments: Mapping[str, Iterable[str]],        # user -> its roles          (unchanged)
        parents: Mapping[str, str] = EMPTY,              # resource -> its parent group (NEW, optional)
    ) -> None: ...                                        # raises InvalidModelError
    def decide(self, user: str, action: str, resource: str, *, now: datetime) -> Decision: ...
                                                          # raises InvalidQuestionError

class EntitlementsError(Exception): ...                   # unchanged
class InvalidModelError(EntitlementsError, ValueError): ...
class InvalidQuestionError(EntitlementsError, ValueError): ...

# entitlements.json_file
def load_model(path: str | os.PathLike[str]) -> EntitlementModel: ...   # unchanged signature

# entitlements.cli
def main(argv: Sequence[str] | None = None) -> int: ...   # unchanged signature; 0 allow · 1 deny · 2 error
```

`GrantDecl` is a documentation alias only. It is not a published class (§9).

Host use:

```python
t = datetime(2026, 9, 23, 12, tzinfo=timezone.utc)
model = EntitlementModel(
    roles={
        "reader":  [{"action": "read", "resource": "finance"}],
        "freeze":  [{"action": "read", "resource": "doc-42", "effect": "deny",
                     "to": datetime(2026, 10, 1, tzinfo=timezone.utc)}],
    },
    assignments={"alice": ["reader", "freeze"]},
    parents={"doc-42": "finance", "doc-43": "finance", "finance": "org-root"},
)
model.decide("alice", "read", "doc-43", now=t)   # ALLOW (inherited from finance)
model.decide("alice", "read", "doc-42", now=t)   # DENY  (in-force deny on the leaf)
```

### 2.1 Seam calibration (changes only)

| Seam | Floor (consumer) | Ceiling (producers) | Type |
|---|---|---|---|
| Question in | the rule needs a point in time | host clocks, CLI argv, all yield an aware `datetime` | `now: datetime`, **keyword-only, required** |
| Grant in | effect, action, resource, optional bounds | host dicts, JSON objects | a `Mapping` with **named** keys (the same names as the file) |
| Hierarchy in | each resource's single parent | host dict, JSON object | `Mapping[str, str]`. The mapping's key uniqueness *is* the one-parent rule. |

**`now` is keyword-only.** `decide("alice", "read", "doc-42", now=t)` reads as the question. A fourth positional
datetime would be position-coupled and anonymous. It is **required** (B4). A default would make the library read
a clock, which is the one thing it must not do.

**Grants become named mappings; the stage-1 `(action, resource)` tuple is superseded.** A grant now has five
fields, three of them optional. A tuple would be positional connascence with optional holes (`("deny", "read",
"doc-42", None, t1)`), and a named mapping is the weakest connascence that works. Accepting *both* shapes would
mean two parsers for one concept. That is accretion, not absorption. The migration is mechanical, and the question
seam breaks anyway (`now` is new), so there is exactly one break for hosts, not two. The file format needs no
migration: it already used named objects, and the new keys are optional (§5).

**Why `parents` and not `groups: {group: [members]}`.** In `resource → parent` form, "at most one parent" cannot be
represented: a `Mapping` has one value per key, and a repeated key in the file is already rejected by A7. The
member-list form makes "two parents" representable, so it would need its own check and its own error. The
parent-map removes that case without writing any code (see §4 for B2's two-parents case).

## 3. The core: internal model (`entitlements/model.py`)

```python
def _identifier(value: object, what: str) -> str          # unchanged (stage-1 §3.1)
def _instant(value: object, what: str) -> datetime        # NEW

class _Effect(enum.Enum):                                  # NEW — first-class effect
    ALLOW = "allow"
    DENY = "deny"

@dataclass(frozen=True, slots=True)
class _Window:                                             # NEW — owns "in force at an instant"
    start: datetime | None
    end: datetime | None
    def __post_init__(self) -> None: ...                   # start >= end → ValueError
    def contains(self, now: datetime) -> bool:
        # (start is None or start <= now) and (end is None or now < end)

@dataclass(frozen=True, slots=True)
class _Grant:                                              # NEW — supersedes _Permission
    effect: _Effect
    action: str
    resource: str
    window: _Window
    def applies(self, action: str, lineage: frozenset[str], now: datetime) -> bool:
        # self.action == action and self.resource in lineage and self.window.contains(now)

@dataclass(frozen=True, slots=True)
class _Role:
    grants: frozenset[_Grant]
    def effects(self, action: str, lineage: frozenset[str], now: datetime) -> frozenset[_Effect]:
        # {g.effect for g in self.grants if g.applies(action, lineage, now)}

@dataclass(frozen=True, slots=True)
class _Hierarchy:                                          # NEW — owns the tree and "reach"
    _lineage_of: Mapping[str, frozenset[str]]              # resource -> itself ∪ its ancestors
    @classmethod
    def of(cls, parents: Mapping[str, str]) -> "_Hierarchy": ...   # tree check; ValueError listing all cycles
    def lineage(self, resource: str) -> frozenset[str]:
        # self._lineage_of.get(resource, frozenset({resource}))

class EntitlementModel:
    __slots__ = ("_roles_of", "_hierarchy")                # both set once, in one constructor
```

### 3.1 `_instant`: the one owner of "a point in time" (B3)

- It accepts a `datetime` instance that is **aware** (`value.utcoffset() is not None`, Python's own definition).
  It rejects naive datetimes, `date`, strings, numbers and `None` with `ValueError`, and the message names `what`
  (`"now must be a timezone-aware datetime, got naive 2026-09-23 12:00:00"`).
- It returns the value **converted to UTC** as an exact `datetime`. This is the time counterpart of
  `_identifier`'s normalization. Every stored and compared instant is the same kind of object, so comparison is
  by instant (which Python already guarantees for aware values). A `datetime` subclass cannot bring its own
  comparison into the rule. The conversion changes no instant, so "same instant, different offsets behaves
  identically" holds by construction.
- Like `_identifier`, it raises plain `ValueError`. The two boundaries (constructor, `decide`) translate it once.

### 3.2 `_Window`: absent bounds are open, not a special case

A grant with no window gets `_Window(None, None)`, which is the genuine interval (−∞, +∞) and contains every
instant. This is not a stand-in: B3 makes each bound independently optional, so "no window" is exactly "both
bounds absent". The alternative, `window: _Window | None`, would add a `None` branch in `_Grant.applies` and a
second representation of "always in force". `__post_init__` rejects `start >= end`, so an empty window cannot be
represented.

### 3.3 `_Grant`: the unit of grant, and the match clause

This is a value (A6: equal iff effect, action, resource and window are all equal). `applies` is the **match
clause**, and it is a conjunction of three owned tests:
- action: exact equality (A4: no action hierarchy). `_Grant` owns this itself.
- reach: `self.resource in lineage`. `_Grant` owns only the membership test. What the lineage contains is
  `_Hierarchy`'s decision.
- in force: delegated to `self.window.contains(now)`.

It says nothing about precedence. A deny grant and an allow grant answer `applies` identically. What the effect
*means* is decided in exactly one place (`decide`).

### 3.4 `_Role`: the role clause, reshaped

A role reports the set of effects carried by its applicable grants. It does not resolve them; resolving
across roles is `decide`'s job, and B1 says an allow in role X and a deny in role Y combine exactly like both in
one role. `decide` never reads `grants` (Tell-Don't-Ask, as in stage 1). An empty role yields `∅` and never
blocks or grants anything.

### 3.5 `_Hierarchy`: owner of the tree invariants and of "reach" (B2)

- **Built by `_Hierarchy.of(parents)`**, which the model constructor calls after `_identifier` has normalized
  every key and value. For each child it walks the parent chain and collects `{child, parent, grandparent, …}`.
  If a walk meets its start, that resource is on a cycle. A self-parent is a cycle of length 1, so it needs no
  separate check. Every resource on a cycle is collected, and one `ValueError` lists them all. This is the
  stage-1 phase-2 rule: well-formed but inconsistent means report everything.
- **Two parents** cannot be represented (§2.1). There is no code for it.
- **`lineage(resource)`** returns the resource and all its ancestors. A resource never named as a child, whether
  unlisted or a root named only as a parent, gets `{resource}`: "its own root: only exact grants apply". The
  default lives here and not in `decide`, so the whole "whose grants reach R" rule has one home.
- Inheritance flows down only, by construction: the lineage of `finance` does not contain `doc-42`.
- Lineages are precomputed at build time because the walk is also the cycle check. Doing it once gives the
  invariant and the query from the same traversal. Nothing about precedence depends on this; it is not a
  performance claim.

### 3.6 `EntitlementModel`: constructor

The two-phase contract from stage 1 is unchanged; the new rows are marked.

*Phase 1: parse (stop at the first error).*
1. Each argument must be a `Mapping` (now three).
2. `roles`: each key through `_identifier(…, "role")`; each value a non-`str` iterable of grant declarations.
   Each declaration goes through **`_grant(raw) -> _Grant`** (a private module function beside `_identifier`):
   - must be a `Mapping`;
   - keys ⊆ `{action, resource, effect, from, to}`, and `action` and `resource` must be present. **An unknown key
     is rejected.** A typo such as `"efect": "deny"` would otherwise load as an *allow*, a silent inversion of
     intent. The core now owns this check for in-code and file input alike (§5).
   - `action`, `resource` through `_identifier`;
   - `effect` (default `"allow"`) through `_identifier(…, "effect")`, then `_Effect(value)`. Anything but exactly
     `"allow"` or `"deny"` is rejected with the allowed values in the message;
   - `from` and `to` (each optional) through `_instant`, then `_Window(start, end)`, whose `__post_init__`
     rejects `from >= to`.
   The grants are collected into a `frozenset[_Grant]` (A6) and wrapped in a `_Role`.
3. `assignments`: unchanged.
4. **`parents`: each key through `_identifier(…, "resource")`, each value through
   `_identifier(…, "parent")`.**
5. Normalized-key collisions are rejected in all three mappings. This is unchanged in kind and now also covers
   `parents`. Here it is also the in-code form of "two parents".

*Phase 2: consistency (report everything).*
6. Resolve assignments to `frozenset[_Role]` (unchanged, A3: all undefined pairs in one error).
7. **`_Hierarchy.of(parents)`: all cycle members in one error.** If both 6 and 7 fail, phase 2 reports both in
   one `InvalidModelError`. Both are independent consistency findings, and the stage-1 rule is to report all of
   them.
8. Freeze: `MappingProxyType`, frozensets, frozen dataclasses. Caller containers are never aliased.

Every `ValueError` is translated once into `InvalidModelError` with its location
(`role 'freeze', grant #1: from must be before to, got [2026-10-01T00:00:00+00:00, 2026-09-01T…)`).

### 3.7 `decide`: the only public member, and the only owner of precedence

```python
def decide(self, user, action, resource, *, now):
    u, a, r, t = <parse all four>                 # _identifier ×3, _instant; ValueError → InvalidQuestionError
    lineage = self._hierarchy.lineage(r)
    effects = frozenset().union(*(role.effects(a, lineage, t) for role in self._roles_of.get(u, ())))
    if _Effect.DENY in effects:
        return Decision.DENY                      # explicit deny overrides any allow (B1)
    if _Effect.ALLOW in effects:
        return Decision.ALLOW
    return Decision.DENY                          # default deny: nothing applies (stage-1 rule)
```

The two ways to reach `Decision.DENY` are two different lines with two different reasons. That is concept fit
made visible: an explicit deny is a found fact, and a default deny is the absence of any fact. All four parts
are parsed before any lookup, so `decide("nobody", "read", "x", now=naive)` raises and does not return DENY
(the stage-1 ordering rule, extended to `now`).

It is a pure query over one immutable object, so it has no torn read between hierarchy and grants (§6).

## 4. Where each rule lives

| Rule | Sole owner | Reached via |
|---|---|---|
| **Combining: deny overrides allow; otherwise allow if any; otherwise deny** (B1) | `EntitlementModel.decide` | host → `decide`; CLI → `load_model` → `decide` |
| a role contributes the effects of its applicable grants; roles have no precedence among themselves | `_Role.effects` | only from `decide` |
| a grant applies iff exact action ∧ its resource reaches R ∧ in force | `_Grant.applies` | only from `_Role.effects` |
| **reach: grants on R and on each ancestor of R, and no others; an unlisted resource is its own root; downward only** (B2) | `_Hierarchy.lineage` | only from `decide` (a single call per question) |
| **tree: no cycle, no self-parent** (B2) | `_Hierarchy.of` | constructor phase 2 |
| tree: at most one parent | representation (`Mapping` key uniqueness) + A7 in `json_file` + normalized-key rule in the constructor | no code of its own |
| **in force: `from <= now < to`, absent bound open** (B3, B5 for both effects) | `_Window.contains` | only from `_Grant.applies` |
| **window non-empty (`from < to`)** | `_Window.__post_init__` | constructor via `_grant` |
| **instant = tz-aware datetime, compared by instant; naive rejected** (B3) | `_instant` | constructor (`from`/`to`) and `decide` (`now`), the only two entries |
| **effect is exactly `allow` or `deny`; absent = `allow`** | `_grant` | constructor only |
| **grant declaration keys (required and allowed)** | `_grant` | constructor; `load_model` reaches it through the constructor |
| identifier rule (A4) | `_identifier` | unchanged |
| malformed question → error before lookup (A2) | `decide` parse step | — |
| undefined role rejected (A3) | constructor phase 2 | unchanged |
| set semantics over whole grants (A6) | `frozenset[_Grant]` + `_Grant` value equality | — |
| immutable model; whole-swap replacement; no torn read (A1) | `EntitlementModel` | host rebinds |
| file syntax, duplicate keys (A7), top-level keys, ISO-8601 text → `datetime` | `json_file` | — |
| wall-clock default for `now`; argv; exit codes (A8) | `cli` | — |
| library never reads the clock (B4) | nobody calls one; fitness test | — |

Each row states one rule and names one owner. The three clauses feeding the decision (reach, in force, match)
are separate rows with separate owners. Changing reach (say, to DAG inheritance) reopens only `_Hierarchy`.
Changing time semantics (say, closed windows) reopens only `_Window`. Changing precedence (say, most-specific-wins)
reopens only `decide`, plus a lineage that keeps its order. No change reopens two of them.

## 5. JSON file format

```json
{
  "roles": {
    "reader": [ {"action": "read", "resource": "finance"} ],
    "freeze": [ {"action": "read", "resource": "doc-42", "effect": "deny",
                 "from": "2026-09-01T00:00:00Z", "to": "2026-10-01T00:00:00+02:00"} ],
    "auditor": []
  },
  "assignments": { "alice": ["reader", "freeze"], "bob": [] },
  "parents":     { "doc-42": "finance", "doc-43": "finance", "finance": "org-root" }
}
```

- **Every stage-1 file loads unchanged and answers identically.** `parents` is optional at the top level;
  `effect`, `from` and `to` are optional in a grant.
- Top-level keys: `roles` and `assignments` are required, `parents` is optional, and any other key is rejected
  (stage-1 typo guard, extended by one name).
- `from`/`to` are ISO-8601 strings, which the loader converts with `datetime.fromisoformat` (3.11 accepts `Z`).
  That conversion is the only thing the file format adds, because JSON has no datetime type. A string that does
  not parse → `InvalidModelError` with path and location. A **naive** timestamp such as
  `"2026-09-01T00:00:00"` parses fine and is passed through, and the **core** rejects it. There is one owner of
  "aware" (`_instant`), and the loader cannot disagree with in-code construction.
- `parents`: a JSON object of string → string. Two parents for one resource means a repeated key, which is
  already rejected (A7).

**Supersedes a stage-1 loader duty.** Stage 1's loader checked that a grant object has *exactly* `action` and
`resource`. That check moves into the core (`_grant`), because in-code mappings carry the same typo risk. Two
copies of the key list would be a real duplication of knowledge. The loader now checks only the shape it needs in
order to *walk* the file (an object of arrays of objects under `roles`, an object under `parents`), and converts
`from`/`to` where present. The stage-1 file tests (missing/extra grant field → `InvalidModelError` with path)
still pass: the error now comes from the core, with the `while loading {path}` note.

## 6. CLI changes

`python -m entitlements --model PATH [--now ISO-8601] USER ACTION RESOURCE`

- `--now` is parsed with `argparse` `type=datetime.fromisoformat`. An unparsable value produces an argparse usage
  error and exit 2, with no code of our own.
- If it is absent, `now = datetime.now(timezone.utc)`, read **once**, in the shell (B4: the imperative shell owns
  the clock). The flag uses the same word as the library parameter (one word per concept).
- A naive `--now 2026-09-23T12:00` reaches `decide` and raises `InvalidQuestionError`, which exits 2 with the
  core's message. The CLI does not duplicate the awareness rule.
- Output, exit codes and error handling are unchanged (A8).

## 7. Replacement and concurrency

This is unchanged in mechanism and extended in scope. Hierarchy and grants are fields of the same immutable
object, built by the same constructor, so a question reads one model's hierarchy together with the same model's
grants for its whole duration. No torn read is possible between them. Replacement is still: build a new model and
rebind one reference. A failed build (for example, a cycle) raises before any rebind.

## 8. Adversarial cases traced

Notation: L(R) = `lineage(R)`, E = the effect set gathered in `decide`.

**Deny**

| Case | Trace | Result |
|---|---|---|
| role X allows (A,R), role Y denies (A,R) | X gives {ALLOW}, Y gives {DENY}; E={ALLOW,DENY}; DENY line first | DENY |
| same role allows and denies (A,R) | two distinct `_Grant`s (effect differs); E={ALLOW,DENY} | DENY |
| deny (write,R), allow (read,R), ask read | deny grant fails action equality; E={ALLOW} | ALLOW |
| deny on R1, allow on R2, ask R2 | R1 ∉ L(R2)={R2}; E={ALLOW} | ALLOW |
| user holds only deny grants | E ⊆ {DENY} | DENY via the **explicit** line if one applies, else via the default line |

**Hierarchy** (parents: doc-42→finance, doc-43→finance, finance→org-root)

| Case | Trace | Result |
|---|---|---|
| allow (read, org-root), ask doc-42 | L(doc-42)={doc-42, finance, org-root} ∋ org-root | ALLOW (depth 2) |
| allow finance + deny doc-42; ask doc-42 / doc-43 | doc-42: E={ALLOW,DENY}; doc-43: L={doc-43,finance,org-root}, E={ALLOW} | DENY / ALLOW |
| deny org-root + allow doc-42; ask doc-42 | both in L(doc-42); E={ALLOW,DENY}. No specificity is consulted: the lineage is a set | DENY (a most-specific-wins shortcut would wrongly say ALLOW) |
| deny doc-42; ask (A, finance) | L(finance)={finance, org-root} ∌ doc-42 | not affected |
| unlisted resource x | L(x)={x}: exact grants only | stage-1 behavior |
| group asked directly: allow (read, finance), ask finance | finance ∈ L(finance) | ALLOW |
| a→b, b→a | walk from a returns to a → cycle | `InvalidModelError` naming a and b |
| a→a | walk meets start at step 1 | `InvalidModelError` naming a |
| two parents | file: repeated key → A7 error; code: unrepresentable in a `Mapping`, and normalized collisions are rejected | `InvalidModelError` |

**Time** (window [t0,t1))

| Case | Trace | Result |
|---|---|---|
| now = t0 | `t0 <= t0` and `t0 < t1` | in force |
| now = t1 | `t1 < t1` false | not in force |
| now < t0 | `t0 <= now` false | not in force |
| `from` only / `to` only / neither | the absent side is `None`, so that conjunct is true | open bounds |
| from = to, from > to | `_Window.__post_init__` | `InvalidModelError` |
| naive `from`/`to` | `_instant` | `InvalidModelError` |
| naive or non-datetime `now` | `_instant` in the parse step, before lookup | `InvalidQuestionError` |
| same instant, `+00:00` vs `+02:00` | `_instant` converts both to UTC, so they are equal instants | identical answers; equal windows also dedupe (A6) |
| expired deny (now ≥ its `to`) + allow | the deny does not apply; E={ALLOW} | ALLOW |
| not-yet-valid allow (now < its `from`) | E=∅ | DENY (default line) |

**Interactions**

| Case | Trace | Result |
|---|---|---|
| deny (read, finance) [t0,t1) vs permanent allow (read, doc-42) | now in window: E={ALLOW,DENY} → DENY. now outside: E={ALLOW} → ALLOW | both sides as required |
| same (effect,A,R) with windows [t0,t1) and [t2,t3) | two distinct `_Grant`s; each applies in its own window | in force in each, not in the gap |
| exact duplicate grant | equal `_Grant` values; one element in the frozenset | idempotent (A6) |

**Crossings no listed case names** (§1 trace, each new axis × each existing rule):
- *Deny × unknown user:* `_roles_of.get` gives ∅, so E=∅ and the default DENY applies. Same as stage 1.
- *Deny × zero-role / empty role:* same as above. An empty role contributes ∅ and never blocks anything.
- *Deny × action exactness:* a deny on `Write` does not block `write` (A4, `_Grant` equality).
- *Hierarchy × action:* inheritance is over resources only. There is no action lineage (A4).
- *Hierarchy × unknown resource:* x is unlisted, so L(x)={x}; an ungranted x → DENY. Same as stage 1.
- *Hierarchy × string subclasses:* `parents` keys and values are normalized, so a `StrEnum` resource name links
  like its plain string.
- *Time × validation ordering:* `now` is parsed with the other three parts before any lookup, so an unknown user
  plus a naive `now` raises.
- *Time × A6:* windows are part of grant identity, so two grants that differ only in window stay distinct (the
  two-windows case). Equal instants in different offsets collapse, because they are normalized to UTC.
- *Time × hierarchy × deny:* each grant's window is checked by the grant itself, independently of which lineage
  member it names, so a windowed deny on any ancestor behaves like a windowed deny on the leaf.
- *Effect default × stage-1 input:* a grant without `effect` is an allow, which is exactly the stage-1 meaning.

**Stage-1 preservation (proof, not sampling).** A model with no deny, no parents and no windows contains only
grants `_Grant(ALLOW, a, r, _Window(None, None))`, and L(R)={R} for every R. So `applies(A, {R}, now)` ⇔
`a == A ∧ r == R`, which is stage-1 `_Permission` equality, at any `now`. Every E ⊆ {ALLOW}, so `decide` returns
ALLOW ⇔ E ≠ ∅ ⇔ some role holds (A,R). That is the stage-1 rule. Every row of stage-1 §3.4's table follows
unchanged, and the §8 characterization tests run against the stage-2 build **unedited except for supplying
`now=`**, which is the one deliberate signature change.

## 9. Key decisions and alternatives rejected

| Decision | Rejected alternative | Why |
|---|---|---|
| Precedence lives only in `decide`, over a set of effects | per-role verdicts combined later; "first match" over ordered grants | a per-role verdict would split precedence across two owners (role-level and user-level); ordering invents a precedence the product does not have |
| Lineage is an unordered set | ordered ancestor path, nearest-grant-wins walk | B1 makes specificity irrelevant, and an order nobody reads is a speculative moving part. Falsifier: a product change that makes specificity matter |
| Deny is `_Effect.DENY` on a grant | a separate `denies=` mapping; reusing `Decision` as the effect | a parallel collection would need parallel parsing, windows and hierarchy (shotgun surgery). Reusing `Decision` would equate "explicit deny" with "the answer deny", the concept cram the package warns about. The two enums share members but not a reason to change (the answer could gain a value that an effect never would), so this is not duplication that couples |
| `_Permission` removed, fields folded into `_Grant` | keep `_Permission(action, resource)` inside `_Grant` | stage 1 kept `_Permission` because its equality *was* the matching rule. Matching is now "action equal ∧ resource in lineage", so its equality matches nothing and it would be an inert wrapper (lazy class). Supersedes 0002's "`_Permission` owns permission identity" |
| Keep `_Role` | flatten each user to `frozenset[_Grant]` at build | flattening is a valid simplification, but it would overturn 0002's recorded concept-fit decision for a one-class saving, and the product still phrases the rule over "any of U's roles". `_Role` stays a filter over its own grants, not a middle man. Falsifier: if a review finds `_Role.effects` is only ever forwarded, flatten it |
| `_Hierarchy` as a type | a bare `_lineage_of` dict on the model, with the "unlisted = own root" default in `decide` | the default would then leak into `decide`, which would own a reach clause too. The type is the one home for the tree invariant and for reach |
| Unbounded window is `_Window(None, None)` | `window: _Window \| None` | one representation of "always in force"; no `None` branch |
| `parents` map, not group member lists | `groups: {g: [members]}` | two parents become unrepresentable, which removes a check and an error |
| Grant keys checked in the core | loader and core both check | one owner of the key list; in-code input has the same typo risk |
| `now` keyword-only, required | optional with a clock default in the library | B4; and a library clock is hidden global state |
| One core module | `hierarchy.py`, `time.py` | same reason to change; splitting would leak private names across modules |
| No new dependency (no `dateutil`, `pytz`) | — | `fromisoformat` (3.11) and `timezone.utc` cover the need |

**Supersessions of stage-1 records** (the Guide should write these into a new decision record; I edit nothing
else):
1. `_Permission` is removed; `_Grant` owns grant identity (A6 over whole grants).
2. The in-code grant form changes from a `(action, resource)` tuple to a named mapping.
3. Grant-key validation moves from `json_file` into the core.
4. `decide` gains the keyword-only `now`.
5. Stage-1 §3.4's closing line "Deny is the absence of any grant… no deny machinery" is superseded: an explicit
   deny is now a fact, and "no applicable grant" remains the default deny.

## 10. Test plan (test-first; behavior through `decide`, the constructor, `load_model` and `main` only)

- **Characterization (written and green before any change):** the stage-1 §8 suite is run as-is against the
  stage-1 build, then ported by the mechanical addition of `now=` (a fixed aware instant) and the tuple→mapping
  grant form. It must pass unchanged in meaning against stage 2, **at several `now` values** (past, present, far
  future), for a model with no deny, no parents and no windows. A stage-1 JSON file must load and answer
  identically.
- **Combining rule:** every row of §8 *Deny*. Also: an explicit deny and "no grant" both yield DENY while
  allow-only yields ALLOW, across a grid of role layouts (deny in same role / other role / only role).
- **Reach:** every row of §8 *Hierarchy*, including depth ≥ 2 and the deny-ancestor + allow-leaf case. Also: a
  root named only as a parent is askable; a chain depth of 5; a cycle error lists every member of two
  independent cycles at once; a cycle *and* an undefined role reported in one error.
- **In force:** every row of §8 *Time*, including both boundary instants, open bounds each side, `from == to` and
  `from > to`, naive and non-datetime (`date`, `str`, `None`) in model and question, offsets `+00:00`/`+02:00`/`Z`
  for the same instant, and a windowed allow and deny each crossing their boundary.
- **Interactions:** every row of §8 *Interactions*, plus the unlisted crossings in §8 (unknown user + naive `now`
  raises; `StrEnum` in `parents`; action exactness under deny).
- **Grant declarations:** effect absent → allow; `"Deny"`, `""`, `5` → error listing the allowed values; an
  unknown key (`"efect"`) → error; `action` or `resource` missing → error; a non-mapping grant (`("read","x")`,
  the stage-1 tuple) → error naming the expected shape; duplicates with equal windows (including in different
  offsets) → same decisions as once.
- **Immutability and replacement:** attributes are unsettable; mutating the caller's `parents` after
  construction changes nothing; rebinding between two models that differ in *both* hierarchy and grants, chosen
  so that a torn mix answers differently from either, under the threaded stress test (regression guard; the
  guarantee is structural).
- **File edge:** the §5 example answers as traced; a stage-1 file is still valid; bad ISO text → error with path;
  a naive ISO timestamp → the core's naive error plus the path note; a repeated `parents` key → A7 error;
  `parents` not an object → error; an unknown top-level key still rejected; the same model built in code and from
  file gives identical decisions over a question × `now` grid.
- **CLI:** `--now` inside or outside a window flips the exit code between 0 and 1; a naive `--now` → exit 2 with
  the core's message; garbage `--now` → usage error, exit 2. Without `--now`, a model whose deny window spans
  "now ± 1 day" gives DENY (the wall-clock default is exercised without mocking a clock in the library).
- **Architecture fitness:** the `ast` of `model.py` imports only the allowed set (now including `datetime`);
  **no call to `datetime.now`, `utcnow`, `today`, and no `time` import in the core** (B4); `import entitlements`
  still does not load `json`; `__all__` is unchanged; the public surface of `EntitlementModel` is still exactly
  `{decide}`.

## 11. Assumptions added (A10–A15)

- **A10 — a grant without `effect` is an allow.** This keeps every stage-1 file and grant meaning unchanged. Effect
  values are exact and case-sensitive (`allow`/`deny`), consistent with A4.
- **A11 — the wire names are `effect`, `from`, `to` and `parents`.** They are the product's own words
  ("[from, to)", "belong to a group").
- **A12 — every resource on a cycle is reported in one error,** together with any undefined-role pairs (the
  stage-1 "consistency: report all" rule).
- **A13 — a parent needs no declaration of its own.** Resources stay opaque names (A4); a name that appears only
  as a parent is a root. A parent or child that no grant mentions is valid.
- **A14 — the CLI's default `now` is the wall clock in UTC, read once per invocation;** `--now` takes an aware
  ISO-8601 instant.
- **A15 — hosts migrate grant tuples to mappings once.** The stage-1 in-code tuple form is not kept as an alias
  (§2.1).

## 12. Deliberately not built

Specificity or depth ordering; nearest-grant resolution; per-role verdicts; a public `Grant`, `Window` or `Effect`
type; a `Question` object; a clock abstraction or injectable clock (the value `now` *is* the injection); a
library-side default for `now`; a `groups` member-list form; a DAG or multi-parent hierarchy; hierarchy on
actions; time-bounded roles or assignments (B5); a tuple alias for grants; loader-side grant-key checks;
precomputed effective permissions per user; caching; explanations (A5); a `hierarchy.py` or `time.py` split; any
dependency (`dateutil`, `pytz`, test libraries).

## 13. Subtractive pass (each addition and the present force behind it)

| Added | Present force | Kept? |
|---|---|---|
| `_Effect` | requirement 1: deny must be a first-class value a grant carries (concept fit, §4) | yes |
| `_Window` | requirement 3 + B3: the in-force clause needs one owner; `from < to` needs a home | yes |
| `_Window.__post_init__` guard | B3: `from >= to` is a model error | yes |
| `_Grant` | A6 over whole grants; the match clause needs one owner | yes (replaces `_Permission`) |
| `_Grant.applies` | the conjunction of three clauses, owned once | yes |
| `_Role.effects` (reshaped) | the role clause 0002 named for this reopen | yes, with the falsifier stated in §9 |
| `_Hierarchy` + `.of` + `.lineage` | requirement 2 + B2: tree invariants and reach need one home, including the unlisted-resource default | yes |
| `_instant` | B3/B4: two entry points (model, question) share one "aware instant" rule | yes |
| `_grant` parse function | five-key declaration with defaults; keeps the constructor at one altitude | yes |
| `parents` parameter | requirement 2 (the hierarchy is part of the supplied model, B2) | yes |
| `now` parameter | requirement 3 + B4 | yes |
| CLI `--now` | B4: the shell may default and must allow override | yes |
| `_Permission` | none left (its equality is no longer the match rule) | **removed** |
| ordered lineage / specificity | none (B1) | **not built** |
| loader grant-key check | none (the core owns it) | **removed** |
| separate "two parents" check | none (unrepresentable) | **not built** |
| `_combine(effects)` helper | none: `decide` is three lines at one altitude and *is* the combining rule's owner | **not built** |
