# Agent Registry

Authoritative list of agents available to the `/project:experts` router.
To add an agent: create `agents/<id>.md` and append one row to the table below.

| id | file | one-line capability |
|----|------|---------------------|

## Agent file conventions
Each `agents/<id>.md` must declare, in YAML frontmatter:
- `name` — must match the `id` above
- `model` — exact model id to invoke with
- `tools` — whitelist of tools the agent may use
- `inputs` — field list the router binds against (append `?` for optional fields)
- `outputs` — field list the router reads back

The body is a pure behavior spec: role, input semantics, output contract, and the
retry protocol. No domain playbooks — those live in the skills the agent invokes.

## Retry protocol
An agent signals an unacceptable result with a single line:

```
STATUS: RETRY <reason>
```

The router feeds `<reason>` back as `retry_hint` on the next loop iteration.
Default cap: 3 retries per agent per pipeline stage.

## Cascade binding
In multi-stage pipelines, the router maps stage N's `outputs` 1:1 into stage N+1's
`inputs` by field name. Declaring compatible schemas is the agent author's job.
