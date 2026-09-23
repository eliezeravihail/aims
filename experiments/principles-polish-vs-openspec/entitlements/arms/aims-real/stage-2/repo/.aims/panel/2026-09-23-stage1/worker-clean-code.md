---
title: "Stage 1 decision service — design (clean-code axis)"
date: 2026-09-23
axis: clean code (few moving parts, no smells, lean dependencies)
---

# Stage 1 entitlements decision service: the clean-code design

## 0. Shape in one paragraph

The service has three modules, and dependencies point one way, toward the core:

```
entitlements/
  __init__.py      re-exports the core's public names (no edge imported)
  model.py         THE CORE: identifier rule, Permission, EntitlementModel, error types      (imports: dataclasses, types, collections.abc)
  model_file.py    EDGE: JSON file -> EntitlementModel                                        (imports: json, os, model)
  __main__.py      EDGE: CLI `python -m entitlements MODEL USER ACTION RESOURCE`              (imports: argparse, sys, model, model_file)
```

```
__main__ ──> model_file ──> model
    └──────────────────────────^
```

The core has no dependencies except small stdlib typing and container helpers. It never imports `json`,
`argparse`, `os` or `sys`. An edge constructs the model only through the published `EntitlementModel`
constructor, so that constructor is the seam every source goes through. The module does not need a
source protocol, a builder or a service holder (see §8).

Runtime dependencies: **none beyond the stdlib**. Test runner: stdlib `unittest`, so no dev dependency
either (pytest would work equally well; no feature of it is needed).

---

## 1. The core — `entitlements/model.py`

Why it is one module: this is the whole domain. The identifier rule, the permission value, the model and
the vocabulary it fails in all change for the same reason, which is a change to the entitlement rules.
Splitting it into `errors.py` / `ids.py` / `permission.py` would give three lazy modules and shotgun
surgery on every rule change. Expected size is about 90 lines.

### 1.1 Errors (the module's boundary vocabulary)

```python
class EntitlementsError(Exception):
    """Base: anything the caller supplied (a question or a model) was rejected."""

class InvalidIdentifierError(EntitlementsError, ValueError):
    """An identifier is not a non-empty str (A2/A4). Raised for a malformed question, or a bad id inside a model."""

class InconsistentModelError(EntitlementsError, ValueError):
    """The model contradicts itself or has the wrong container shape: a user assigned to an undefined role (A3),
    a grant that is not a Permission, a role list given as a bare string."""
```

(`ModelFileError(EntitlementsError)` lives in the file edge; see §2. The edge owns its own vocabulary.)

How each type gets handled. A host catches `EntitlementsError` around a load or build and keeps its
current model. At a query site the only thing `allows` can raise is `InvalidIdentifierError`, which
signals a programming error in the caller. The CLI catches the base and exits 2. Each leaf type is
raised by exactly one owner (§4). The leaves also subclass `ValueError`, so a host that already guards
bad arguments with `except ValueError` keeps working.

### 1.2 The identifier rule: one private function

```python
def _require_identifier(value: object, what: str) -> str:
    """Return value unchanged if it is a non-empty str; else raise InvalidIdentifierError naming `what`."""
```

- It checks `isinstance(value, str) and value != ""`. It does **not** strip, casefold or
  Unicode-normalize anything, because identifiers are opaque and exact (A4). That is why `Read` ≠ `read`
  and `doc-42` ≠ `DOC-42` hold automatically: the code has no normalization step for anyone to add by
  mistake.
- Assumption (A4 read literally): `" "` (whitespace only) is a non-empty string, so it is a valid,
  opaque identifier. Composed and decomposed Unicode forms of the same text are different identifiers.
- The error message speaks the caller's concept, for example
  `"action must be a non-empty string, got ''"` or `"user must be a non-empty string, got int 5"`.
