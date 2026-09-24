---
title: "Stage-1 decision service — design draft (axis: correct encapsulation)"
date: 2026-09-23
author: design Worker (encapsulation axis)
---

# Stage-1 entitlements decision service: design (encapsulation axis)

## 0. Thesis in five lines

1. **The public seam is plain strings in and a `Decision` out.** Every identifier becomes a validated domain
   value *inside* the package, on one path, so a caller has no way to hand the core an unvalidated or
   wrongly typed value (see §3.1 for why typed ids at the seam would *open* a silent-deny hole in Python).
2. **`EntitlementModel` is the only home of the model and of the grant rule.** Its one constructor validates
   everything, and after that the model cannot hold a dangling role reference: a user's roles are stored as
   resolved role objects, not role names. It exposes one query, `decide`, and nothing else. Callers tell it
   the question; they never read its state.
3. **Deny is simply the absence of a grant.** No deny machinery, no default-deny flag, no rule list.
4. **A source of the model is any code that ends in `EntitlementModel(roles=..., assignments=...)`.** The
   JSON file loader is one such edge. Dependencies point from source to core. The core imports no `json`,
   `argparse`, `pathlib`, `os` or `io`.
5. **Replacing the model means rebinding a reference to a new immutable object.** A query runs as a method
   on one model instance, so it cannot see two models. There is no lock and no holder class; §7 explains
   why neither is needed.

---

## 1. Package skeleton

```
entitlements/                 (Python 3.11+, stdlib only; no runtime dependencies)
├── __init__.py               public API re-exports: EntitlementModel, Decision,
│                             EntitlementsError, InvalidModelError, InvalidQuestionError
├── errors.py                 CORE  the three public error types
├── _identifiers.py           CORE  (private) identifier value objects + Permission; owns "valid identifier"
├── model.py                  CORE  EntitlementModel, Decision, private _Role; owns the grant rule & A3/A6
├── json_file.py              EDGE  load_model(path): JSON file → EntitlementModel; owns the file format
├── cli.py                    EDGE  main(argv) → exit code; owns argv, stdout/stderr, exit codes
└── __main__.py               EDGE  `raise SystemExit(main())`
```

Import graph (acyclic; arrows point toward the stable core):

```
__main__ → cli → json_file → model → _identifiers → errors
                 cli ───────→ model, errors
```

The **core** is `errors`, `_identifiers` and `model`: pure, with no I/O and no knowledge of any source. The
**edges** are `json_file` and `cli`, the only modules that know a file or a process exists. Only
`__init__`'s exports plus `entitlements.json_file.load_model` and `entitlements.cli.main` are public. A module
whose name starts with `_` is internal to the package. No edge imports `_identifiers`.

---

## 2. Public API: the only things that cross a seam

```python
# entitlements/model.py
class Decision(enum.Enum):
    ALLOW = "allow"
    DENY = "deny"

class EntitlementModel:
    def __init__(
        self,
        *,
        roles: Mapping[str, Iterable[tuple[str, str]]],   # role name -> its (action, resource) grants
        assignments: Mapping[str, Iterable[str]],         # user id   -> the role names assigned to it
    ) -> None: ...                                         # raises InvalidModelError

    def decide(self, user: str, action: str, resource: str) -> Decision: ...
                                                           # raises InvalidQuestionError

# entitlements/errors.py
class EntitlementsError(Exception): ...          # base: "the entitlements service refused"
class InvalidModelError(EntitlementsError): ...  # model rejected at build/load (A3, bad ids, bad file)
class InvalidQuestionError(EntitlementsError): ...  # malformed question (A2)

# entitlements/json_file.py
def load_model(path: str | os.PathLike[str]) -> EntitlementModel: ...
                                  # raises InvalidModelError; lets OSError (unreadable file) propagate

# entitlements/cli.py
def main(argv: Sequence[str] | None = None) -> int: ...   # 0 allow, 1 deny, 2 error
```

The public seam carries only these types: `str`, `tuple`, `Mapping`/`Iterable` (stdlib), `os.PathLike`,
and the package's own published `Decision`, `EntitlementModel` and error types. Nothing internal crosses:
not `UserId`, `RoleName`, `Action`, `ResourceId`, `Permission` or `_Role`, and not the internal
dict/frozenset representation.

**Typical in-code host use:**

