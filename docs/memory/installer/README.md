# installer/

The clone-and-bootstrap install path (ADR-0005). aims is installed
into a target project by running `/init-workflow <target-path>`
from inside the aims source repo; nothing is installed globally
besides the `/init-workflow` command itself.

## Leaves

- **init-workflow.md** — the five-phase installer command. Sniff,
  interview, show plan, apply, doctor.
- **templates.md** — the `.tmpl` files under `templates/` and the
  substitution variables (`{{PROJECT_NAME}}`, `{{TEST_CMD}}`, …).