- **Why not four value types (`UserId`, `RoleId`, `Action`, `ResourceId`)?** They would all carry the
  same single rule. Four wrappers that each delegate to one validator are the "lazy class" smell, and
  every caller would have to wrap its strings. The rule has one owner either way. `Permission` is the
  one place a pair of ids forms a concept, so that is the one value type (§1.3).

### 1.3 `Permission`: the unit of grant

```python
@dataclass(frozen=True, slots=True)
class Permission:
    action: str
    resource: str
    def __post_init__(self) -> None:   # validates both fields via _require_identifier
```

- A frozen `Permission` compares and hashes by exact field equality. So "(write, R) granted, (read, R)
  asked → deny" and "(read, R1) granted, (read, R2) asked → deny" both come from **value equality**,
  with no matching logic at all. The code has nowhere to put wildcards or implication, and none are
  wanted (A4).
- Fields are named, not positional, which keeps connascence weak: a grant is
  `Permission(action="write", resource="doc-42")`.

### 1.4 `EntitlementModel`: immutable, consistent by construction, owner of the grant rule

```python
class EntitlementModel:
    __slots__ = ("_grants", "_roles")

    def __init__(
        self,
        grants: Mapping[str, Iterable[Permission]],   # role id -> permissions it grants (a role may grant nothing)
        assignments: Mapping[str, Iterable[str]],     # user id -> role ids held (a user may hold none)
    ) -> None: ...

    def allows(self, user: str, action: str, resource: str) -> bool: ...
```

**Construction contract (enforced in `__init__`, so every source goes through it):**

| Precondition checked | Failure |
|---|---|
| every role id (key of `grants`) and user id (key of `assignments`) is a valid identifier | `InvalidIdentifierError` |
| each value is a collection, not a bare `str`/`bytes` (`{"alice": "editor"}` would otherwise silently become roles `e,d,i,t,o,r`) | `InconsistentModelError` |
| every item in a grant collection is a `Permission` (a tuple would never match anything and would deny silently) | `InconsistentModelError` |
| every role a user is assigned is a key of `grants` (A3) | `InconsistentModelError`, naming the user and the undefined role |

**Postconditions and invariants:**
- `_grants` is a `MappingProxyType` over a fresh `dict[str, frozenset[Permission]]`, and `_roles` is a
  `MappingProxyType` over a fresh `dict[str, frozenset[str]]`. The constructor copies its inputs, so
  mutating the caller's dicts afterwards has no effect. `frozenset` gives set semantics (A6): a repeated
  grant or assignment is the same as one.
- Every role id in any `_roles` value is a key of `_grants`. This holds from construction onwards
  because the object has no mutators (and `__slots__` stops ad-hoc attributes). The model is consistent
  by construction, so `allows` never has to handle an undefined role.
- The model is not supposed to be mutated (this is design intent). Python can always be subverted
  through `object.__setattr__`, and that case is out of scope.

**Query: `allows(user, action, resource) -> bool`. This method is the only home of the grant rule.**

Illustrative body (three lines; this *is* the rule):

```python
user = _require_identifier(user, "user")
wanted = Permission(action, resource)                      # validates action, resource
return any(wanted in self._grants[role] for role in self._roles.get(user, ()))
```

- Malformed question (empty or non-`str` user, action or resource) → `InvalidIdentifierError`, raised
  before any lookup. That is the error-not-deny side of A2.
- Unknown user → `.get(user, ())` returns an empty iterable, so `any(...)` is `False` and the answer is
  **deny**. A user with zero roles takes the same path. There is no special case, which matches A3's
  "same answer as an unknown user".
- A role that grants nothing contributes an empty frozenset, so `any` passes over it.
- Two roles where only the second grants → `any` → allow. Order does not matter.
- Deny is simply `any` finding nothing (exit criterion: there is no deny machinery with nothing to do).
- The method is pure: it reads immutable data, has no side effects and returns a value (CQS).
- Why the rule is evaluated per query instead of precomputing a per-user union at construction: this
  way the spec sentence appears in the code exactly once, as one expression. Precomputing would be an
  optimization with nothing asking for it (no performance requirement, §13 does not apply).