```python
model = EntitlementModel(
    roles={"editor": [("write", "doc-42"), ("read", "doc-42")], "auditor": []},
    assignments={"alice": ["editor"], "bob": []},
)
model.decide("alice", "read", "doc-42")   # Decision.ALLOW
```

The `(action, resource)` tuple order is the order the spec itself uses for a permission ("a permission
being an `(action, resource)` pair"). It is documented on the constructor. The file format (§5) uses
named fields instead, because a file is edited by hand, far from any docstring.

---

## 3. Core components, their rules, and why they sit where they do

### 3.1 `_identifiers.py`: what a valid identifier is (private)

```python
@dataclass(frozen=True, slots=True)
class _Identifier:
    value: str
    kind: ClassVar[str]                        # "user", "role", "action", "resource" (used in messages)
    def __post_init__(self) -> None: ...       # the ONE check: isinstance(value, str) and value != ""
                                               # raises IdentifierError(kind, value)

class UserId(_Identifier):     kind = "user"
class RoleName(_Identifier):   kind = "role"
class Action(_Identifier):     kind = "action"
class ResourceId(_Identifier): kind = "resource"

@dataclass(frozen=True, slots=True)
class Permission:
    action: Action
    resource: ResourceId

class IdentifierError(ValueError):   # internal only; always translated before it leaves the package
    kind: str; value: object
```

**Owns:** A4, "an identifier is a non-empty `str`, compared exactly". The only code that checks this is
`__post_init__`. Nothing in the package calls `.lower()`, `.strip()` or `.casefold()`, and equality is the
dataclass's field equality over `str`. `Read` ≠ `read` and `doc-42` ≠ `DOC-42` therefore hold by
construction, with no code path to audit.

**Why it is private.** Exposing typed ids at the public seam looks like "value objects over primitives",
but in Python it *weakens* encapsulation. `UserId("alice") != "alice"`, so a host that passes a raw `str`
where a `UserId` is expected gets a silent **deny**, not an error. That breaks A2 unless `decide`
re-checks types, and then there are two validation owners. With strings at the seam, all input goes
through one conversion (`str` to validated value, inside the package), and no caller can forge or
mis-type a domain value. The value objects are still the working currency *inside* the core, which is
where §0 of the principles puts them.

**Why four kinds, not one `Identifier`.** Each is a different concept (concept fit), and `kind` drives the
error message the consumer sees ("action must be a non-empty string, got ''"). `Permission`'s named
fields keep action and resource from swapping silently. They cost one line each and share one rule owner.

**Whitespace.** `" read"` is a valid identifier, distinct from `"read"`. A4 says ids are "opaque, exact",
so we do no trimming (flagged in §10).

### 3.2 `model.py`: `EntitlementModel`, `_Role` and `Decision`

**Internal representation (hidden):**

```python
@dataclass(frozen=True, slots=True)
class _Role:
    name: RoleName
    permissions: frozenset[Permission]
    def grants(self, permission: Permission) -> bool:   # exact membership; no implication (A4)

class EntitlementModel:
    __slots__ = ("_roles_of",)
    _roles_of: Mapping[UserId, frozenset[_Role]]   # MappingProxyType over a private dict
```

After construction a user maps to **role objects, not role names**. So the post-construction model
cannot represent an assignment to an undefined role, and A3 is a structural invariant, not a runtime
lookup that could fail. The role table used to resolve names is thrown away after `__init__`: no query
needs it (A5, no explanation), and keeping it would be a second representation to keep consistent. A role
granting nothing becomes `_Role(name, frozenset())`, which is valid (A3). A user with zero roles maps to
`frozenset()` (valid, and denied everything).

**Rules owned, each once:**

| Rule | Where exactly |
|---|---|
| **Grant rule, user level:** allow iff *any* of U's roles grants (A,R) | `EntitlementModel.decide`, one expression: `any(role.grants(p) for role in self._roles_of.get(u, frozenset()))` |
| **Grant rule, role level:** a role grants (A,R) iff that exact pair is in its set (no wildcard, no implication, no hierarchy) | `_Role.grants`: `permission in self.permissions` |
| **Unknown user → deny, same answer as zero roles** (A2, A3) | the same `decide` expression: `.get(u, frozenset())` makes an unknown user and a user with zero roles take the *same* path, with no special case |
| **Unknown action/resource → deny** (A2) | falls out of `_Role.grants` (not a member); no code for it |
| **Model consistency:** every assigned role is defined (A3) | `EntitlementModel.__init__` while resolving names to `_Role`; after that the invariant is structural |
| **Set semantics:** duplicates are idempotent (A6) | `EntitlementModel.__init__`: grants and assignments are collected into `frozenset`s |
| **Immutability** | `EntitlementModel`: `__slots__`, attributes set once in `__init__`, `__setattr__`/`__delattr__` raise `AttributeError`, internal maps are `MappingProxyType`/`frozenset`, inputs are defensively copied |
| **Allow/deny only** (A5) | `Decision` enum with exactly two members; `decide` returns nothing else |

Splitting the grant rule into "any role" (model) and "this role grants exactly" (role) is not two owners
of one rule. Each clause of the spec's sentence has exactly one home, and `decide` is the only caller of
`_Role.grants`.

**`__init__` contract (fail fast, all or nothing):**

- *Pre:* `roles` and `assignments` are mappings. Values are iterables and are consumed **exactly once**,
  so generators work.
- *Steps, in order:* (1) parse every role name, and every grant as a 2-element non-`str` sequence of
  (action, resource) identifiers, into `_Role`s. (2) Parse every user and every assigned role name, and
  resolve each name against step 1's table. (3) Freeze.
- *Errors:* any `IdentifierError` → `InvalidModelError` naming the location ("role 'editor', grant #2:
  resource must be a non-empty string, got ''"). A grant that is not a pair, including a bare `str` such as
  `"ab"`, which would otherwise unpack into two one-character ids, → `InvalidModelError`. An assignment
  value that is a bare `str` (`{"alice": "editor"}`, which would otherwise iterate as the roles
  `e, d, i, …`) → `InvalidModelError`. Undefined roles → one `InvalidModelError` that lists **every**
  `(user, undefined role)` pair, so a host fixes its model in one pass. A non-mapping argument →
  `InvalidModelError`.
- *Post:* either an `EntitlementModel` that satisfies all the invariants above exists, or none does. There
  is no half-built or "unvalidated" instance, and no second constructor, builder, `from_*` alternative or
  `validate()` method to forget to call.
- *Aliasing:* the caller's dicts and lists are copied into frozen structures, so mutating them afterwards
  cannot change the model.

**`decide` contract:**

- *Pre:* none on the caller beyond the signature. Validating the input is `decide`'s own job.
- *Step 1, the whole question is validated first.* `user`, `action` and `resource` all become domain
  values *before* any lookup. An `IdentifierError` → `InvalidQuestionError` naming the offending part.
  Order matters: `decide("nobody", "", "doc")` must raise, not return DENY because the user was unknown.
  Validating after the lookup would short-circuit malformed questions into denies (tested, §8).
- *Step 2, the grant rule* as in the table.
- *Post:* returns `Decision.ALLOW` or `Decision.DENY` and never mutates anything (query, not command).
  Pure, so it is safe to call from any number of threads.

**Why the model has no other public members.** Tell-Don't-Ask: the only thing any consumer (host, CLI,
tests) needs is the answer to the question. No `roles_of(user)`, `users()`, `__iter__`, `__eq__` or
`to_dict()`. Each would expose the representation, invite a second grant-rule implementation outside the
model ("ask for roles, then decide"), and serves no present force (A5 forbids explanations). Tests assert
behavior only through `decide`.

### 3.3 `errors.py`: boundary vocabulary

| Type | Raised when | Distinct handling that justifies it |
|---|---|---|
| `EntitlementsError` | base only | the CLI catches one type for "the service refused, exit 2" |
| `InvalidModelError` | model rejected at build/load: undefined role, bad id in the model, bad file shape or syntax | the *host* has to fix its model; it happens once, at startup or reload |
| `InvalidQuestionError` | `decide` got an empty or non-`str` part | the *caller* of this query has a bug; per request |

`IdentifierError` stays internal and is always translated, with `raise ... from`, at one of two points:
`__init__` (→ model) or `decide` (→ question). `json.JSONDecodeError` is translated at the file edge.
`OSError` (file missing or unreadable) is not wrapped. It is already stdlib vocabulary the consumer
understands, and the host handles it the same as any I/O failure. Messages speak the consumer's terms
(role, user, action, resource, file path, JSON location), never internal names.

---

## 4. `Decision`: why an enum and not `bool`

There is a present force: the CLI must print `allow`/`deny` and map them to exit codes, and A5 says the
answer is exactly one of two named outcomes. A `bool` makes every consumer re-encode "True means allow".
The enum holds that meaning in one place, `Decision.value` is the CLI's output text, and there is no
third member.

---

## 5. Edge: `json_file.load_model`, the one owner of the file format

```python
def load_model(path: str | os.PathLike[str]) -> EntitlementModel
```

**File format (v1):**

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

**Responsibilities (only syntax and shape, never domain rules):**

1. Read the text as UTF-8 (`OSError` propagates) and parse it with `json.loads(..., object_pairs_hook=...)`,
   so duplicate keys are *seen* rather than silently collapsed.
2. Check the shape. The top level is an object with **exactly** the keys `roles` and `assignments` (both
   required). An unknown key, such as a typo like `"assignment"`, is rejected: silently ignoring it would
   produce an empty model that denies everything. `roles` is an object of name → array. Each grant is an
   object with **exactly** `action` and `resource`. `assignments` is an object of user → array.
3. Build the plain declaration (`dict[str, list[tuple[str, str]]]`, `dict[str, list[str]]`) and call
   `EntitlementModel(roles=..., assignments=...)`.
4. Translate. `JSONDecodeError` → `InvalidModelError` with path, line and column. A shape violation →
   `InvalidModelError` with path and JSON location. An `InvalidModelError` from the model propagates
   unchanged, with `exc.add_note(f"while loading {path}")` (3.11) so the consumer sees which file.

**What it deliberately does not check:** whether leaf values are non-empty strings, or whether roles are
defined. Those are domain rules owned by the core (§3). The loader passes JSON leaves through as they are,
and a `5` or `""` or an undefined role is rejected by the model. The loader therefore cannot disagree
with the in-code path about what a valid model is.

**Duplicate keys (assumption A7, §10).** A repeated role key or user key is **merged** (its arrays are
concatenated before the model is built), which matches A6: a repeated grant or assignment is the same as
one. The loader only concatenates, and de-duplication is still the model's `frozenset` (one owner of set
semantics). A repeated *top-level* key (`roles` twice) is a malformed file → `InvalidModelError`, because
there is no set semantics for the document's own structure.

