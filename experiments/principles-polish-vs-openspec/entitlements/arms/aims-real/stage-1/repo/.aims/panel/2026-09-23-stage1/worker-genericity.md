---
title: "Stage-1 decision service: design (axis: correct genericity)"
date: 2026-09-23
worker: genericity
---

# Stage 1 entitlements decision service: design

The axis is correct genericity. For every seam I set the type between two limits. The floor is what the
consumer needs to be complete. The ceiling is what every producer can honestly supply. Each seam below
names both limits, and a type with no present force behind it is cut (§ Subtractive pass).

## 1. The shape in one paragraph

The whole product is one immutable domain object, `EntitlementModel`. Its constructor is the only way to
make one. The constructor parses and validates the supplied relations, enforces model consistency (A3) and
collapses duplicates (A6). The object then answers `decide(user, action, resource) -> Decision`, and that
method holds the grant rule, once. Model sources are thin adapters that call that constructor. One source
is host code, which calls it directly. The other is a JSON file adapter used by the CLI. There is no service
object, no source interface and no holder. Replacing entitlements means building a new model and rebinding
a reference. That is safe for concurrent readers because the model cannot change after construction.

```
                 ┌────────────── edges (I/O, formats) ──────────────┐
  argv ──► cli.main ──► json_file.load_model(path) ──┐                │
                 └───────────────────────────────────┼────────────────┘
  host code ─────────────────────────────────────────┤  (str, Mapping, Iterable only)
                                                     ▼
                 ┌────────────────── core (pure) ─────────────────────┐
                 │ model.EntitlementModel(roles=…, assignments=…)     │
                 │     .decide(user, action, resource) -> Decision    │
                 │ identifiers (UserId, RoleId, Action, ResourceId)   │
                 │ errors (EntitlementsError, InvalidQuestion,        │
                 │         InvalidModel)                              │
                 └────────────────────────────────────────────────────┘
```

Dependencies point inward only: `cli → json_file → model → identifiers, errors`. The core imports only
`dataclasses`, `enum`, `types` and `collections.abc`. It never imports `json`, `pathlib`, `argparse` or
`sys`.

## 2. Package skeleton

```
entitlements/
  __init__.py      # public surface (re-exports only)
  errors.py        # EntitlementsError, InvalidQuestion, InvalidModel          [core]
  identifiers.py   # _Identifier base + UserId, RoleId, Action, ResourceId    [core, internal]
  model.py         # Permission, Decision, EntitlementModel                   [core]
  json_file.py     # load_model(path) -> EntitlementModel                     [edge]
  __main__.py      # python -m entitlements  → cli.main                       [edge]
  cli.py           # main(argv) -> int                                        [edge]
tests/
  test_identifiers.py  test_model_build.py  test_decide.py
  test_immutability.py test_json_file.py    test_cli.py
```

The public surface is what `__init__` exports:

```python
from entitlements import (
    EntitlementModel, Decision, load_model,
    EntitlementsError, InvalidQuestion, InvalidModel,
)
```

`Permission` and the identifier types are internal currency. They are not exported, because no consumer
needs them (see §3).

## 3. Genericity calibration, seam by seam

| Seam | Consumer (floor) | Producers (ceiling) | Chosen crossing type |
|---|---|---|---|
| Question in: `decide(...)` | Host code and CLI. Both hold three strings. | Every caller can supply a `str`. | `user: str, action: str, resource: str`, in the product's canonical U, A, R order. |
| Answer out | Host needs to branch. CLI prints allow or deny. A5 says there is nothing else. | The rule yields a boolean fact. | `Decision` enum with two members, `ALLOW` and `DENY`. It carries no reason (A5). |
| Model in: constructor | Core needs role → set of permissions, user → set of roles, and roles that grant nothing (A3). | Host code has dicts and lists. JSON has objects and arrays. Both are natural `Mapping`s of iterables. | `roles: Mapping[str, Iterable[tuple[str, str]]]`, `assignments: Mapping[str, Iterable[str]]`, keyword-only. |
| File → model | CLI needs a model from a path. | The filesystem and the JSON format. | `load_model(path: str \| os.PathLike) -> EntitlementModel` |
| Internal currency | `decide` and the constructor need identifiers that are validated, hashable and distinct by kind. | Each is parsed from a `str` once. | `UserId`, `RoleId`, `Action`, `ResourceId`, `Permission` |