- Why `allows` takes three strings instead of a `Permission`: the goals phrase the question as `(U, A, R)`.
  Taking three strings also removes a real trap: `allows("u", ("read", "doc"))` with a tuple would be a
  silent deny, not an error.

**The model exposes nothing else.** It has no getters, no iteration and no "explain" (A5), because no
consumer needs them. Tests exercise the model only through `allows` and construction.

### 1.5 `entitlements/__init__.py`

This module re-exports `EntitlementModel`, `Permission`, `EntitlementsError`, `InvalidIdentifierError`
and `InconsistentModelError`. It deliberately does **not** import `model_file`, so `import entitlements`
never pulls in the file edge or `json`. A host that wants files writes
`from entitlements.model_file import load_model`.

---

## 2. The file edge — `entitlements/model_file.py`

Why it is a separate module: the file format changes for different reasons than the rules or the CLI
arguments do (§7 localize change axes). The objective also asks for the model's source to be a
replaceable edge. Deleting this module leaves the core untouched.

```python
class ModelFileError(EntitlementsError):
    """The file could not be read, is not JSON, or does not have the documented shape."""

def load_model(path: str | os.PathLike[str]) -> EntitlementModel: ...
```

**Format (JSON, UTF-8).** Permissions are objects, so fields are matched by name, not position:

```json
{
  "roles": {
    "editor":  [{"action": "write", "resource": "doc-42"}, {"action": "read", "resource": "doc-42"}],
    "auditor": []
  },
  "users": {
    "alice": ["editor", "auditor"],
    "bob":   []
  }
}
```

**What this edge owns, and only this:** turning the JSON *structure* into constructor arguments.
- The file is read as UTF-8. An `OSError` (missing or unreadable file) or a `json.JSONDecodeError` /
  `UnicodeDecodeError` is translated to `ModelFileError` with the path and the reason.
- Parsing uses `object_pairs_hook` to **reject a repeated key** in any JSON object. JSON leaves duplicate
  keys undefined, and `json` would silently keep the last one, dropping a user's earlier roles. This is
  about file syntax, not model semantics: a repeated *list entry* is still idempotent (A6), because the
  core deduplicates.
- The top level must be an object with exactly the keys `"roles"` and `"users"` (no missing and no extra
  keys, so a typo like `"role"` fails fast). Both must be objects, every role and user value must be a
  list, and every grant must be an object with exactly `"action"` and `"resource"`. Anything else →
  `ModelFileError` with a JSON-path-like location (`roles.editor[1]`).
- The edge then calls `EntitlementModel(grants={role: [Permission(**entry) ...]}, assignments=users)`.

**What it does not own:** identifier validity or role consistency. A `""` action, a numeric resource or
an assignment to an undefined role are rejected by the core (`InvalidIdentifierError` /
`InconsistentModelError`), and those errors pass through unwrapped because they are already published
vocabulary. The only overlap with the core is "value is a list, not a string". It is intentional and is
not duplicated knowledge: the edge checks the JSON *document* shape (with a file location), while the
core defends its own constructor against in-code callers.

---

## 3. The CLI edge — `entitlements/__main__.py`

```python
def main(argv: Sequence[str] | None = None) -> int: ...
if __name__ == "__main__":
    sys.exit(main())
```

- Usage: `python -m entitlements MODEL_FILE USER ACTION RESOURCE`, parsed by `argparse` (four positional
  arguments, no flags).
- Flow: `load_model(path).allows(user, action, resource)`. It prints `allow` or `deny` to stdout.
- Exit codes follow the grep convention: **0 = allow, 1 = deny, 2 = error**. Any `EntitlementsError` is
  printed to stderr as `entitlements: <message>` and exits 2. argparse's own usage errors already exit 2.
- The CLI holds no rules at all. An empty-string argument (`''`) reaches the core and comes back as
  `InvalidIdentifierError` → exit 2, so the CLI has no validation of its own that could drift from the
  core's.
