# Entitlements — stage 1

Design a service that answers one question: **may user U perform action A on resource R?** (allow / deny).

The model at stage 1:

- Each **user** is assigned one or more **roles**.
- Each **role** grants a set of **permissions**, where a permission is an `(action, resource)` pair the role
  is allowed to perform (e.g. `read` on `doc-42`, `write` on `doc-42`).
- U may perform A on R if **any** of U's roles grants the permission `(A, R)`. Otherwise, deny.

Deliver the architecture of the decision service and its data model. Design only — no implementation.