Why the public seam speaks `str` and not the value types:

- **Ceiling.** Every producer of identifiers holds a string: host code, argv and JSON.
- **Floor.** Every consumer is complete with strings.
- **The Python hazard it closes.** Suppose `decide` accepted `UserId`. A host that passed a raw `"alice"`
  would never match `UserId("alice")`, because dataclass equality includes the class. The result would be
  a silent deny, which violates A2 ("malformed is an error, not a deny"). With `str` at the seam and
  parsing inside, a wrongly typed argument cannot slip through.
- **Value types still earn their place inside.** Their constructors are the only place that says "this id
  is valid" (parse, don't validate). Typed maps (`Mapping[UserId, frozenset[RoleId]]`) make a mix-up such
  as looking up a user in the role table visible to a type checker. `str` and `Mapping` are stdlib types,
  which may cross seams (base-dependencies.md).

## 4. Core types and signatures

### 4.1 `errors.py`: one error type per distinct handling

```python
class EntitlementsError(Exception): ...
class InvalidQuestion(EntitlementsError, ValueError): ...   # the caller fixes the question
class InvalidModel(EntitlementsError, ValueError): ...      # the supplier fixes the model; the host keeps its old model
```

There are exactly two handlings. Each error is raised at exactly one boundary.

- `InvalidQuestion` is raised only by `decide`.
- `InvalidModel` is raised only by the `EntitlementModel` constructor and by `load_model`.

A file that cannot be read, or is not well-formed, is handled the same way as an inconsistent model
(reject it and keep the old one). So it gets the same type, with the path in the message. The design has
no `ModelFileError` subtype, because nobody would catch it differently (§5, "no dead subtype"). Messages
use the consumer's terms, for example `assignment of user 'alice' refers to undefined role 'editr'`.

### 4.2 `identifiers.py`: the only owner of A4 validity

```python
@dataclass(frozen=True, slots=True)
class _Identifier:
    value: str
    def __post_init__(self) -> None: ...   # isinstance(value, str) and value != "", else ValueError(<what is wrong>)
    def __str__(self) -> str: ...

class UserId(_Identifier): ...
class RoleId(_Identifier): ...
class Action(_Identifier): ...
class ResourceId(_Identifier): ...
```

- The rule is stored exactly as given. There is no trimming and no case folding. Equality is the
  dataclass's field and class equality, so `Action("Read") != Action("read")` and
  `UserId("x") != RoleId("x")`.
- The module raises a plain `ValueError` whose message describes the value. It does not know whether it is
  parsing a question or a model. The two boundaries in `model.py` translate the error into their own
  vocabulary, so each translation happens once, in its own place.
- Subclassing here is genuine subtyping. Every kind *is* an identifier under the same rule, and no subclass
  adds or refuses anything.

### 4.3 `model.py`

```python
@dataclass(frozen=True, slots=True)
class Permission:
    action: Action
    resource: ResourceId
    # Equality is exact on both fields. That makes it the single meaning of "grants (A, R)" (A4: no
    # implication, no wildcard).

class Decision(Enum):
    ALLOW = "allow"
    DENY = "deny"

class EntitlementModel:
    __slots__ = ("_grants_by_role", "_roles_by_user")

    def __init__(
        self,
        *,
        roles: Mapping[str, Iterable[tuple[str, str]]],
        assignments: Mapping[str, Iterable[str]],
    ) -> None: ...
    # Post: _grants_by_role is a read-only mapping from RoleId to frozenset[Permission].
    #       _roles_by_user is a read-only mapping from UserId to frozenset[RoleId].
    #       Every RoleId in _roles_by_user is a key of _grants_by_role (the invariant, A3).
    # Raises: InvalidModel.

    def decide(self, user: str, action: str, resource: str) -> Decision: ...
    # Pre: none. The method is the boundary.
    # Post: ALLOW iff some role of the user grants Permission(action, resource).
    # Raises: InvalidQuestion.

    def _grants(self, user: UserId, permission: Permission) -> bool: ...
    # THE grant rule. Its entire body is:
    #   return any(permission in self._grants_by_role[r]
    #              for r in self._roles_by_user.get(user, frozenset()))
```

