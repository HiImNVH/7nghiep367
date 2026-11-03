# ViSign project source of truth

The `main` branch owns the project requirements, implementation plan, API
contract and task backlog. Application code is integrated from the role branches
through reviewed pull requests.

## Start here

- Feature specification: `specs/001-vsl-recognition-mvp/spec.md`
- Technical plan: `specs/001-vsl-recognition-mvp/plan.md`
- Actionable task backlog: `specs/001-vsl-recognition-mvp/tasks.md`
- API contract: `specs/001-vsl-recognition-mvp/contracts/openapi.yaml`
- Team tracking snapshot: `docs/team/implementation-status.md`
- Team tracking rules: `docs/team/README.md`

## Spec Kit workflow

On a fresh `main` checkout, select the active feature once in PowerShell before
running a workflow; Spec Kit persists the machine-local pointer in its ignored
`feature.json` file:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/001-vsl-recognition-mvp'
```

```text
$speckit-constitution
$speckit-specify
$speckit-plan
$speckit-tasks
$speckit-analyze
$speckit-implement
$speckit-converge
```

`tasks.md` is the only authoritative backlog. Member dashboards record current
work, blockers and evidence; they do not create a second task list.

## Completion rule

A task is release-complete only when its implementation and required tests have
been reviewed and merged into `main`, and its evidence is linked from the task or
team tracking snapshot. Raw videos, generated landmarks, trained model binaries,
temporary files and secrets must not be committed.
