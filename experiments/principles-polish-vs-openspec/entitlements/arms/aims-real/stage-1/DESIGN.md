---
title: "Entitlements decision service — stage 1 architecture"
date: 2026-09-23
status: final — panel-merged, revised after one mandatory review round; serves as the root architecture record
---

# Entitlements decision service — stage 1

**Question answered:** may user U perform action A on resource R? → `allow` | `deny`.
**Rule:** allow iff **any** of U's roles grants the permission `(A, R)`; otherwise deny.
**Substrate:** Python 3.11+, standard library only, single process, no persistence (`base-dependencies.md`).
**Product assumptions** A1–A6 are in `goals.md`; this design adds A7–A9 (§9).

## 1. Shape

One immutable domain object, `EntitlementModel`, holds the whole entitlement model and owns the grant rule.
Its constructor is the only way to make one and the only seam through which any source supplies a model.
A JSON-file loader and a CLI are thin edges that end in that constructor and in `decide`. There is no
service/holder object, no source interface, no builder: replacing entitlements means building a new model
and rebinding one reference.

```
entitlements/                 Python 3.11+, stdlib only, no runtime dependencies
├── __init__.py   public core re-exports; does NOT import the edges (import entitlements never loads json)
├── model.py      CORE  errors, identifier rule, _Permission, _Role, Decision, EntitlementModel
├── json_file.py  EDGE  load_model(path) — owns the file format
├── cli.py        EDGE  main(argv) -> int — owns argv, output text, exit codes
└── __main__.py   EDGE  raise SystemExit(main())
tests/            stdlib unittest (no dev dependency)
```

Dependencies (acyclic, pointing to the core): `__main__ → cli → json_file → model`, `cli → model`.
The core imports only `dataclasses`, `enum`, `types`, `collections.abc`; never `json`, `argparse`, `os`,
`pathlib`, `sys`, `io`, `threading`.

**Why the core is one module.** The identifier rule, `_Permission`, `_Role`, the model and its error vocabulary change
for one reason — a change in the entitlement rules — and total roughly a hundred lines. Splitting them into
`errors.py`/`ids.py`/`permission.py` would make lazy modules and shotgun surgery on every rule change. When a
later stage grows the core, the split follows the new change axis, not a template.

## 2. Public API — everything that crosses a seam

```python
# entitlements (re-exported from entitlements.model)
class Decision(enum.Enum):
    ALLOW = "allow"
    DENY = "deny"

class EntitlementModel:
    def __init__(
        self,
        *,
        roles: Mapping[str, Iterable[tuple[str, str]]],   # role -> its (action, resource) grants
        assignments: Mapping[str, Iterable[str]],         # user -> the roles assigned to it
    ) -> None: ...                                         # raises InvalidModelError
    def decide(self, user: str, action: str, resource: str) -> Decision: ...
                                                           # raises InvalidQuestionError

class EntitlementsError(Exception): ...                   # base: the service refused an input
class InvalidModelError(EntitlementsError, ValueError): ...   # a supplied model was rejected
class InvalidQuestionError(EntitlementsError, ValueError): ...# a malformed question (A2)

# entitlements.json_file
def load_model(path: str | os.PathLike[str]) -> EntitlementModel: ...   # raises InvalidModelError

# entitlements.cli
def main(argv: Sequence[str] | None = None) -> int: ...   # 0 allow · 1 deny · 2 error
```

Only stdlib types (`str`, `tuple`, `Mapping`, `Iterable`, `os.PathLike`) and the package's own published
types cross a seam. `_Permission`, `_Role` and the internal maps never do. "`str`" at the seam means any
`str` instance, so a host that names its actions or roles with an `enum.StrEnum` passes the members directly
(§3.1).

Host use:

```python
model = EntitlementModel(
    roles={"editor": [("write", "doc-42"), ("read", "doc-42")], "auditor": []},
    assignments={"alice": ["editor"], "bob": []},
)
model.decide("alice", "read", "doc-42")   # Decision.ALLOW
model.decide("bob", "read", "doc-42")     # Decision.DENY
```

### 2.1 Calibration of each seam

