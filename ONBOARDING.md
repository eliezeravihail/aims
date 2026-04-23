# Onboarding

## Install

```bash
claude plugin marketplace add https://github.com/eliezeravihail/expert-system.git
claude plugin install expert-system@expert-system
```

Or for local development:

```bash
git clone https://github.com/eliezeravihail/expert-system.git
cd expert-system
claude plugin marketplace add .
claude plugin install expert-system@expert-system
```

See `README.md` §Installation for VS Code Copilot and the Python harness.

## Agent routing system

1. Invoke the lean router (default, for Opus/Sonnet): `/experts <request>`.
2. For weaker baselines (Copilot, smaller OSS) use the pipeline mode: `/agents-experts <request>`.
3. Read `agents/registry.md` to see which workers are registered.
4. To add a worker: create `agents/<id>.md`, append one row to `agents/registry.md`, and (for lean) add a line to the decision rule in `agents/_router.md`.