**Why no `ModelSource` protocol.** The core does not depend on any source abstraction. Its seam for
sources is its own constructor, so dependency inversion holds with nothing extra: the source depends on
the core, never the other way. A protocol would have one implementation and no consumer that is
polymorphic over it (the CLI calls `load_model` directly). The falsifier in §7 of the principles, "name
the X-item the seam serves", finds none at stage 1. A second format would be a new sibling module that
calls the same constructor, with zero change to the core.

---

## 6. Edge: `cli.main`, the imperative shell

```
python -m entitlements --model PATH USER ACTION RESOURCE
```

- `argparse` parses. Its own usage errors exit 2, as usual.
- `model = load_model(args.model)`, then `decision = model.decide(args.user, args.action, args.resource)`.
- It prints `decision.value` (`allow`/`deny`) to stdout and returns **0 for allow and 1 for deny**, like
  `grep`/`test`, so scripts can branch without parsing (A8).
- `EntitlementsError` or `OSError` → one line on stderr (the error's message and notes) → return 2. No
  traceback for these expected failures. Anything else is a bug and propagates.
- The CLI reads the file on every invocation. There is no daemon and no reload inside the CLI.

The CLI decides nothing. It reaches the grant rule through the same `decide` a library host calls, so
there is one path.

---

## 7. Replacing the model, and concurrency

- **Replacement (A1)** means building a new `EntitlementModel` (in code, or `load_model`) and **rebinding
  the host's reference** to it. The old object is never modified, and cannot be: no mutators, frozen
  internals, and defensive copies of the inputs.
- **No torn reads, by construction.** A query is `model.decide(...)`, a method on one immutable object.
  For its whole duration it reads only `self`, so it cannot combine one model's assignments with another
  model's grants. Rebinding a Python reference is a single atomic store, including on free-threaded 3.13+,
  where object references are still stored atomically. A thread that picked up the old reference simply
  finishes on the old, still-consistent model. In-place reload (the falsifier in the exit criteria) is
  impossible because there is nothing to mutate.
- **Why there is no `EntitlementService` holder with `replace()`.** It would hold one reference and
  forward `decide`: a Middle Man with no rule of its own. Atomic swap and consistency already come from
  immutability. It would also create a second place a caller could ask the question from. If a later
  stage reveals a lifecycle (reload on a signal, a watched file), that is the force that introduces it.
- A failed rebuild leaves the host's current reference untouched, because the constructor is all or
  nothing. Rejecting a bad replacement therefore can never leave the service without a model.

---

## 8. Test plan (test-first; behavior through the public seams only)

Tests use stdlib `unittest`, and the `tempfile`/`subprocess` modules for the edge tests. None imports
`_identifiers` or touches private attributes. Each test is named after the rule it pins.

### 8.1 Grant rule (`EntitlementModel.decide`)

| # | Case | Expect |
|---|---|---|
| G1 | alice: editor; editor grants (read, doc-42); ask (alice, read, doc-42) | ALLOW |
| G2 | unknown user `mallory` | DENY |
| G3 | alice has roles r1 and r2, neither grants (read, doc-42) | DENY |
| G4 | alice has r1 and r2, only **r2** grants; and a mirror case where only r1 grants | ALLOW both (order-independent) |
| G5 | (write, R) granted, (read, R) asked | DENY (no implication) |
| G6 | (read, R1) granted, (read, R2) asked | DENY |
| G7 | alice assigned zero roles (`"alice": []`) | DENY, same as G2 |
| G8 | role `auditor` granting nothing is accepted; its holder is denied everything | model builds; DENY |
| G9 | a user holding the empty role *and* a granting role | ALLOW (the empty role never blocks) |
| G10 | unknown action / unknown resource | DENY |
| G11 | no leakage between users: bob (viewer) asks for alice's (editor) permission | DENY |
| G12 | empty model `roles={}, assignments={}` | builds; every question DENY |

### 8.2 Exactness (A4)

| # | Case | Expect |
|---|---|---|
| E1 | granted `read`, asked `Read` | DENY |
| E2 | granted `doc-42`, asked `DOC-42` | DENY |
| E3 | user `alice` assigned, asked as `Alice` | DENY |
| E4 | assignment to `Editor` when only `editor` is defined | `InvalidModelError` (roles are case-sensitive too) |
| E5 | `" read"` vs `"read"` | DENY (no trimming) |

### 8.3 Malformed question (A2), errors at the boundary

| # | Case | Expect |
|---|---|---|
| Q1–Q3 | `""` as user, as action, as resource (known user) | `InvalidQuestionError` naming the part |
| Q4 | `None` / `5` / `b"read"` in each position | `InvalidQuestionError` (never `TypeError`, never DENY) |
| Q5 | **unknown** user with an empty action: `decide("nobody", "", "doc")` | `InvalidQuestionError`, not DENY (validation runs before lookup) |
| Q6 | `InvalidQuestionError` is an `EntitlementsError` | true |

### 8.4 Model construction (A3, A6, immutability)

| # | Case | Expect |
|---|---|---|
| M1 | user assigned to an undefined role | `InvalidModelError` naming user and role, raised at construction |
| M2 | two users with undefined roles | one error listing both pairs |
| M3 | empty or non-`str` role name, user, action or resource inside the model | `InvalidModelError` naming the location |
| M4 | grant that is not a pair: `"ab"`, `("read",)`, `("a","b","c")` | `InvalidModelError` |
| M5 | assignment value is a bare string `{"alice": "editor"}` | `InvalidModelError` |
| M6 | duplicate grant in one role; duplicate role in one user's list | builds; same decisions as the de-duplicated model on a full question grid |
| M7 | generator inputs (roles and assignments given as generators) | builds correctly (consumed once) |
| M8 | mutate the caller's input dicts and lists after construction | decisions unchanged (defensive copy) |
| M9 | assigning an attribute on the model, or deleting one | `AttributeError` |
| M10 | public surface: the model's non-dunder public attributes are exactly `{"decide"}` | true (guards against getters creeping in) |
| M11 | `Decision` has exactly the members `ALLOW` and `DENY`, with values `"allow"`/`"deny"` | true |

### 8.5 Replacement and concurrency

| # | Case | Expect |
|---|---|---|
| R1 | build M1, keep a reference, build M2 with different grants, rebind | the old reference still answers as M1, the new one as M2 |
| R2 | a failed rebuild (invalid replacement) raises and leaves the host's existing model answering as before | true |
| R3 | stress: 8 threads loop `current.decide(...)` over a question grid while the main thread rebinds `current` between M1 and M2 thousands of times. M1 and M2 are chosen so that a torn mix (M1 assignments with M2 grants) would give an answer neither model gives | every answer ∈ {M1's answer, M2's answer} for its question |

R3 is a regression guard. The real guarantee is structural (§7), because a probabilistic test cannot prove
a race is absent.

### 8.6 File edge (`load_model`)

| # | Case | Expect |
|---|---|---|
| F1 | the example file in §5 | the model answers G1/G5/G7/G8-style questions correctly |
| F2 | invalid JSON | `InvalidModelError` with the path and line |
| F3 | top level is an array; `roles` missing; `assignments` missing | `InvalidModelError` |
| F4 | unknown top-level key (`"assignment"` typo) | `InvalidModelError` (not a silently empty model) |
| F5 | a grant object missing `resource`, or with an extra key | `InvalidModelError` |
| F6 | undefined role in the file | `InvalidModelError` from the core, with the file path in its notes |
| F7 | `""` or `5` as an action in the file | `InvalidModelError` (the core's rule; the loader has no check of its own) |
| F8 | role key repeated (two `"editor"` entries) | merged: the union of both grant lists |
| F9 | user key repeated | merged: the union of role lists |
| F10 | `roles` key repeated at the top level | `InvalidModelError` |
| F11 | case preserved from the file (`Read` in the file, ask `read`) | DENY |
| F12 | missing file | `OSError` propagates |

### 8.7 CLI (`main(argv)`, with stdout and stderr captured)

| # | Case | Expect |
|---|---|---|
| C1 | allowed question | stdout `allow`, returns 0 |
| C2 | denied question | stdout `deny`, returns 1 |
| C3 | invalid model file | stderr message including the path, returns 2, no traceback |
| C4 | missing model file | stderr, returns 2 |
| C5 | `""` passed as the action argument | stderr, returns 2 |
| C6 | wrong number of arguments | argparse usage, exit 2 |
| C7 | `python -m entitlements ...` via subprocess | same as C1 (entry-point wiring) |

### 8.8 Architecture fitness (keeps the seams honest)

| # | Check |
|---|---|
| A1 | parse (`ast`) the sources of `errors`, `_identifiers` and `model`: no import of `json`, `argparse`, `pathlib`, `os`, `io`, `sys`, `threading` |
| A2 | no module except `model` references `_Role`, and no edge module imports `_identifiers` |
| A3 | `entitlements.__all__` equals the published set in §2 |

---

## 9. Where each stated rule lives (the single-owner map)

| Rule (source) | Sole owner | Every entry path reaches it via |
|---|---|---|
| allow iff any of U's roles grants (A,R) | `EntitlementModel.decide` | library call → `decide`; CLI → `load_model` → `decide` |
| a role grants exactly its (A,R) pairs; no implication or wildcard (A4) | `_Role.grants` | only called from `decide` |
| identifier = non-empty `str`, exact and case-sensitive (A4) | `_Identifier.__post_init__` | model constructor and `decide`, the only two places raw strings enter |
| malformed question → error (A2) | `decide`, step 1 (translation to `InvalidQuestionError`) | — |
| unknown user, action or resource → deny (A2) | the `decide` expression (no special case) | — |
| undefined role → rejected at build or load (A3) | `EntitlementModel.__init__` (resolving names to `_Role`) | in-code construction; `load_model` calls the same constructor |
| role granting nothing is valid; zero-role user is valid and denied (A3) | `EntitlementModel.__init__` accepts them; `decide` treats them uniformly | — |
| duplicates idempotent (A6) | `frozenset` collection in `EntitlementModel.__init__` | file duplicate keys are concatenated by the loader, then de-duplicated here |
| model supplied whole; replacement = whole swap (A1) | immutability of `EntitlementModel` | host rebinds its reference |
| allow/deny only (A5) | `Decision` (two members) | — |
| file syntax and shape | `json_file` | — |
| argv, output text, exit codes | `cli` | — |

---

## 10. Assumptions this design adds (for the Guide to confirm or override)

- **A7: duplicate JSON keys.** A repeated role or user key in the file is merged (a union), in line with
  A6. A repeated top-level key is a malformed file. The alternative, rejecting every duplicate key, is
  also defensible and would be a one-line change inside `json_file`.
- **A8: CLI exit codes.** 0 = allow, 1 = deny, 2 = error.
- **A9: whitespace is significant.** `" read"` is a valid identifier distinct from `"read"`, and a
  whitespace-only id such as `" "` is accepted, because A4 says opaque and exact and non-empty is the only
  stated constraint. If the product owner wants whitespace-only ids rejected, that goes in
  `_Identifier.__post_init__`, the one owner, and nowhere else.
- **Unknown file keys are rejected** rather than ignored. This is a fail-fast reading of A3, since
  otherwise a typo means a silent deny-everything.

---

## 11. Subtractive pass: each element and the present force that keeps it (or the lack of one that cut it)

**Kept:**

| Element | Present force |
|---|---|
| `EntitlementModel` | the one home of the model, the grant rule and A3 consistency |
| `_Role` with `grants` | makes a dangling assignment unrepresentable after construction; owns the exact-match clause |
| `_Identifier` + 4 kinds | one owner of the identifier rule; concept fit; the kind names the error message |
| `Permission` | the spec's own concept; exact pair equality *is* A4's "no implication" |
| `Decision` enum | A5; one place that maps the meaning to CLI text and exit codes |
| 3 error types | two distinct handlings (model vs question) plus the one catch-all the CLI needs |
| `json_file.load_model` | the CLI needs a file source (A1); confines `json` to an edge |
| `cli.main` returning `int` | the CLI entry point; returning a value keeps it testable without `SystemExit` |
| architecture fitness tests | the objective's criterion "the core never imports json/argparse" becomes checkable |

**Cut:**

| Cut | Why |
|---|---|
| `EntitlementService` / holder with `replace()` | Middle Man; immutability already provides atomic swap; a second place to ask the question |
| `ModelBuilder` (mutable, incremental) | a second construction path plus a mutable type; the declarative constructor covers both producers |
| `ModelSource` protocol / repository | one implementation, no polymorphic consumer; the constructor already is the source seam (falsifier: no X-item) |
| public `UserId`/`Action`/`ResourceId`/`Permission` | opens the raw-`str` silent-deny hole; forces a second type check; leaks representation |
| public `Question`/`AccessRequest` type | three strings are the whole question; a wrapper adds a construction step with no rule of its own |
| `EntitlementModel.from_json` / `from_file` | would pull the file format into the core |
| getters (`roles_of`, `users`), `__eq__`, `to_dict`, `__iter__` | no consumer (A5); an invitation to decide outside the model |
| precomputed per-user effective-permission sets | a performance choice with no stated need; it would move the "any role" clause into construction and blur its owner |
| explanation / "granted by" in the result | A5 |
| deny rules, wildcards, hierarchy, normalization, caching, logging, locks | unrevealed or unneeded (§7) |
| a separate error type for "file unreadable" | same handling as any `OSError`; wrapping adds a type nobody handles differently |

---

## 12. Risks and new facts surfaced

1. **`json` silently keeps the last duplicate key.** Left alone, this would violate A6 (a role declared
   twice would lose grants). Handled with `object_pairs_hook` and A7.
2. **Typed ids at a Python public seam cause silent denies.** A raw `str` never equals a `UserId`. This
   is the reason the seam takes strings (§3.1). Any merged design that exposes typed ids must add a type
   guard in `decide`, or it breaks A2.
3. **Validation order.** A malformed question about an unknown user must raise, not deny. This is easy to
   get wrong if lookup happens before validation (test Q5).
4. **Python iterability traps.** A `str` passed where a pair or list is expected unpacks or iterates into
   characters and would *succeed* wrongly. It is guarded explicitly (M4, M5).
5. **Unknown keys in the file.** A typo would otherwise yield an empty model that denies everything
   silently. It is rejected (F4).
6. **Encapsulation in Python is by convention** (`object.__setattr__` can always bypass it). As the
   principles say, the design funnels every intended path through one owner, and M9 and A1–A3 test that.

**Result: met.** Every exit criterion in `.aims/state.md` has a named owner (§9) and at least one test
(§8). Nothing in the evidence invalidates the objective.