| Seam | Floor (what the consumer needs) | Ceiling (what every producer can supply) | Type |
|---|---|---|---|
| Question in | host and CLI hold three strings | host code, argv — all strings | `decide(user: str, action: str, resource: str)` |
| Answer out | host branches; CLI prints and maps to exit code; A5: nothing else | the rule yields a yes/no fact | `Decision`, two members, no reason |
| Model in | role → permissions (may be empty), user → roles (may be empty) | host dicts/lists; JSON objects/arrays | keyword-only `Mapping`s of `Iterable`s of `str` / `(str, str)` |
| File → model | CLI needs a model from a path | filesystem + JSON | `load_model(path) -> EntitlementModel` |

**Why strings, not typed ids, at the seam.** In Python a raw `"alice"` never equals a `UserId("alice")`, nor a
raw pair a permission object. If the seam took typed values, a caller passing the wrong type would get a **silent deny**
instead of an error — breaking A2 — unless `decide` also type-checked, which makes two validation owners.
With strings at the seam every input goes through one conversion inside the package.

## 3. The core — `entitlements/model.py`

### 3.1 The identifier rule (A4) — one private function

```python
def _identifier(value: object, what: str) -> str:
    """Return the exact-str form of a non-empty str instance; else raise ValueError naming `what`."""
```

- **Accepts** any `str` instance (`isinstance`); rejects everything else (`None`, `5`, `b"read"`).
- **Normalizes** the accepted value to `str.__str__(value)`: an exact `str` with the same characters, built
  by `str`'s own implementation, so no subclass override (`__eq__`, `__hash__`, `__str__`, `__len__`) takes
  part. Emptiness is checked on that result, and that result — never the caller's object — is what the
  package stores, hashes and compares.
- **Why normalize rather than reject subclasses.** The threat is a subclass whose `__eq__`/`__hash__` could
  make a question match a grant it does not name. Normalization removes the threat completely — every
  comparison in the package is exact `str` against exact `str` — whereas rejection also turns an ordinary
  host idiom into an error: an `enum.StrEnum` member (`Action.READ`) *is* the string `"read"` in Python
  (`Action.READ == "read"`, `str(Action.READ) == "read"`) and is accepted as exactly that. Nothing is
  lost: a subclass can contribute only its characters.
- No stripping, case folding or Unicode normalization anywhere in the package — so `Read` ≠ `read` and
  `doc-42` ≠ `DOC-42` hold because nothing could make them equal.
- `what` ("user", "role", "action", "resource") makes the message speak the caller's concept:
  `action must be a non-empty string, got ''`.
- It raises plain `ValueError`; it does not know whether it is parsing a question or a model. Each of the two
  boundaries (the constructor, `decide`) translates it once into its own error type.

**Why not four id types (`UserId`, `RoleId`, `ActionId`, `ResourceId`).** They would carry one identical rule,
cross no seam, and add a wrapping step at every use. The rule has one owner either way. Falsifier for this
choice: the day one kind of identifier gains a rule of its own, it gets its own type.

### 3.2 `_Permission` — the unit of grant (internal)

```python
@dataclass(frozen=True, slots=True)
class _Permission:
    action: str
    resource: str
```

Owns **permission identity**: two permissions are the same iff both named fields are the same exact string.
That is all it owns — it says nothing about who holds a permission. Built only from `_identifier` results.
There is nowhere to put wildcards or implication, and none are wanted (A4).

### 3.3 `_Role` — what a role grants (internal)

```python
@dataclass(frozen=True, slots=True)
class _Role:
    permissions: frozenset[_Permission]
    def grants(self, permission: _Permission) -> bool:   # permission in self.permissions
```