- Each invocation is one-shot, so the process never needs to reload a model.
- Why `main` lives in `__main__.py` and not a separate `cli.py`: nothing else imports it, so a second
  module would be a middle man. Tests call `main([...])` directly and capture stdout and stderr.

---

## 4. Where each rule lives (one owner each)

| Rule | Owner | Every path to it |
|---|---|---|
| Grant rule: allow iff any held role grants (A,R) | `EntitlementModel.allows` (one expression) | library call; CLI → `allows` |
| Exact, case-sensitive match; no implication or wildcard (A4) | `Permission` value equality (frozen dataclass), plus the rule that nothing normalizes | grants and questions are both `Permission`s |
| Identifier = non-empty `str` (A2, A4) | `model._require_identifier` | `Permission.__post_init__`, `EntitlementModel.__init__` (user and role keys), `allows` (user) |
| Unknown user or zero roles → deny (A2, A3) | `allows` (`.get(user, ())` feeding `any`), with no special case | same |
| Assignment to an undefined role → rejected at build/load (A3) | `EntitlementModel.__init__` | in-code build; `load_model` → constructor |
| A role granting nothing is valid; a user with zero roles is valid (A3) | `EntitlementModel.__init__` (empty collections are accepted) | same |
| Set semantics and idempotent duplicates (A6) | `EntitlementModel.__init__` (normalizes to `frozenset`) | same |
| Immutability; replacement is a whole-model swap (A1) | `EntitlementModel` (frozen containers, no mutators) plus the host rebinding its reference | see §5 |
| JSON structure, duplicate-key rejection, file I/O errors | `model_file.load_model` | CLI; hosts that opt in |
| Output wording and exit codes | `__main__.main` | CLI only |

---

## 5. Replacement and concurrency (A1, the torn-read criterion)

The model is immutable, so **the host's reference is the swap point**:

```python
try:
    candidate = load_model(path)        # or EntitlementModel(...) built in code
except EntitlementsError as err:
    log(err)                            # rejected whole; the current model keeps serving
else:
    current = candidate                 # one reference rebind
```

- A query calls `current.allows(...)` on the object it dereferenced. That object can never change, so a
  query runs entirely against the old model or entirely against the new one. A torn read is impossible
  by construction, and no lock is needed. Rebinding a name or attribute is atomic in CPython (GIL), and
  in the free-threaded build (3.13t) object attribute stores are also safe. Neither build ever exposes a
  half-built model, because the constructor returns only after validation has finished.
- The falsifier from state.md, "a reload that mutates the live model in place", **cannot be written**
  against this API because the model has no mutators.
- Why no `EntitlementService` or `ModelHolder` class with `replace()`: its only job would be to hold
  one attribute and rebind it, which is exactly what the host's own variable already does. See §8.

---

## 6. Tracing the input space (§1 procedure)

The change axes in play are user, role set, grants and question identifiers. Each one crossed with the
grant, identifier and consistency rules:

- User: known with roles / known with zero roles / unknown → allow-if-granted / deny / deny. ✓
- Role set size: 0 / 1 / many. Ordering does not matter (`any` over a frozenset). ✓
- Grants: an empty role, the same permission granted by two roles, the same permission repeated inside
  one role (deduplicated). ✓
- Question identifiers: valid-and-known / valid-and-unknown (deny) / empty, non-`str`, `None` (error).
  A `str` subclass is accepted as a `str`. ✓
- Case and exactness: `Read`/`read`, `doc-42`/`DOC-42`, a trailing space, Unicode forms are all distinct.
  ✓
- Model: an undefined role in an assignment (reject), a role that is defined but never assigned
  (valid), a user id equal to a role id (separate namespaces, valid), and an empty model `{}`/`{}`
  (valid; everything is denied). ✓
- Aliasing: the caller mutates its input dicts or lists after construction → the model is unaffected
  (it copied them). ✓
