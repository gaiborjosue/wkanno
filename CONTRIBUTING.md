# Contributing

## Development Setup

Create an isolated environment and install the package in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

If you already use `pipx` for CLI tools, keep development inside a normal virtual
environment instead of editing the `pipx` installation.

## Recommended Workflow

1. Create a focused branch for the change.
2. Keep changes small and command-oriented.
3. Add or update tests when behavior changes.
4. Run the local checks before opening a pull request.

## Local Checks

Run the unit tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

Run linting:

```bash
python -m ruff check .
```

Optionally run type checking:

```bash
python -m mypy src
```

## Scope Guidelines

- Prefer adding behavior to the high-level `fetch-box` flow only when it is broadly
  useful across annotations and datasets.
- Keep network access logic in `wkanno.client` and workflow orchestration in
  `wkanno.workflows`.
- Preserve voxel alignment guarantees when touching raw-patch or label extraction.
- Treat physical voxel size metadata conservatively. If spacing is not confirmed,
  avoid presenting placeholders as authoritative scientific truth.

## Pull Request Expectations

- Explain what changed and why.
- Mention any dataset or annotation assumptions.
- Include command examples for new CLI behavior.
- Avoid introducing breaking CLI changes unless clearly documented.