**Constructor steps.** The constructor is the one path to a model, and it has one level of abstraction.

1. `_parse_roles(roles)` returns `dict[RoleId, frozenset[Permission]]`. Each permission must be a 2-item
   non-string sequence `(action, resource)`. Frozensets collapse duplicate grants (A6). A role whose
   iterable is empty is valid and maps to `frozenset()` (A3).
2. `_parse_assignments(assignments)` returns `dict[UserId, frozenset[RoleId]]`. Frozensets collapse
   duplicate assignments (A6). A user with an empty list is valid (A3).
3. `_require_defined_roles(...)` raises `InvalidModel` for the first assignment that refers to a role not
   in step 1. The message names the user and the role.
4. The instance stores both dicts wrapped in `types.MappingProxyType`. They are fresh copies, so a host
   that later mutates its own input dict cannot reach the model.

Every `ValueError` from the identifiers module, and every shape problem, is raised as `InvalidModel` with
its location (`role 'editor', permission #2: action must be a non-empty string`).

There is one explicit shape guard. A `str` passed where an iterable of roles or permissions is expected is
rejected. For example, `{"alice": "editor"}` would otherwise iterate as the characters `e, d, i, …`.

**Immutability.** `__slots__` removes `__dict__`. `__setattr__` and `__delattr__` raise `AttributeError`
once construction is done. The only initializer path is `object.__setattr__`, used inside `__init__`.
There is no method that returns a changed model and no mutator. Python cannot make anything truly
unbreakable. The design intent is that the model changes only by being replaced, and every intended path
enforces that.

**`decide` has two steps at one altitude.**

1. It parses the question: `UserId(user)` and `Permission(Action(action), ResourceId(resource))`. A
   `ValueError` becomes `InvalidQuestion`, naming the field (`user`, `action` or `resource`).
2. It returns `Decision.ALLOW if self._grants(u, p) else Decision.DENY`.

Nothing else maps `bool` to `Decision`.

### 4.4 Why the edge cases need no special cases

Every deny comes out of the one rule, `any(...)`. No stated case needs its own branch:

| Case | Path through `_grants` | Result |
|---|---|---|
| Unknown user | `.get(user, frozenset())` returns ∅, and `any(∅)` is `False` | DENY |
| User with zero roles | The stored set is ∅, and `any(∅)` is `False` | DENY |
| Roles, none granting | Every membership test is `False` | DENY |
| Two roles, only the second grants | `any` reaches the second role | ALLOW |
| `(write, R)` granted, `(read, R)` asked | `Permission` equality compares the action exactly | DENY |
| `(read, R1)` granted, `(read, R2)` asked | `Permission` equality compares the resource exactly | DENY |
| Unknown action or resource | It is in no grant set | DENY |
| `Read` asked, `read` granted | Exact `str` equality | DENY |

Unknown user and zero-role user share one path, as A3 requires ("same answer"). Deny is the absence of a
grant, with no inert deny machinery. The `self._grants_by_role[r]` lookup inside `_grants` cannot raise
`KeyError`, because the constructor invariant guarantees every assigned role is defined. That is A3 at
build time, never at query time.

## 5. Edges

### 5.1 `json_file.py`

```python
def load_model(path: str | os.PathLike[str]) -> EntitlementModel: ...
# Raises: InvalidModel (the message names the path).
```

The file format (UTF-8 JSON):

```json
{
  "roles": {
    "editor":  [{"action": "write", "resource": "doc-42"}, {"action": "read", "resource": "doc-42"}],
    "auditor": []
  },
  "assignments": {
    "alice": ["editor", "auditor"],
    "bob":   []
  }
}
```

The adapter owns the **file-format rules only**:

- An `OSError` on read, a `UnicodeDecodeError` or a `json.JSONDecodeError` is raised as `InvalidModel`
  with the path.
- The top level must be an object with exactly the keys `roles` and `assignments`. A missing key, or an
  unknown one such as the typo `"asignments"`, is rejected. Otherwise a typo would silently produce a model
  in which everyone is denied.
- Duplicate object keys are rejected, via `object_pairs_hook`. `json` would otherwise keep only the last
  value, silently dropping one definition of a role or user (see assumption A7).
- Each permission must be an object with exactly the keys `action` and `resource`. The adapter maps it to
  the `(action, resource)` pair. Named fields protect the people who write files from swapping action and
  resource by position.
- The adapter then calls `EntitlementModel(roles=…, assignments=…)`.

The adapter does **not** validate identifiers, check role references or deduplicate anything. Those are
core rules with a single owner. A non-string id, an empty id, a string where a list belongs, or an
undefined role all reach the constructor and come back as `InvalidModel`. The adapter re-raises that error
with the path prefixed to its message, for example `raise InvalidModel(f"{path}: {e}") from e`. The type
is the same, and only the context is added.

### 5.2 `cli.py` and `__main__.py`

```python
def main(argv: Sequence[str] | None = None) -> int: ...
```

- Usage: `python -m entitlements --model FILE USER ACTION RESOURCE`.
- It calls `load_model` and then `model.decide`, and prints `decision.value` to stdout.
- Exit codes (assumption A8):
  - `0`: allow.
  - `1`: deny.
  - `2`: any `EntitlementsError`, or an argparse usage error. The message goes to stderr.
- `argparse` stays in this module. The CLI holds no rule. It only reads argv, delegates and turns results
  into exit codes.

### 5.3 Replacing the model (A1) and concurrency

In a long-running host the host holds a reference to a model. To change entitlements, the host builds a
new model and assigns it: `self.model = load_model(p)` or `EntitlementModel(...)`. Two properties make
this safe without a lock:

- The model is immutable after `__init__` returns, so a reader never sees a model in the middle of a
  change. A torn read is structurally impossible.
- Rebinding one reference is atomic in CPython. It is also atomic in free-threaded 3.13+ builds, because
  object references are never torn. So a concurrent `decide` runs entirely against either the old model or
  the new one.

If a build fails, `InvalidModel` is raised before any assignment happens, so the old model stays in force.
The design does not add a holder class (§ Subtractive pass). The falsifier from the exit criteria is "a
reload that mutates the live model in place". It cannot be written, because no mutation path exists.

## 6. Where each rule lives

| Rule | Single owner |
|---|---|
| Grant rule: allow iff any of U's roles grants (A, R) | `EntitlementModel._grants` |
| Mapping the result to allow/deny (A5) | `EntitlementModel.decide`, step 2, together with the `Decision` enum |
| Identifier validity: non-empty `str` (A4) | `_Identifier.__post_init__` |
| Exact, case-sensitive matching with no implication (A4) | Dataclass equality of `_Identifier` and `Permission`. There is no normalization anywhere. |
| Malformed question is an error (A2) | `EntitlementModel.decide`, step 1, which is the only place that raises `InvalidQuestion` |
| Unknown user, action or resource is a deny (A2) | Falls out of `_grants`. No branch exists for it. |
| Consistency: assigned roles must be defined (A3) | `EntitlementModel.__init__` → `_require_defined_roles` |
| Empty role and zero-role user are valid (A3) | `EntitlementModel.__init__`, which accepts empty iterables |
| Set semantics (A6) | `EntitlementModel.__init__`, through its frozensets |
| Immutability and whole-model replacement (A1) | `EntitlementModel` (slots, blocked setattr, copied inputs) |
| File syntax, top-level keys, permission-object keys, duplicate JSON keys | `json_file.load_model` |
| argv, output text, exit codes | `cli.main` |

## 7. Assumptions added (flagged for the Guide)

- **A7: duplicate keys in the model file are rejected** as ill-formed JSON. They are not merged. Merging
  would put a second implementation of A6 in the edge. Silently keeping the last value would drop grants.
  A6 still applies to repeated entries *inside* a list.