- File only: a duplicate JSON key (reject), a missing or extra top-level key (reject), a grant as an
  array instead of an object (reject), a string where a list is expected (reject), a non-UTF-8 file
  (reject). ✓

No case produced an output that no stated rule covers.

---

## 7. Test plan (test-first; stdlib `unittest`; one test per non-trivial decision)

`tests/test_model.py` (core, fast, no I/O):
1. A role grants (read, doc-42) and the user holds it → allow.
2. Unknown user → deny.
3. A user whose roles none grant (A,R) → deny.
4. Two roles, only the second grants → allow (and the same with the dict order reversed).
5. (write, R) granted, (read, R) asked → deny.
6. (read, R1) granted, (read, R2) asked → deny.
7. A user with zero roles → deny, and the construction succeeds.
8. A role granting nothing → construction succeeds, and holding it grants nothing.
9. Case: `Read` vs `read` → deny; `doc-42` vs `DOC-42` → deny; `" read"` vs `read` → deny (no stripping).
10. Malformed question: `""` as user, action or resource → `InvalidIdentifierError`. `None` and `5` →
    `InvalidIdentifierError`. None of these return deny (parameterized with `subTest`).
11. `Permission("", "x")` and `Permission("r", 7)` → `InvalidIdentifierError`.
12. Assignment to an undefined role → `InconsistentModelError` raised from the constructor, with the
    message naming the user and the role.
13. An invalid user or role id as a model key → `InvalidIdentifierError` at construction.
14. The role list given as a bare `str` → `InconsistentModelError`.
15. A grant item that is a tuple, not a `Permission` → `InconsistentModelError`.
16. Duplicates: the same grant twice, the same role twice in an assignment, and the same permission via
    two roles → the model builds and answers the same as with single entries.
17. Isolation: mutate the input dicts or lists after construction → the answers do not change.
18. Immutability: assigning a new attribute raises (`__slots__`), and there is no public mutator (the
    public attribute set is asserted to be `{allows}`).
19. Swap: build model A, rebind to model B, and a query on a held reference to A still answers
    according to A.
20. Concurrency smoke test: N threads query a shared reference while another thread rebinds it between
    two models that differ on one permission. Every answer must equal A's or B's answer for that
    question; there must be no exception and no third outcome.
21. Error taxonomy: every leaf is an `EntitlementsError` and a `ValueError`.

`tests/test_model_file.py` (tmp dir files):
22. The documented example file loads and answers like the equivalent in-code model.
23. Missing file → `ModelFileError` (mentions the path). Invalid JSON and non-UTF-8 → `ModelFileError`.
24. A duplicate key (a user listed twice, or a role listed twice) → `ModelFileError`.
25. A missing `"users"`, an extra `"role"` key, or a non-object top level → `ModelFileError`.
26. A grant as `["read","doc"]`, or with a missing or extra field → `ModelFileError` that names the
    location.
27. An undefined role in the file → `InconsistentModelError` (the core's error passes through
    unwrapped). An empty action in the file → `InvalidIdentifierError`.
28. The file edge adds no rules: a file equivalent to each of cases 1–9 gives the same answer
    (parameterized over a few representative cases, not all of them).

`tests/test_cli.py` (calling `main(argv)`, capturing stdout and stderr):
29. Allow → prints `allow`, returns 0. Deny → prints `deny`, returns 1.
30. An empty-string argument → stderr message, returns 2. A bad model file → stderr message, returns 2.
31. A wrong number of arguments → argparse exits with 2.

Structure test:
32. `model.py` imports none of `json`, `argparse`, `os`, `sys`, `io` (checked by an AST scan of its
    imports), and `import entitlements` does not import `entitlements.model_file`.

---

## 8. Subtractive pass: every element and the force that requires it

