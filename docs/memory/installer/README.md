# installer/

The clone-and-bootstrap install path (ADR-0005). aims is installed
into a target project by running `/install-on <target-path>` (renamed
from `/init-workflow` per ADR-0010) from inside the aims source repo;
nothing is installed globally besides the `/install-on` command itself.

## Leaves

- **init-workflow.md** — the six-phase `/install-on` command: detect,
  interview, show changes + approval, apply (with stale-file cleanup),
  memory bootstrap/augment, doctor. Self-refreshing per ADR-0011.
- **templates.md** — the `.tmpl` files under `templates/` and the
  substitution variables (`{{PROJECT_NAME}}`, `{{TEST_CMD}}`, …).