- **A8: CLI exit codes** are 0 for allow, 1 for deny and 2 for an error, so the CLI works in shell
  conditionals. The printed `allow` or `deny` is the answer, and the exit code mirrors it.
- **A9: identifiers are otherwise opaque.** Whitespace-only and padded ids (`" read"`) are accepted
  exactly as given and are distinct from `"read"`. This follows A4's "opaque, exact" wording. If the
  product owner wants them rejected, the change is one line in `_Identifier`.

## 8. Test plan (test-first, one test per non-trivial decision)

The tests are behavioural and go through the public surface, unless noted otherwise.

**Grant rule (`test_decide.py`).** Each test uses a model built in code.

1. User with one role granting `(read, doc-1)`, asked `(read, doc-1)`: ALLOW.
2. Unknown user: DENY.
3. User whose roles do not grant it: DENY.
4. Two roles, only the second grants: ALLOW. A variant puts the granting role first, as a guard against
   order dependence.
5. `(write, R)` granted, `(read, R)` asked: DENY.
6. `(read, R1)` granted, `(read, R2)` asked: DENY.
7. User with zero roles: DENY, the same answer as test 2.
8. A user whose only role is an empty role is valid, and every question is DENY.
9. `Read` asked while `read` is granted: DENY. Also `doc-42` against `DOC-42`, and user `Alice` against
   `alice`.
10. The same string used as both a user id and a role id causes no cross-talk.
11. Unknown action, and unknown resource: DENY each.
12. An empty model (`roles={}`, `assignments={}`) is valid, and everything is DENY.

**Question boundary (`test_decide.py`).**

13. An empty string for each of user, action and resource raises `InvalidQuestion`, and the message names
    the field. That is three parametrized cases.
14. Non-string values (`None`, `5`, `b"read"`, `("read",)`) for each field raise `InvalidQuestion`. None of
    them is a DENY.
15. `InvalidQuestion` is an `EntitlementsError` and a `ValueError`.

**Model construction (`test_model_build.py`).**

16. An assignment to an undefined role raises `InvalidModel`, and the message names the user and the role.
17. A case mismatch between an assigned role and a defined one (`Editor` against `editor`) raises
    `InvalidModel`.
18. A defined role that nobody is assigned is valid.
19. Duplicate grants in a role and duplicate roles for a user are idempotent. Decisions are identical to
    the deduplicated model.
20. The same permission granted by two roles is valid, and the user gets ALLOW.
21. An empty or non-string role id, user id, action or resource in the model raises `InvalidModel`, never
    `InvalidQuestion`.
22. A permission that is not a pair (1-tuple, 3-tuple or bare string) raises `InvalidModel`.
23. A string where an iterable belongs (`{"alice": "editor"}`) raises `InvalidModel`.

**Immutability and replacement (`test_immutability.py`).**

24. Mutating the input dicts or lists after construction leaves decisions unchanged.
25. Setting or deleting attributes on a model raises `AttributeError`.
26. Smoke test for replacement: N threads call `decide` in a loop while the main thread rebinds a shared
    reference between model A (ALLOW) and model B (DENY). Every answer is either ALLOW or DENY and no call
    raises. The guarantee itself is structural (tests 24 and 25). This test only guards against a
    regression that introduces lazily mutated state.
27. A failed build leaves the reference the host already holds unchanged, because the exception is raised
    before assignment.

**File edge (`test_json_file.py`).** Each test uses a temporary file.

28. A valid file gives the same decisions as the equivalent in-code model. This is the "source is a
    replaceable edge" check.
29. Missing file, non-UTF-8 content and invalid JSON each raise `InvalidModel`, and the message contains
    the path.
30. A missing `roles` or `assignments` key, or an unknown top-level key, raises `InvalidModel`.
31. A duplicate role key and a duplicate user key each raise `InvalidModel` (A7).
32. A permission object with a missing, extra or misspelled key raises `InvalidModel`.
33. An undefined role in the file raises `InvalidModel`, with the path and the core's message. This shows
    that the core's rule is reached through the edge, not re-implemented there.