| Element | Present force | Verdict |
|---|---|---|
| `EntitlementModel` | the grant rule and consistency invariant need one immutable home | keep |
| `Permission` | the goals name it; it is the unit of grant; its value equality *is* the exact-match rule | keep |
| `_require_identifier` (a function, not a class) | A2/A4 must be enforced at three entry points by one owner | keep, private |
| `EntitlementsError` base | the CLI and hosts catch "rejected input" in one place | keep |
| `InvalidIdentifierError` / `InconsistentModelError` | two distinct owners, and "what to fix" differs (a caller's argument vs the model's references). Callers handle them the same way, so this is a judgment call, kept for precision, because the leaves are the types A2 and A3 name | keep (close call, see risks) |
| `ModelFileError` | the edge's own failures (I/O, syntax, shape) are not domain concepts; keeping them in the edge keeps the core file-agnostic | keep, in the edge |
| `model_file.py` as a module | the source must be a replaceable edge; the format changes for its own reasons | keep |
| `__main__.py` | the CLI entry point asked for in base-dependencies | keep; `main` is not split into `cli.py` |
| Value types `UserId`/`RoleId`/`Action`/`ResourceId` | the same single rule four times, with no behaviour of their own | **cut** (lazy classes) |
| `ModelSource` protocol or loader strategy | no consumer takes a polymorphic source; the constructor already is the seam | **cut** |
| `ModelBuilder` / fluent builder | the constructor takes whole mappings (A1: the model is supplied whole) | **cut** |
| `EntitlementService` / `ModelHolder` with `replace()` | it would just wrap one attribute rebind (§5) | **cut** |
| `Decision` enum (ALLOW/DENY) | two values with no extra data (A5); `bool` with a predicate name is complete, and the CLI owns the wording | **cut** |
| `Question` dataclass | three named arguments are not a long parameter list, and a type would make every caller wrap | **cut** |
| Precomputed per-user permission union | an optimization nothing asks for; it would split the rule between construction and query | **cut** |
| Separate `errors.py` | a lazy module; the errors belong to the core's vocabulary | **cut** (errors live in `model.py`) |
| `__init__` re-export of `load_model` | convenient, but it would drag the file edge and `json` into every import | **cut** |
| Any third-party package (pytest, pydantic, attrs) | stdlib covers validation, tests and immutability | **none added** |

What remains: 3 modules, 1 value type, 1 model class, 1 private function, 4 exception classes,
3 public functions or methods (`EntitlementModel.__init__`, `allows`, `load_model`) plus `main`.

---

## 9. Risks and new facts for the Guide

- **New fact: JSON duplicate keys.** `json.loads` silently keeps the last value, which would drop a
  user's roles without any error. The design rejects repeated keys via `object_pairs_hook`. This is a
  file-edge decision, beyond A1–A6, and should be recorded as an assumption (A7: *a model file with a
  repeated key is rejected as ambiguous*).
- **New fact: two traps that deny silently in Python.** A bare `str` where an iterable of roles is
  expected, and a tuple where a `Permission` is expected, would both give quiet denies instead of load
  errors. Both are rejected at construction (tests 14 and 15). The question API takes three strings so
  that the trap cannot occur on the query side.
- **Assumption surfaced:** a whitespace-only identifier is valid (A4 read literally), and no Unicode
  normalization is done. The product owner may prefer rejecting blank identifiers; if so, the change is
  one line in `_require_identifier`.
- **Close call:** the two core error leaves are not handled differently by any present caller. A
  stricter subtractive reading would merge them into one `InvalidModelError`/`InvalidQuestionError`
  pair, or into the base alone. That merge is cheap later.
- **Concurrency:** the design relies on immutability plus an atomic reference rebind, not on locks. That
  is correct on CPython and on free-threaded builds for a single reference. If a host needs a
  compare-and-swap reload policy, that is host code, and nothing in stage 1 asks for it.
- **CLI exit code 1 = deny** follows grep. A caller that treats every non-zero code as failure would
  misread a deny. This is documented in `--help`.

## Result

**met.** All of the objective's exit criteria are covered. The grant rule has one owner and one
expression, the model is immutable and consistent by construction, and the file and CLI are edges that
the core never imports. Nothing in the evidence invalidates the objective.