Owns the **role-level clause**: a role grants a permission iff that permission is one of the role's declared
grants — membership, with no implication between grants and no grant derived from another. It relies on
`_Permission` identity to decide "one of" but does not define it. An empty `permissions` is valid (A3).
Called only from `decide`, which never reads `permissions` itself (Tell-Don't-Ask).

**No `name` field.** A role's name is how a declaration *refers* to it, and that reference is resolved once,
inside the constructor (§3.4). No query reads a name (A5 forbids naming the granting role), so a stored name
would be an inert member. Consequence, stated because it is visible in the representation only: two roles
with identical grants are equal values and collapse to one element in a user's `frozenset[_Role]`. No
decision can observe this — "any of U's roles grants p" has the same answer over the set with or without the
duplicate — and it is A6's set semantics applied one level up.

**Why `_Role` rather than storing each user's grants as `frozenset[frozenset[_Permission]]`.** The
alternative is the same data with the role-level clause left implicit in `frozenset.__contains__` inside
`decide`'s expression, so `decide` would own both clauses of the rule and the domain's second concept would
exist only as an anonymous inner set. `_Role` earns its place by two present forces, not by a foreseen stage:
*concept fit* — the stated rule is phrased over roles ("any of U's roles grants (A,R)"), and with `_Role` the
grant-rule expression reads as that sentence; *ownership* — the two clauses of the rule (user-level
quantifier, role-level membership) get two distinct homes, so neither is folded into the other. Its cost is
one frozen dataclass of one field and one one-line method, with no seam, no protocol and no subclassing.

### 3.4 `EntitlementModel` — immutable, consistent by construction, owner of the grant rule

Internal representation: `__slots__ = ("_roles_of",)`; `_roles_of: Mapping[str, frozenset[_Role]]`
(a `MappingProxyType` over a private dict). A user maps to **resolved role objects, not role names**, so once
built the model cannot represent an assignment to an undefined role — A3 is a structural invariant, and there
is no lookup at query time that could fail. The name → role table is local to the constructor and discarded
when it returns: no query needs it (A5).

**Constructor contract — fail fast, all or nothing, in two phases.**

*Phase 1 — parse (stops at the first error).*

1. Each argument must be a `Mapping`; else `InvalidModelError`.
2. Parse `roles`: each key through `_identifier(…, "role")`; each value must be a non-`str` iterable, consumed
   once (generators work); each grant must be a 2-item non-`str` sequence whose items pass
   `_identifier(…, "action")`/`(…, "resource")`. Grants collect into a `frozenset` (A6). Result: a local
   table name → `_Role`.
3. Parse `assignments`: each key through `_identifier(…, "user")`; each value a non-`str` iterable of role
   names through `_identifier(…, "role")`. Result: a local table user → frozenset of role names (A6).
4. In either mapping, two keys that normalize to the same exact string (possible only with a `str` subclass
   whose `__eq__`/`__hash__` kept them apart in the caller's mapping) are rejected, naming the key — the
   in-code counterpart of A7; merging or keeping the last would silently drop a declaration.

*Phase 2 — check consistency (reports every violation).*

5. Resolve every assigned role name against the role table. Collect every `(user, undefined role)` pair;
   if any, raise **one** `InvalidModelError` listing them all (A3). Otherwise each user maps to a
   `frozenset[_Role]`.
6. Freeze: store the result behind `MappingProxyType`; the caller's containers are never aliased.

**Why the two phases report differently.** A parse error means the input's shape cannot be trusted past that
point — a bare string where a list belongs, a grant of the wrong arity — so anything reported after it may be
an artifact of it; the first one is the actionable one. Phase 2 runs only on a fully parsed model, where each
dangling reference is independent of the others and the typical cause (a role renamed or removed) produces
several at once; reporting them together saves the supplier a fix-and-retry loop per user. The rule a host
can rely on: *malformed input → the first problem; well-formed but inconsistent → all the problems.* The JSON
edge's own shape checks (§4) follow the parse rule.

Every failure is `InvalidModelError` with its location (`role 'editor', grant #2: resource must be a
non-empty string, got ''`); `ValueError` from `_identifier` is translated with `raise … from`.
The bare-`str` guards (`isinstance(value, str)`, so subclasses too) matter: `{"alice": "editor"}` would
otherwise iterate into roles `e, d, i, …`, and a grant `"ab"` would unpack into two one-character ids — both
would *succeed* wrongly.

Post: either a model satisfying every invariant exists, or none does. There is no half-built instance, no
second constructor, no `validate()` to forget.

**`decide(user, action, resource) -> Decision` — the only public member.**

1. Parse the whole question first: `_identifier` on all three parts (first bad part reported — the parse
   rule above), then `_Permission(action, resource)` from the normalized values. `ValueError` →
   `InvalidQuestionError` naming the part. Order matters: `decide("nobody", "", "doc")` must raise, not
   return DENY because the user is unknown.
2. The grant rule — its entire body, over the normalized user `u` and permission `p`:
   `any(role.grants(p) for role in self._roles_of.get(u, frozenset()))` → `ALLOW` if true else `DENY`.

Pure query: reads immutable data, changes nothing (CQS), safe from any number of threads.

**Why every stated case needs no branch of its own:**

| Case | Path | Result |
|---|---|---|
| unknown user | `.get` → ∅; `any(∅)` is false | DENY |
| user with zero roles | stored ∅ — the *same* path as unknown (A3) | DENY |
| roles, none granting | every `grants` false | DENY |
| two roles, only the second grants | `any` reaches it; order irrelevant | ALLOW |
| (write,R) granted, (read,R) asked | `_Permission` inequality on action | DENY |
| (read,R1) granted, (read,R2) asked | `_Permission` inequality on resource | DENY |
| `Read` vs `read`, `doc-42` vs `DOC-42` | exact `str` equality | DENY |
| (read,R) granted, asked as (`Action.READ`,R) with `Action` a `StrEnum` | normalized to `"read"`, then equal | ALLOW |
| role granting nothing | empty frozenset; never blocks another role | — |

Deny is the absence of any grant. Stage 1 has no deny rule, so there is no deny machinery.

**Immutability.** `__slots__` (no `__dict__`); `__setattr__`/`__delattr__` raise `AttributeError` after
`__init__`; internals are `MappingProxyType`/`frozenset`/frozen dataclasses; inputs copied. Python can always
be subverted via `object.__setattr__`; the intent is that every intended path funnels through construction.

**Why nothing else is public.** No `roles_of`, `users`, iteration, `__eq__`, `to_dict`, `explain`. Each would
expose the representation and invite a second implementation of the grant rule outside the model
("fetch the roles, then decide"); A5 rules out explanations.

**Why the rule is evaluated per query, not precomputed per user.** Precomputing effective permissions at build
time would move the "any role" clause into construction and blur its owner, for a performance gain nobody has
asked for (§13 of the principles is conditional and no requirement is stated).

### 3.5 Errors — one type per distinct handling

| Type | Raised by | Handling it exists for |
|---|---|---|
| `EntitlementsError` | (base) | the CLI's single catch → exit 2 |
| `InvalidModelError` | `EntitlementModel.__init__`, `load_model` | the supplier fixes the model; a host keeps its current model |
| `InvalidQuestionError` | `decide` | the caller of this query has a bug |

An unreadable file, bad JSON, a wrong file shape and an inconsistent model all have the same handling
(reject, keep the old model), so they share `InvalidModelError`; no `ModelFileError` that nobody would catch
differently. Both leaves also subclass `ValueError`, so existing `except ValueError` guards keep working.

## 4. Edge — `entitlements/json_file.py` (sole owner of the file format)

```json
{
  "roles": {
    "editor":  [ {"action": "write", "resource": "doc-42"},
                 {"action": "read",  "resource": "doc-42"} ],
    "auditor": []
  },
  "assignments": {
    "alice": ["editor", "auditor"],
    "bob":   []
  }
}
```

`load_model(path)`:

1. Read as UTF-8. `OSError` → `InvalidModelError` (path in the message, `from` the original).
2. `json.loads(text, object_pairs_hook=_reject_duplicate_keys)`. Python's `json` silently keeps the last of
   repeated keys, which would drop a role's earlier grants without a word; any repeated key is rejected (A7).
   `JSONDecodeError` → `InvalidModelError` with path, line, column.
3. Shape only: top level an object with **exactly** `roles` and `assignments` (unknown key rejected — a typo
   like `"assignment"` would otherwise load an empty model that denies everyone); `roles` an object of arrays
   of objects with **exactly** `action` and `resource`; `assignments` an object of arrays.
4. Convert to the constructor's plain declaration and call `EntitlementModel(roles=…, assignments=…)`.
   An `InvalidModelError` from the core propagates, with `add_note(f"while loading {path}")`.

It deliberately does **not** check leaf values (non-empty strings) or role definitions: those are domain
rules owned by the core, so the loader cannot disagree with in-code construction about what a valid model is.
Permissions are named objects in the file (not pairs) because a file is edited by hand, far from any
docstring. A second format would be a sibling module calling the same constructor, with zero change to the
core — which is why there is no `ModelSource` protocol today.

## 5. Edge — `entitlements/cli.py` (the imperative shell)

`python -m entitlements --model PATH USER ACTION RESOURCE`

- `argparse` parses (its usage errors exit 2).
- `load_model(args.model).decide(args.user, args.action, args.resource)`.
- Prints `decision.value` (`allow`/`deny`) to stdout; returns 0 for allow, 1 for deny (A8), like `test`/`grep`.
- `EntitlementsError` → one line (message + notes) on stderr, return 2, no traceback. Anything else is a bug
  and propagates.

The CLI decides nothing; it reaches the grant rule through the same `decide` a library host calls.

## 6. Replacement and concurrency (A1)

- Replacement = build a new model (in code or `load_model`) and **rebind the host's reference**. Nothing is
  mutated; nothing can be.
- **No torn reads, by construction.** A query is a method on one immutable object; for its whole duration it
  reads only `self`, so it cannot combine one model's assignments with another's grants. Rebinding a
  reference is an atomic store. A thread holding the old reference finishes on the old, consistent model.
  An in-place reload is impossible because there is nothing to mutate.
- A failed rebuild raises before any reference changes, so a bad replacement never leaves the host without a
  model.
- **Why no `EntitlementService` holder with `replace()`.** It would hold one reference and forward `decide` —
  a middle man with no rule — and a second place to ask the question. A revealed lifecycle (reload on signal,
  watched file) is the force that would introduce it. The host must keep its model in one reference; that is
  the documented usage contract.

## 7. Where each rule lives

| Rule | Sole owner | Every path reaches it via |
|---|---|---|
| allow iff any of U's roles grants (A,R) | `EntitlementModel.decide` | host → `decide`; CLI → `load_model` → `decide` |
| a role grants a permission iff it is one of the role's declared grants; nothing implied (A4) | `_Role.grants` | only from `decide` |
| two permissions are the same iff action and resource are the same exact strings (A4) | `_Permission` (its value equality) | only via `_Role.grants` |
| identifier = non-empty `str`, compared by its exact characters (A4) | `_identifier` | constructor and `decide`, the only two entries of raw strings |
| malformed question → error (A2) | `decide` step 1 | — |
| unknown user/action/resource → deny (A2) | the `decide` expression, no special case | — |
| undefined role rejected at build/load (A3) | `EntitlementModel.__init__` phase 2 (resolution to `_Role`) | `load_model` calls the same constructor |
| parse errors: first one; consistency errors: all at once | `EntitlementModel.__init__` (§3.4) | `json_file` shape checks follow the parse half |
| duplicates idempotent (A6) | `frozenset` collection in `__init__` | — |
| model immutable; replacement is whole swap (A1) | `EntitlementModel` | host rebinds |
| allow/deny only (A5) | `Decision` | — |
| file syntax/shape, duplicate keys (A7) | `json_file` | — |
| in-code keys identical after normalization rejected (A7) | `EntitlementModel.__init__` phase 1 step 4 | — |
| argv, output text, exit codes (A8) | `cli` | — |

The first three rows are three different rules composed, not one rule split: `decide` owns the quantifier
over a user's roles, `_Role.grants` owns membership within one role, and `_Permission` owns when two
permissions are the same. Each owner states only its own rule, and changing one reopens only its owner.

## 8. Test plan (test-first; behavior through public seams only; stdlib `unittest`)

- **Grant rule:** single grant allows; unknown user denies; roles none granting deny; two roles with only the
  second granting allow, and the mirror; (write,R)/(read,R) deny; (read,R1)/(read,R2) deny; zero-role user
  denies; an empty role never blocks another role; unknown action/resource deny; no leakage between users;
  empty model denies everything.
- **Exactness:** `Read`/`read`, `doc-42`/`DOC-42`, `alice`/`Alice` deny; assignment to `Editor` when only
  `editor` exists → `InvalidModelError`; `" read"` ≠ `"read"`.
- **Malformed question:** `""`, `None`, `5`, `b"read"` in each position → `InvalidQuestionError` (never
  `TypeError`, never DENY); an empty `StrEnum`/`str`-subclass value → `InvalidQuestionError`; **unknown user
  + empty action raises** (validation before lookup).
- **String subclasses:** `StrEnum` members as user, action and resource in the question, and as role names,
  users, actions and resources in the model, give the same decisions as the plain strings; a subclass whose
  `__eq__` always returns true and `__hash__` is constant, asked for a permission nobody holds → DENY
  (matching is by characters, not by the caller's `__eq__`); two model keys that are distinct in the caller's
  mapping but normalize to the same string → `InvalidModelError`.
- **Construction:** undefined role → error naming user and role; two undefined → one error listing both;
  a malformed grant *and* an undefined role in the same input → the malformed grant is reported (parse before
  consistency); a role declared with no grants is accepted, and a user holding only it is denied everything;
  bad id anywhere in the model; non-pair grants (`"ab"`, 1-tuple, 3-tuple); bare-string assignment; non-mapping
  argument; duplicates → same decisions as the de-duplicated model over a question grid; generator inputs;
  mutating caller's inputs afterwards changes nothing; setting/deleting attributes → `AttributeError`; public
  surface is exactly `{decide}`; `Decision` has exactly two members.
- **Replacement/concurrency:** old reference still answers as the old model after rebinding; failed rebuild
  leaves the current model answering; threaded stress test rebinding between two models chosen so a torn mix
  would give an answer neither gives (regression guard — the guarantee itself is structural).
- **File edge:** the example file answers correctly; bad JSON, wrong shapes, missing/unknown top-level key,
  grant with missing/extra field, repeated key at any level → `InvalidModelError` with path; undefined role in
  file → core error with the path note; `""`/`5` as an action → rejected by the core; a grant or role
  repeated *within* a list → same decisions as once (A6, not A7); case preserved; missing file →
  `InvalidModelError`; the same model built in code and from file gives identical decisions.
- **CLI:** allow → `allow`/0; deny → `deny`/1; invalid or missing file, empty argument → stderr/2, no
  traceback; wrong arg count → usage/2; `python -m entitlements` via subprocess works.
- **Architecture fitness:** `ast`-parse `model.py`: no forbidden imports; `import entitlements` does not load
  `json`; `__all__` equals §2's core set.

## 9. Assumptions added by this design (A1–A6 are in `goals.md`)

- **A7 — a repeated key in the model file is rejected**, at every level. A repeated role or user block in a
  hand-edited file is more likely a mistake than intent, and rejecting it loses no expressiveness (combine the
  lists). A6 still governs repeated items *within* a list. The in-code counterpart — two mapping keys that
  are distinct objects but the same string once normalized (§3.1) — is rejected by the constructor for the
  same reason.
- **A8 — CLI exit codes:** 0 allow, 1 deny, 2 error. A script that treats any non-zero as failure must read
  the code, not just its truthiness.
- **A9 — whitespace is significant:** `" read"` is valid and distinct from `"read"`; `" "` is a valid id.
  A4 says opaque and exact; if whitespace-only ids should be rejected, that is a one-line change in
  `_identifier`, the single owner.

## 10. Deliberately not built

Holder/service with `replace()`; mutable builder; `ModelSource` protocol; public id or permission types;
`Question` object; `from_json` on the model; getters/equality/serialization on the model; precomputed
effective permissions; explanations; explicit deny rules, wildcards, hierarchies, role inheritance,
conditions, caching, logging, locks; any third-party dependency. Each lacks a present force (reasons inline
above); each would be introduced by the stage that reveals its force.