34. An architecture test: `model`, `identifiers` and `errors` import none of `json`, `argparse`,
    `pathlib`, `sys` or `os`. It checks the module source or `sys.modules` after a fresh import.

**CLI (`test_cli.py`).** These call `main(argv)` directly and capture stdout and stderr.

35. An allowed question prints `allow` and returns 0.
36. A denied question prints `deny` and returns 1.
37. An empty-string argument writes the error to stderr and returns 2.
38. A missing or invalid model file writes the path to stderr and returns 2.
39. A usage error (missing positional argument) returns 2.

## 9. Subtractive pass

Every surviving element, and the present force that requires it:

| Element | Present force |
|---|---|
| `EntitlementModel` | Holds the grant rule, A3 and A6, and immutability. It is the single domain object. |
| `Decision` | A5's allow-or-deny vocabulary, used by both host and CLI. Without it, the CLI would invent the words. |
| `Permission` | The unit of "grants (A, R)". Its exact equality *is* the matching rule. |
| `_Identifier` plus 4 kinds | A4 has one owner. Parsed-means-valid lets the core trust its inputs. Kind-typed maps separate users from roles. |
| `InvalidQuestion` / `InvalidModel` | Two different handlings: fix the question, or reject the model and keep the old one. |
| `EntitlementsError` | One catch point for the CLI's exit code 2. |
| `json_file.load_model` | The CLI's model source (A1: "a file for the CLI"). |
| `cli.main` | Stated entry point. |

**Cut** (each had no present force, or the force was already met elsewhere):

- **`ModelSource` protocol, `InMemorySource`, `FileSource`.** Nothing consumes "a source" polymorphically.
  The host calls the constructor and the CLI calls `load_model`. The constructor is already the port. An
  interface over two call sites that never vary at runtime is decorative. A future source (for example
  YAML) is one more function that calls the constructor, and nothing in the core reopens.
- **`DecisionService`, `ModelHolder` or `swap()`.** Whole-model replacement and torn-read freedom follow
  from immutability plus reference rebinding (§5.3). A holder would wrap one variable. No X-item forces it,
  because admin, reload and watch are non-goals.
- **A `Question` or `AccessRequest` value object.** It would only compose `UserId` and `Permission`.
  `decide`'s parse step is its entire job.
- **`Role` and `User` entity classes.** A role is `RoleId → frozenset[Permission]` and has no behavior of
  its own. A `Role.grants(p)` would split the grant rule across two owners.
- **Exporting the value types publicly.** No consumer needs them. Exporting them would create a second way
  to ask (typed), with the silent-deny hazard of §3.
- **A separate builder class or `build()` factory.** The constructor is the single path, so no bypass
  exists.
- **A `ModelFileError` subtype.** No handling distinguishes it from `InvalidModel`.
- **Precomputed per-user effective permissions, caches and indexes.** No performance requirement exists
  (§13 is conditional). The literal "any role" form keeps the rule readable against the spec.
- **A deny reason or an explanation field on `Decision`.** A5 rules it out.
- **Locks.** There is no shared mutable state to guard.

## 10. Risks and new facts

- **Python cannot enforce immutability absolutely.** `object.__setattr__` on the instance, or mutating the
  proxy's underlying dict through `gc`, would bypass it. The guarantee is design intent enforced on every
  intended path (§5, one owner). That is acceptable for an in-process library with no trust boundary.
- **The torn-read argument depends on atomic rebinding of one reference.** That holds in CPython with or
  without the GIL. A host that stores the model inside a larger mutable structure it updates piecemeal
  would be outside this guarantee. The rule to document for hosts is "hold the model in one reference".
- **A `str` subclass with an overridden `__eq__` or `__hash__` could subvert exact matching.**
  `_Identifier` could copy such a value to a plain `str` with `str.__str__(value)`, which ignores any
override, and only when `type(value) is not str`. The
  cost is tiny and the builder may take it. It is not a product behavior.
- **The objective is not invalidated by any evidence found.** A7 to A9 are new product assumptions, each
  the simple reading, and each needs the Guide's acknowledgement.

**Result: met.**
